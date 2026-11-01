import pytest
import uuid
from app.core.database import SessionLocal
from app.core.config import settings
from app.core.state_machine import ApplicationStatus, ApplicationCapability
from app.models.schema import (
    JobPosting, Application, JobMatch, CandidateProfile, User,
    SubmissionEvidence, TelegramCallbackAction, AutomationSetting
)
from app.services.auto_apply_engine import auto_apply_engine
from app.services.approval_service import approval_service
from app.services.telegram_service import telegram_service

@pytest.fixture(scope="module")
def setup_test_data():
    db = SessionLocal()
    # Ensure a user exists
    user = db.query(User).first()
    if not user:
        user = User(email="test@jobhunter.ai", full_name="Mustkeem Ahmad", role="jobseeker")
        db.add(user)
        db.commit()

    # Ensure profile exists
    prof = db.query(CandidateProfile).first()
    if not prof:
        prof = CandidateProfile(
            user_id=user.id,
            full_name="Mustkeem Ahmad",
            email="mustkeem324@gmail.com",
            headline="AI Trainer & Full-Stack Developer",
            location="India"
        )
        db.add(prof)
        db.commit()

    # Create mock test job 1 (Authorized sandbox)
    job_auth = JobPosting(
        title="AI Evaluation Specialist",
        company_name="Mock ATS Corp",
        location="Worldwide Remote",
        country_eligibility="Worldwide",
        is_india_eligible=True,
        employment_type="Contract",
        compensation_text="$45/hr",
        application_url="https://example.com/apply/mock-1",
        description="Looking for an AI Evaluation Specialist in India or Remote Worldwide.",
        source_id="mock_ats",
        source_job_id=f"test-auth-{uuid.uuid4().hex[:6]}",
        status="active",
        application_capability=ApplicationCapability.AUTHORIZED_API_SUBMISSION.value
    )
    db.add(job_auth)

    # Create mock test job 2 (Greenhouse ATS requiring review)
    job_review = JobPosting(
        title="Senior Python Engineer",
        company_name="Acme Tech",
        location="Remote (India)",
        country_eligibility="India",
        is_india_eligible=True,
        employment_type="Full-Time",
        compensation_text="$60k-$90k",
        application_url="https://boards.greenhouse.io/acmetech/jobs/999",
        description="Python backend engineer with FastAPI and PostgreSQL.",
        source_id="greenhouse",
        source_job_id=f"test-rev-{uuid.uuid4().hex[:6]}",
        status="active",
        application_capability=ApplicationCapability.MANUAL_REVIEW_REQUIRED.value
    )
    db.add(job_review)

    # Create mock test job 3 (Ineligible for India)
    job_ineligible = JobPosting(
        title="US Only Developer",
        company_name="US Local Corp",
        location="US Only",
        country_eligibility="US Only",
        is_india_eligible=False,
        employment_type="Full-Time",
        compensation_text="$120k",
        application_url="https://example.com/us-only",
        description="US Citizens only.",
        source_id="lever",
        source_job_id=f"test-inelig-{uuid.uuid4().hex[:6]}",
        status="active",
        application_capability=ApplicationCapability.MANUAL_REVIEW_REQUIRED.value
    )
    db.add(job_ineligible)
    db.commit()

    db.refresh(job_auth)
    db.refresh(job_review)
    db.refresh(job_ineligible)

    # Add matches
    db.add(JobMatch(
        job_id=job_auth.id,
        profile_id=prof.id,
        overall_score=94.0,
        skills_score=28.0,
        experience_score=19.0,
        eligibility_score=20.0,
        education_score=9.0,
        preferences_score=9.0,
        recency_score=9.0,
        match_tier="Highly suitable",
        is_india_eligible=True
    ))
    db.add(JobMatch(
        job_id=job_review.id,
        profile_id=prof.id,
        overall_score=88.0,
        skills_score=26.0,
        experience_score=18.0,
        eligibility_score=20.0,
        education_score=8.0,
        preferences_score=8.0,
        recency_score=8.0,
        match_tier="Suitable",
        is_india_eligible=True
    ))
    db.commit()

    job_auth_id = job_auth.id
    job_review_id = job_review.id
    job_ineligible_id = job_ineligible.id
    db.close()

    yield {
        "job_auth_id": job_auth_id,
        "job_review_id": job_review_id,
        "job_ineligible_id": job_ineligible_id
    }

