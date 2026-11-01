import pytest
import uuid
import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.schema import JobPosting, Application, JobMatch, CandidateProfile, User, FollowupDraft
from app.core.state_machine import ApplicationStatus
from app.services.resume_tailoring import resume_tailoring_service
from app.services.form_intelligence import form_intelligence_service
from app.services.email_classifier import email_classifier
from app.services.gmail_service import gmail_service
from app.services.followup_agent import followup_agent
from app.services.prioritization_engine import prioritization_engine

client = TestClient(app)

def test_multi_variant_resume_tailoring_and_hallucination_blocking():
    # 1. Test variant selection
    variant_ai = resume_tailoring_service.select_variant_type("Senior RLHF AI Trainer", "Evaluate multi-turn reasoning and prompt calibration.")
    assert variant_ai == "AI_TRAINING"

    variant_eval = resume_tailoring_service.select_variant_type("LLM Evaluation Specialist", "Benchmark models, red teaming, and safety assessments.")
    assert variant_eval == "LLM_EVALUATION"

    variant_fullstack = resume_tailoring_service.select_variant_type("Full Stack Python & Next.js Developer", "Build web applications.")
    assert variant_fullstack == "FULLSTACK"

    # 2. Test tailoring execution
    job_mock = {
        "id": 999,
        "title": "AI Model Evaluation Specialist",
        "company_name": "Frontier AI Labs",
        "description": "Looking for model evaluation contributors in India."
    }
    result = resume_tailoring_service.tailor_resume(job_mock)
    assert result.variant_type == "LLM_EVALUATION"
    assert "UPES" in result.tailored_summary
    assert "Jamia Millia Islamia" in result.formatted_resume_text
    assert result.validation_status == "VALIDATED"
    assert len(result.unsupported_claims) == 0

    # 3. Test hallucination blocking validator
    fabricated_claims = [
        "Candidate holds a Ph.D from MIT with 15+ years experience as VP of Engineering."
    ]
    val_res = resume_tailoring_service.validate_factual_claims(resume_tailoring_service.CANONICAL_FACTS, fabricated_claims)
    assert val_res["is_valid"] is False
    assert val_res["validation_status"] == "REJECTED_UNSUPPORTED_CLAIMS"
    assert len(val_res["unsupported_claims"]) > 0

def test_form_intelligence_and_field_mapping():
    raw_fields = [
        {"id": "c_fname", "name": "First Name", "type": "text", "required": True},
        {"id": "c_email", "name": "Email Address", "type": "email", "required": True},
        {"id": "c_nda", "name": "Do you accept the binding Non-Disclosure Agreement?", "type": "checkbox", "required": True}
    ]
    discovered = form_intelligence_service.extract_form_fields(raw_fields)
    assert len(discovered) == 3

    mapped = form_intelligence_service.map_fields(discovered, {"first_name": "Mustkeem", "email": "mustkeem324@gmail.com"})
    assert mapped[0].proposed_value == "Mustkeem"
    assert mapped[1].proposed_value == "mustkeem324@gmail.com"
    # NDA requires human review
    assert mapped[2].requires_manual_review is True

    val = form_intelligence_service.validate_mapped_answers(mapped)
    assert val["can_auto_submit"] is False
    assert any("Agreement" in r for r in val["review_required"])

def test_recruitment_email_classification():
    # 1. Interview Invitation
    res_interview = email_classifier.classify_email(
        subject="Invitation to Interview for AI Engineer at Scale AI",
        body="We were impressed with your background and would like to invite you for an interview. Please select a time slot on Calendly.",
        sender_email="recruiting@scale.com"
    )
    assert res_interview.category == "INTERVIEW_INVITATION"
    assert res_interview.confidence >= 0.85

    # 2. Rejection Email
    res_rejection = email_classifier.classify_email(
        subject="Application status: Full-Stack Developer",
        body="Thank you for your interest. We have decided to move forward with other candidates at this time.",
        sender_email="jobs@techcorp.com"
    )
    assert res_rejection.category == "REJECTION"

    # 3. Assessment Invitation
    res_assessment = email_classifier.classify_email(
        subject="Coding Assessment for AI Specialist",
        body="Please complete the following technical assessment on HackerRank within 48 hours.",
        sender_email="eval@frontier.io"
    )
    assert res_assessment.category == "ASSESSMENT_INVITATION"

