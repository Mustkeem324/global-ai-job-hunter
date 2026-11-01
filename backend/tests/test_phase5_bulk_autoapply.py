import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.schema import (
    JobPosting, Application, JobMatch, CandidateProfile, User,
    ApplicationBatch, ApplicationBatchItem, BatchAuthorization
)
from app.core.state_machine import ApplicationCapability, ApplicationStatus
from app.services.batch_discovery_engine import batch_discovery_engine
from app.services.batch_orchestrator import batch_orchestrator
from app.services.telegram_service import telegram_service

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_phase5_fixtures():
    db = SessionLocal()
    user = db.query(User).first()
    if not user:
        user = User(email="test_phase5@jobhunter.ai", full_name="Mustkeem Ahmad", role="jobseeker")
        db.add(user)
        db.commit()

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

    # Seed 3 distinct jobs for batch testing
    comp_suffix = uuid.uuid4().hex[:6]
    job1 = JobPosting(
        title="AI Evaluation Specialist",
        company_name=f"Scale Benchmark Corp {comp_suffix}",
        location="Worldwide Remote",
        is_india_eligible=True,
        employment_type="Contract",
        compensation_text="$45/hr",
        application_url=f"https://example.com/apply/scale-{comp_suffix}",
        description="RLHF and LLM model reasoning evaluation.",
        source_id="mock_ats",
        source_job_id=f"test-p5-auth-{comp_suffix}",
        status="active",
        application_capability=ApplicationCapability.AUTHORIZED_API_SUBMISSION.value
    )
    job2 = JobPosting(
        title="Senior Python Backend Engineer",
        company_name=f"FastAPI Enterprise {comp_suffix}",
        location="Remote (India)",
        is_india_eligible=True,
        employment_type="Full-Time",
        compensation_text="$75k-$95k",
        application_url=f"https://boards.greenhouse.io/fastapi/jobs/{comp_suffix}",
        description="Python backend engineer with FastAPI, Next.js, PostgreSQL.",
        source_id="greenhouse",
        source_job_id=f"test-p5-rev-{comp_suffix}",
        status="active",
        application_capability=ApplicationCapability.MANUAL_REVIEW_REQUIRED.value
    )
    job3 = JobPosting(
        title="Restricted Onsite Engineer",
        company_name=f"US Defense Local {comp_suffix}",
        location="Washington, DC (US Only)",
        is_india_eligible=False,
        employment_type="Full-Time",
        compensation_text="$150k",
        application_url=f"https://example.com/us-restricted-{comp_suffix}",
        description="US Citizenship required. Onsite only.",
        source_id="lever",
        source_job_id=f"test-p5-inelig-{comp_suffix}",
        status="active",
        application_capability=ApplicationCapability.MANUAL_REVIEW_REQUIRED.value
    )
    db.add(job1)
    db.add(job2)
    db.add(job3)
    db.commit()

    db.refresh(job1)
    db.refresh(job2)
    db.refresh(job3)

    db.add(JobMatch(
        job_id=job1.id, profile_id=prof.id, overall_score=93.0,
        skills_score=28.0, experience_score=19.0, eligibility_score=20.0,
        education_score=9.0, preferences_score=9.0, recency_score=8.0,
        match_tier="Highly suitable", is_india_eligible=True
    ))
    db.add(JobMatch(
        job_id=job2.id, profile_id=prof.id, overall_score=89.0,
        skills_score=27.0, experience_score=18.0, eligibility_score=20.0,
        education_score=8.0, preferences_score=8.0, recency_score=8.0,
        match_tier="Suitable", is_india_eligible=True
    ))
    db.add(JobMatch(
        job_id=job3.id, profile_id=prof.id, overall_score=60.0,
        skills_score=20.0, experience_score=15.0, eligibility_score=0.0,
        education_score=8.0, preferences_score=8.0, recency_score=9.0,
        match_tier="Not suitable", is_india_eligible=False
    ))
    db.commit()

    j1_id = job1.id
    j2_id = job2.id
    j3_id = job3.id
    db.close()

    yield {"j1_id": j1_id, "j2_id": j2_id, "j3_id": j3_id}

