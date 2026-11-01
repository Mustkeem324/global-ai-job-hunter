import pytest
from app.services.eligibility_engine import eligibility_engine
from app.services.query_planner import query_planner
from app.services.connectors.greenhouse import greenhouse_connector
from app.services.connectors.lever import lever_connector
from app.services.connectors.ashby import ashby_connector
from app.services.connectors.himalayas import himalayas_connector
from app.services.connectors.jobicy import jobicy_connector
from app.services.connectors.remotive import remotive_connector
from app.services.connectors.catalog import catalog_connector, mock_ats_connector
from app.services.telegram_service import telegram_service
from app.core.database import SessionLocal
from app.models.schema import JobPosting, Application, SubmissionEvidence

def test_eligibility_engine_classification():
    # Worldwide Remote
    e1 = eligibility_engine.evaluate_eligibility("Worldwide Remote", "Work from anywhere in the world.")
    assert e1["classification"] == "Worldwide Remote"
    assert e1["is_india_eligible"] is True

    # India explicit
    e2 = eligibility_engine.evaluate_eligibility("Bangalore, India", "Backend engineer.")
    assert e2["classification"] == "Remote — India"
    assert e2["is_india_eligible"] is True

    # US Only restriction
    e3 = eligibility_engine.evaluate_eligibility("Remote", "Candidates must reside in the United States. US work authorization required.")
    assert e3["classification"] == "Remote — US Only"
    assert e3["is_india_eligible"] is False

    # EMEA restriction
    e4 = eligibility_engine.evaluate_eligibility("Europe", "EMEA only timezones.")
    assert e4["classification"] == "Remote — EMEA"
    assert e4["is_india_eligible"] is False

def test_query_planner_keyword_expansion():
    seeds = ["AI Coding Evaluator", "Generative AI Engineer"]
    plan = query_planner.create_query_plan(seeds)
    assert plan["total_queries"] >= 6
    assert any("coding ai trainer" in q for q in plan["expanded_queries"])
    assert any("llm integration developer" in q for q in plan["expanded_queries"])

def test_connector_interface_compliance():
    connectors = [
        greenhouse_connector, lever_connector, ashby_connector,
        himalayas_connector, jobicy_connector, remotive_connector,
        catalog_connector, mock_ats_connector
    ]
    for c in connectors:
        assert hasattr(c, "search_jobs")
        assert hasattr(c, "normalize_job")
        assert hasattr(c, "get_application_capabilities")
        assert hasattr(c, "get_source_permissions")
        assert hasattr(c, "get_rate_limit_policy")
        caps = c.get_application_capabilities()
        assert "mode" in caps

def test_mock_ats_submission_and_canonical_normalization():
    jobs = mock_ats_connector.search_jobs()
    assert len(jobs) == 1
    j = jobs[0]
    assert j["job_id"] == "sandbox-ai-01"
    assert j["application_capability"] == "API_SUBMISSION_AUTHORIZED"
    assert j["is_india_eligible"] is True

def test_telegram_commands_and_job_cards():
    db = SessionLocal()
    job = db.query(JobPosting).first()
    assert job is not None

    # Test job card formatting
    card = telegram_service.format_job_card({
        "id": job.id,
        "company_name": job.company_name,
        "title": job.title,
        "location": job.location,
        "country_eligibility": job.country_eligibility,
        "employment_type": job.employment_type,
        "compensation_text": job.compensation_text,
        "application_url": job.application_url
    }, 91.0)

    assert "🚀 <b>GLOBAL JOB HUNTER AI</b>" in card["text"]
    assert "inline_keyboard" in card["reply_markup"]
    # 5 buttons present across 3 rows
    buttons = [b["text"] for row in card["reply_markup"]["inline_keyboard"] for b in row]
    assert "🚀 Auto Apply" in buttons
    assert "👁 View Job" in buttons
    assert "📄 Review Application" in buttons
    assert "❌ Skip" in buttons
    assert "⭐ Save Job" in buttons

    import uuid
    # Test callback queries for skip and save
    telegram_service.handle_incoming_update({
        "update_id": 111111,
        "callback_query": {
            "id": f"q_save_{uuid.uuid4().hex[:8]}",
            "from": {"id": 12345678},
            "data": f"save:{job.id}"
        }
    })
    assert str(job.id) in telegram_service.saved_jobs

    db.close()