def test_gmail_response_correlation_and_state_transition():
    db = SessionLocal()
    # Create test job and application
    job = JobPosting(
        title="Generative AI Engineer",
        company_name="Anthropic Partner Co",
        location="Worldwide Remote",
        is_india_eligible=True,
        employment_type="Full-Time",
        compensation_text="$90k",
        description="Generative AI engineer position focusing on LLM models and APIs.",
        application_url="https://example.com/apply-genai",
        source_id="catalog",
        source_job_id=f"test-gmail-{uuid.uuid4().hex[:6]}",
        status="active"
    )
    db.add(job)
    db.flush()

    user = db.query(User).first()
    conf_id = f"CONF-{uuid.uuid4().hex[:8].upper()}"
    app_rec = Application(
        job_id=job.id,
        user_id=user.id if user else 1,
        status=ApplicationStatus.SUBMITTED_CONFIRMED,
        idempotency_key=f"tg-gmail-{job.id}-{uuid.uuid4().hex[:6]}",
        match_score=92.0,
        confirmation_receipt_id=conf_id,
        applied_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    )
    db.add(app_rec)
    db.commit()
    db.refresh(app_rec)
    app_id = app_rec.id

    # Test correlation by confirmation ID in email body
    corr_id = gmail_service.correlate_message_to_application(
        sender_email="talent@anthropicpartner.com",
        subject="Interview Scheduling",
        body=f"Regarding your application reference {conf_id}, we would like to schedule an interview."
    )
    assert corr_id == app_id

    # Test process incoming email updates application status to INTERVIEW
    res = gmail_service.process_incoming_email(
        message_id=f"msg_{uuid.uuid4().hex[:8]}",
        sender_email="talent@anthropicpartner.com",
        subject="Interview Scheduling",
        body=f"Regarding your application reference {conf_id}, we would like to schedule an interview."
    )
    assert res["status"] == "PROCESSED"
    assert res["new_application_status"] == "INTERVIEW"

    # Verify DB update
    db.expire_all()
    updated_app = db.query(Application).filter(Application.id == app_id).first()
    assert updated_app.status == ApplicationStatus.INTERVIEW

    # Test Follow-up agent scanning and draft generation
    candidates = followup_agent.scan_for_followup_candidates(min_days_elapsed=7)
    # Draft generation
    draft_res = followup_agent.generate_followup_draft(app_id)
    assert draft_res["success"] is True
    assert draft_res["status"] == "DRAFTED"

    # Candidate approval
    appr_res = followup_agent.approve_and_send_followup(draft_res["draft_id"])
    assert appr_res["success"] is True
    assert appr_res["status"] == "SENT"
    db.close()

def test_intelligent_prioritization_and_feedback():
    job_sample = {
        "id": 888,
        "title": "Senior AI Trainer",
        "company_name": "Scale AI",
        "location": "Remote (Worldwide)",
        "compensation_text": "$50/hr USD",
        "category": "AI Training",
        "is_india_eligible": True,
        "source_id": "greenhouse",
        "application_capability": "AUTHORIZED_API_SUBMISSION"
    }
    pri_res = prioritization_engine.calculate_priority(job_sample, match_score=94.0)
    assert pri_res.priority_score >= 85.0
    assert pri_res.priority_tier == "PRIORITY_A"
    assert "compatibility" in pri_res.explanation

    # Record user feedback (SAVED)
    fb_res = prioritization_engine.record_user_feedback(888, "SAVED")
    assert fb_res["success"] is True
    assert fb_res["affinity_delta"] == 0.5

def test_analytics_csv_export():
    response = client.get("/api/v1/analytics/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert "Application ID" in response.text
    assert "Company Name" in response.text