def test_auto_apply_ineligible_location_blocked(setup_test_data):
    job_id = setup_test_data["job_ineligible_id"]
    res = auto_apply_engine.process_one_click_apply(str(job_id), sender_id="12345")
    assert res["success"] is False
    assert res["error"] == "INELIGIBLE_LOCATION"

def test_auto_apply_mode_a_authorized_api_submission(setup_test_data):
    job_id = setup_test_data["job_auth_id"]
    prev_auto = settings.AUTO_APPLY_ENABLED
    settings.AUTO_APPLY_ENABLED = True
    try:
        res = auto_apply_engine.process_one_click_apply(str(job_id), sender_id="12345")
        assert res["success"] is True
        assert res["action"] == "SUBMITTED_CONFIRMED"
        assert res["confirmation_id"].startswith("CONF-")
        assert res["application_id"] is not None

        # Verify DB state
        db = SessionLocal()
        app_rec = db.query(Application).filter(Application.id == res["application_id"]).first()
        assert app_rec.status == ApplicationStatus.SUBMITTED_CONFIRMED
        assert app_rec.confirmation_receipt_id == res["confirmation_id"]
        assert app_rec.tailored_summary is not None
        assert app_rec.cover_letter is not None

        # Duplicate submission check (Step 6)
        res_dup = auto_apply_engine.process_one_click_apply(str(job_id), sender_id="12345")
        assert res_dup["success"] is False
        assert res_dup["error"] == "ALREADY_APPLIED"
        db.close()
    finally:
        settings.AUTO_APPLY_ENABLED = prev_auto

def test_auto_apply_mode_b_staging_and_approval_flow(setup_test_data):
    job_id = setup_test_data["job_review_id"]
    res = auto_apply_engine.process_one_click_apply(str(job_id), sender_id="12345")
    assert res["success"] is True
    assert res["action"] == "APPLICATION_PREPARED"
    app_id = res["application_id"]

    db = SessionLocal()
    app_rec = db.query(Application).filter(Application.id == app_id).first()
    assert app_rec.status == ApplicationStatus.AWAITING_APPROVAL
    db.close()

    # Test approval card formatting
    card = approval_service.format_approval_card(app_id)
    assert card is not None
    assert "APPLICATION READY FOR REVIEW" in card["text"]
    assert "Acme Tech" in card["text"]
    keyboard = card["reply_markup"]["inline_keyboard"]
    assert keyboard[0][0]["callback_data"] == f"appr:{app_id}"
    assert keyboard[0][1]["callback_data"] == f"edit:{app_id}"
    assert keyboard[1][0]["callback_data"] == f"rej:{app_id}"

    # Test approval handler
    appr_res = approval_service.handle_approve(app_id)
    assert appr_res["success"] is True

    db = SessionLocal()
    app_rec = db.query(Application).filter(Application.id == app_id).first()
    assert app_rec.status == ApplicationStatus.AUTHORIZED_TO_SUBMIT
    db.close()

    # Test rejection handler
    rej_res = approval_service.handle_reject(app_id, reason="Changed mind")
    assert rej_res["success"] is True

    db = SessionLocal()
    app_rec = db.query(Application).filter(Application.id == app_id).first()
    assert app_rec.status == ApplicationStatus.REJECTED
    assert app_rec.failure_reason == "Changed mind"
    db.close()

def test_telegram_callback_and_replay_protection():
    call_id = f"cb_test_{uuid.uuid4().hex[:8]}"
    update = {
        "update_id": 99999,
        "callback_query": {
            "id": call_id,
            "from": {"id": 12345678, "first_name": "Mustkeem"},
            "message": {"message_id": 777, "chat": {"id": 12345678}},
            "data": "cfg:toggle_india"
        }
    }
    telegram_service.handle_incoming_update(update)

    db = SessionLocal()
    action = db.query(TelegramCallbackAction).filter(TelegramCallbackAction.callback_id == call_id).first()
    assert action is not None
    assert action.action == "config_toggle"
    assert action.target_id == "toggle_india"

    # Replay: send same callback_id again
    telegram_service.handle_incoming_update(update)
    count = db.query(TelegramCallbackAction).filter(TelegramCallbackAction.callback_id == call_id).count()
    assert count == 1  # Handled only once
    db.close()