def test_preflight_qualification_checks(setup_phase5_fixtures):
    f = setup_phase5_fixtures

    # Job 1 (Authorized sandbox, high match, India eligible)
    res1 = batch_discovery_engine.preflight_job(f["j1_id"])
    assert res1.is_eligible is True
    assert res1.can_auto_submit is True
    assert res1.match_score >= 85.0

    # Job 2 (Greenhouse, manual review required, India eligible)
    res2 = batch_discovery_engine.preflight_job(f["j2_id"])
    assert res2.is_eligible is True
    assert res2.can_auto_submit is False  # Requires manual review
    assert res2.capability == ApplicationCapability.MANUAL_REVIEW_REQUIRED.value

    # Job 3 (Ineligible location)
    res3 = batch_discovery_engine.preflight_job(f["j3_id"])
    assert res3.is_eligible is False
    assert any("Not eligible" in r for r in res3.reasons)

def test_batch_creation_and_session_snapshot(setup_phase5_fixtures):
    batch = batch_discovery_engine.create_batch_session(target_size=10)
    assert batch is not None
    assert batch.batch_id.startswith("BATCH-")
    assert batch.total_jobs > 0
    assert batch.eligible_jobs > 0
    assert batch.status in ("AWAITING_AUTHORIZATION", "COMPLETED_WITH_EXCEPTIONS")

    db = SessionLocal()
    items = db.query(ApplicationBatchItem).filter(ApplicationBatchItem.batch_id == batch.id).all()
    assert len(items) == batch.total_jobs
    db.close()

def test_batch_orchestrator_execution(setup_phase5_fixtures):
    batch = batch_discovery_engine.create_batch_session(target_size=5)

    res = batch_orchestrator.authorize_and_start_batch(batch.batch_id, telegram_user_id="12345678")
    assert res["success"] is True
    assert res["status"] in ("COMPLETED", "COMPLETED_WITH_EXCEPTIONS")
    assert res["submitted_count"] + res["manual_count"] > 0

    # Verify DB state
    db = SessionLocal()
    updated = db.query(ApplicationBatch).filter(ApplicationBatch.id == batch.id).first()
    assert updated.status == "COMPLETED" or updated.status == "COMPLETED_WITH_EXCEPTIONS"
    assert updated.completed_at is not None

    # Check pause & resume methods
    pause_res = batch_orchestrator.pause_batch(batch.batch_id)
    assert pause_res["success"] is True

    resume_res = batch_orchestrator.resume_batch(batch.batch_id)
    assert resume_res["success"] is True

    stop_res = batch_orchestrator.stop_batch(batch.batch_id)
    assert stop_res["success"] is True
    db.close()

def test_batch_api_routes():
    # 1. Create batch via API
    res_create = client.post("/api/v1/batches/create", json={"target_size": 5})
    assert res_create.status_code == 200
    b_data = res_create.json()
    assert b_data["success"] is True
    batch_id = b_data["batch_id"]

    # 2. List batches
    res_list = client.get("/api/v1/batches/")
    assert res_list.status_code == 200
    assert len(res_list.json()) > 0

    # 3. Batch Detail
    res_detail = client.get(f"/api/v1/batches/{batch_id}")
    assert res_detail.status_code == 200
    assert "items" in res_detail.json()

    # 4. Apply Batch
    res_apply = client.post(f"/api/v1/batches/{batch_id}/apply", json={"user_id": "test_runner"})
    assert res_apply.status_code == 200
    assert res_apply.json()["success"] is True

def test_telegram_bulk_callback_handling():
    call_id = f"cb_p5_{uuid.uuid4().hex[:8]}"
    update = {
        "update_id": 999901,
        "callback_query": {
            "id": call_id,
            "from": {"id": 12345678, "first_name": "Mustkeem"},
            "message": {"message_id": 888, "chat": {"id": 12345678}},
            "data": "bulk:find:5"
        }
    }
    telegram_service.handle_incoming_update(update)

    db = SessionLocal()
    from app.models.schema import TelegramCallbackAction, ApplicationBatch
    action = db.query(TelegramCallbackAction).filter(TelegramCallbackAction.callback_id == call_id).first()
    assert action is not None
    assert action.action == "bulk_find_jobs"

    active_batch = db.query(ApplicationBatch).order_by(ApplicationBatch.id.desc()).first()
    assert active_batch is not None
    db.close()
