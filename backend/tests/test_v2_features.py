import pytest
import os
import json
from app.services.resume_parser import resume_parser_service
from app.services.telegram_service import telegram_service
from app.core.database import SessionLocal
from app.models.schema import CandidateProfile, JobPosting, JobMatch, Application, SubmissionEvidence

def test_resume_parser_v2_extraction():
    sample_text = (
        "Mustkeem Ahmad\n"
        "AI Trainer / LLM Evaluation Contributor\n"
        "mustkeem324@gmail.com | +91-7905800532 | Hyderabad, India\n"
        "https://github.com/Mustkeem324\n"
        "Handshake Project Dynamo - AI Trainer\n"
        "Outlier AI - Generative AI Engineer & Model Evaluation Consultant (Contract)\n"
        "FreelanceKar.com - Founder (200+ projects)\n"
        "Skills: Python, Django, FastAPI, React, Next.js, RLHF, LLM Evaluation, Prompt Engineering, PostgreSQL, AWS\n"
        "Education: MBA (UPES, 8.90 CGPA), B.Tech Electrical (Jamia Millia Islamia, 83.3%)\n"
    )
    profile = resume_parser_service.parse_profile(sample_text, "test_resume.txt")
    
    assert profile["full_name"] == "Mustkeem Ahmad"
    assert profile["email"] == "mustkeem324@gmail.com"
    assert len(profile["skills"]) > 5
    assert len(profile["education"]) >= 2
    assert len(profile["experiences"]) >= 3
    assert len(profile["projects"]) >= 3
    assert len(profile["traceable_claims"]) > 5
    assert profile["work_authorization"]["remote_work_eligible"] is True

def test_telegram_one_click_auto_apply_callback():
    db = SessionLocal()
    job = db.query(JobPosting).first()
    assert job is not None

    update = {
        "update_id": 88888,
        "callback_query": {
            "id": "query_test_auto_apply",
            "from": {"id": 12345678, "first_name": "Mustkeem"},
            "message": {"message_id": 555, "chat": {"id": 12345678}},
            "data": f"auto_apply:{job.id}"
        }
    }

    telegram_service.handle_incoming_update(update)

    app_rec = db.query(Application).filter(Application.job_id == job.id).first()
    assert app_rec is not None
    assert app_rec.status.value == "SUBMITTED_CONFIRMED"
    assert app_rec.tailored_summary is not None
    assert app_rec.cover_letter is not None

    evidence = db.query(SubmissionEvidence).filter(SubmissionEvidence.application_id == app_rec.id).first()
    assert evidence is not None
    assert evidence.confirmation_id.startswith("CONF-")
    assert evidence.verified is True
    db.close()
