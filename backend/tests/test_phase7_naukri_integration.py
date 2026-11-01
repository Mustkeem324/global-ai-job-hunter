import uuid
import datetime
import pytest

from app.core.database import SessionLocal
from app.models.schema import (
    JobPosting, Application, User, NaukriJobImport, NaukriNeoStatusRecord,
    NaukriApplicationSource, NaukriProfileRecommendation
)
from app.core.state_machine import ApplicationStatus
from app.services.naukri_adapter import naukri_adapter, NaukriCapabilityMode
from app.services.naukri_discovery_service import naukri_discovery_service
from app.services.naukri_profile_service import naukri_profile_service
from app.services.naukri_neo_service import naukri_neo_service
from app.services.telegram_service import telegram_service

def test_phase7_naukri_capabilities_and_compliance():
    caps = naukri_adapter.get_capabilities()
    assert caps["source"] == "naukri.com"
    # Strict Compliance: Official Partner API must be False unless licensed
    assert caps["capabilities"][NaukriCapabilityMode.OFFICIAL_PARTNER_API] is False
    assert caps["capabilities"][NaukriCapabilityMode.USER_PROVIDED_JOB_IMPORT] is True
    assert caps["capabilities"][NaukriCapabilityMode.MANUAL_APPLICATION_ASSISTANT] is True
    assert caps["capabilities"][NaukriCapabilityMode.EXTERNAL_ATS_APPLICATION] is True

    health = naukri_adapter.get_integration_health()
    assert health["status"] == "HEALTHY"
    assert "STRICT_COMPLIANCE" in health["compliance_status"]

def test_phase7_user_provided_naukri_url_ingestion():
    raw_url = f"https://www.naukri.com/job-listings-ai-training-specialist-outlier-india-noida-delhi-ncr-{uuid.uuid4().hex[:8]}"
    res = naukri_discovery_service.ingest_naukri_url(raw_url)

    assert res["success"] is True
    assert res["is_duplicate"] is False
    assert "ai training specialist" in res["title"].lower()
    assert res["company"] is not None
    assert res["match_score"] >= 80.0
    assert res["capability"] == NaukriCapabilityMode.MANUAL_APPLICATION_ASSISTANT

    # Test Duplicate Detection
    dup_res = naukri_discovery_service.ingest_naukri_url(raw_url)
    assert dup_res["success"] is True
    assert dup_res["is_duplicate"] is True
    assert dup_res["job_id"] == res["job_id"]

def test_phase7_naukri_email_alert_parsing():
    sample_email = (
        "Here are new job recommendations for your profile:\n"
        "1. https://www.naukri.com/job-listings-full-stack-developer-tcs-noida-123456789\n"
        "2. https://www.naukri.com/job-listings-generative-ai-engineer-infosys-gurugram-987654321\n"
        "Apply now on Naukri."
    )
    extracted = naukri_discovery_service.parse_naukri_alert_text(sample_email)
    assert len(extracted) == 2
    assert any("full-stack-developer" in j["job_url"].lower() for j in extracted)
    assert any("generative-ai-engineer" in j["job_url"].lower() for j in extracted)

def test_phase7_naukri_profile_optimization_constraints():
    pkg = naukri_profile_service.generate_profile_optimization_package()
    assert pkg["success"] is True
    assert pkg["candidate"] == "Mustkeem Ahmad"

    # Naukri 250 character limit constraint on headline
    headline = pkg["recommended_headline"]
    assert len(headline) <= 250
    assert "Python" in headline or "AI" in headline
    assert "UPES" in headline or "Jamia" in headline

    # Naukri Key Skills tags (comma-separated format)
    skills = pkg["key_skills_csv"].split(", ")
    assert len(skills) >= 10
    assert "FastAPI" in skills or "Python" in skills
    assert "RLHF Evaluation" in skills or "LLM Benchmarking" in skills

    # Profile summary
    assert "Outlier AI" in pkg["profile_summary"] or "Handshake Dynamo" in pkg["profile_summary"]

def test_phase7_naukri_application_package_preparation():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        token = uuid.uuid4().hex[:6]
        job = JobPosting(
            source_id="naukri",
            source_job_id=f"nk-{token}",
            title="Senior Python & LLM Benchmark Engineer",
            company_name=f"Scale India {token}",
            location="Noida, India",
            is_india_eligible=True,
            employment_type="Full-Time",
            compensation_text="₹25,00,000 - ₹35,00,000 P.A.",
            description="Evaluate prompt responses and build backend benchmark pipelines in Python.",
            application_url=f"https://www.naukri.com/job-listings-{token}",
            status="active"
        )
        db.add(job)
        db.commit()

        pkg = naukri_adapter.create_application_package(job.id)
        assert pkg["success"] is True
        assert pkg["company"] == f"Scale India {token}"
        assert pkg["capability"] == NaukriCapabilityMode.MANUAL_APPLICATION_ASSISTANT
        assert "screening_answers" in pkg
        sa = pkg["screening_answers"]
        assert "Immediate" in sa["notice_period"]
        assert "2+ years" in sa["total_experience"]
        assert len(pkg["tailored_resume_text"]) > 100
    finally:
        db.close()

def test_phase7_naukri_neo_tracking_and_provenance():
    msg_id = f"neo_confirm_{uuid.uuid4().hex[:8]}"
    company = "Cognizant India"
    title = "Lead AI Prompt Evaluator"

    # Record Neo confirmation
    res = naukri_neo_service.record_neo_application_confirmation(
        email_message_id=msg_id,
        job_title=title,
        company_name=company
    )

    assert res["success"] is True
    assert res["status"] == "RECORDED"
    assert res["provenance"] == "NAUKRI_NEO"

    db = SessionLocal()
    try:
        # Verify provenance record in DB
        app_id = res["canonical_application_id"]
        source_rec = db.query(NaukriApplicationSource).filter(
            NaukriApplicationSource.application_id == app_id
        ).first()
        assert source_rec is not None
        assert source_rec.source_type == "NAUKRI_NEO"

        # Verify application status was set to SUBMITTED_CONFIRMED
        app_rec = db.query(Application).filter(Application.id == app_id).first()
        assert app_rec.status == ApplicationStatus.SUBMITTED_CONFIRMED
        assert "NEO-" in app_rec.confirmation_receipt_id
    finally:
        db.close()

def test_phase7_multi_job_batch_preparation():
    batch = naukri_discovery_service.prepare_naukri_batch(batch_size=5, min_match_score=80)
    assert batch["success"] is True
    assert "summary" in batch
    sm = batch["summary"]
    assert "ready_for_manual" in sm
    assert "already_applied" in sm

def test_phase7_telegram_naukri_job_card():
    card = telegram_service.format_naukri_job_card({
        "id": 555,
        "title": "Generative AI Developer",
        "company_name": "Wipro Frontier AI",
        "location": "Gurugram, India",
        "compensation_text": "₹30 LPA",
        "employment_type": "Full-Time",
        "application_url": "https://www.naukri.com/job-listings-555",
        "capability": "MANUAL_APPLICATION_ASSISTANT"
    }, 92.0)

    assert "NAUKRI JOB MATCH" in card["text"]
    assert "Wipro Frontier AI" in card["text"]
    assert "92/100" in card["text"]
    assert "inline_keyboard" in card["reply_markup"]
    buttons = [b["text"] for row in card["reply_markup"]["inline_keyboard"] for b in row]
    assert "👁 View Job" in buttons
    assert "📝 Prepare Application" in buttons
