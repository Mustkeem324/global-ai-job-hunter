import uuid
import datetime
import pytest
from app.core.database import SessionLocal
from app.models.schema import (
    JobPosting, Application, User, RecruiterMessage, RecruiterContact,
    InterviewEvent, AssessmentEvent, OfferRecord, FollowupDraft,
    FollowupRecommendation, FollowupApproval
)
from app.core.state_machine import ApplicationStatus
from app.services.email_classifier import email_classifier
from app.services.gmail_service import gmail_service
from app.services.recruiter_crm_service import recruiter_crm
from app.services.followup_agent import followup_agent
from app.services.interview_intelligence_service import interview_intelligence_service
from app.services.recruiter_analytics_service import recruiter_analytics
from app.services.multi_agent_orchestrator import (
    JobDiscoveryAgent, ResumeMatchingAgent, ApplicationExecutionAgent,
    RecruiterIntelligenceAgent, FollowUpAgent, InterviewAgent,
    AnalyticsAgent, AgentSecurityException
)
from app.services.telegram_service import telegram_service

def test_phase6_email_classification_and_entity_extraction():
    # 1. Offer Received
    res_offer = email_classifier.classify_email(
        subject="Offer of Employment - AI Research Engineer at Scale AI",
        body="We are pleased to offer you the position of AI Research Engineer. The compensation details are attached.",
        sender_email="recruiting@scale.com"
    )
    assert res_offer.category == "OFFER_RECEIVED"
    assert res_offer.confidence >= 0.90
    assert res_offer.company in ("Scale", "Scale AI", "Employer")

    # 2. Coding Test
    res_coding = email_classifier.classify_email(
        subject="Coding Challenge for Python AI Specialist",
        body="Please complete the online coding test on HackerRank before November 10, 2026.",
        sender_email="eval@hackerrank.com"
    )
    assert res_coding.category in ("CODING_TEST", "ASSESSMENT_INVITATION")
    assert res_coding.confidence >= 0.90

    # 3. Recruiter Question
    res_q = email_classifier.classify_email(
        subject="Quick question regarding your availability",
        body="Hi Mustkeem, what is your notice period and expected hourly rate for this engagement?",
        sender_email="sarah.connor@frontierai.io"
    )
    assert res_q.category == "RECRUITER_QUESTION"
    assert "sarah" in res_q.recruiter_name.lower() or "recruiting" in res_q.recruiter_name.lower()

    # 4. Unrelated Promotional Email
    res_spam = email_classifier.classify_email(
        subject="Black Friday 50% discount sale on cloud subscriptions",
        body="Unsubscribe here to stop receiving promotional newsletters.",
        sender_email="newsletter@cloudpromos.com"
    )
    assert res_spam.category == "UNRELATED_EMAIL"

def test_phase6_interview_timezone_conversion_to_kolkata():
    # PST to IST (+13.5 hours PDT or +12.5 PST)
    # Testing datetime string parsing
    pst_str = "Friday, November 06, 2026 at 10:00 AM PST"
    kolkata_dt = interview_intelligence_service.parse_and_convert_to_kolkata(pst_str, "PST")
    assert kolkata_dt.tzinfo is not None
    assert str(kolkata_dt.tzinfo) == "Asia/Kolkata"
    # 10:00 AM PST is 11:30 PM IST on the same day (or next day depending on DST)
    assert kolkata_dt.hour in (22, 23, 23, 0)

def test_phase6_recruiter_crm_and_message_correlation():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        unique_token = uuid.uuid4().hex[:6]
        comp_name = f"Apex AI Corp {unique_token}"
        receipt_id = f"CONF-{uuid.uuid4().hex[:8].upper()}"

        job = JobPosting(
            title="Senior AI Prompt Evaluator",
            company_name=comp_name,
            location="Remote Worldwide",
            is_india_eligible=True,
            employment_type="Contract",
            compensation_text="$65/hr",
            description="Evaluate RLHF prompt outputs and benchmark performance.",
            application_url="https://apexai.example/apply",
            source_id="greenhouse",
            source_job_id=f"apex-{unique_token}",
            status="active"
        )
        db.add(job)
        db.flush()

        app = Application(
            job_id=job.id,
            user_id=user.id if user else 1,
            status=ApplicationStatus.SUBMITTED_CONFIRMED,
            idempotency_key=f"idemp-p6-{unique_token}",
            match_score=94.0,
            confirmation_receipt_id=receipt_id,
            applied_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=12)
        )
        db.add(app)
        db.commit()
        db.refresh(app)

        # 1. Process incoming email with exact receipt ID
        sender = f"recruiting@{comp_name.lower().replace(' ', '')}.com"
        msg_res = gmail_service.process_incoming_email(
            message_id=f"msg_p6_{unique_token}",
            sender_email=sender,
            subject=f"Interview Invitation for Senior AI Prompt Evaluator ({receipt_id})",
            body=f"Hello Mustkeem, we would love to speak with you regarding {receipt_id}. Join us on Google Meet at meet.google.com/abc-defg-hij on Friday at 3:00 PM IST."
        )

        assert msg_res["status"] == "PROCESSED"
        assert msg_res["classification"] == "INTERVIEW_INVITATION"
        assert msg_res["correlated_application_id"] == app.id
        assert msg_res["match_type"] == "EXACT_RECEIPT_ID"

        # Check CRM contact was created
        contact = db.query(RecruiterContact).filter(RecruiterContact.email == sender).first()
        assert contact is not None
        assert comp_name in contact.company

        # Verify Interview Event registered in Kolkata time
        intv = db.query(InterviewEvent).filter(InterviewEvent.application_id == app.id).first()
        assert intv is not None
        assert intv.meeting_platform == "GOOGLE_MEET"
        assert intv.meeting_url == "https://meet.google.com/abc-defg-hij"
    finally:
        db.close()

def test_phase6_strict_human_in_the_loop_followup_workflow():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        token = uuid.uuid4().hex[:6]
        comp = f"RoboTech Systems {token}"

        job = JobPosting(
            title="Full-Stack Engineer",
            company_name=comp,
            location="Remote",
            is_india_eligible=True,
            employment_type="Full-Time",
            compensation_text="$95,000",
            description="Python FastAPI and Next.js full stack developer.",
            application_url="https://robotech.example/apply",
            source_id="lever",
            source_job_id=f"robo-{token}",
            status="active"
        )
        db.add(job)
        db.flush()

        app = Application(
            job_id=job.id,
            user_id=user.id if user else 1,
            status=ApplicationStatus.SUBMITTED_CONFIRMED,
            idempotency_key=f"idemp-fup-{token}",
            match_score=91.0,
            confirmation_receipt_id=f"CONF-{uuid.uuid4().hex[:8].upper()}",
            applied_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=15)
        )
        db.add(app)
        db.commit()
        db.refresh(app)

        # 1. Scan recommendations
        recs = followup_agent.scan_for_followup_recommendations()
        matched_rec = next((r for r in recs if r["application_id"] == app.id), None)
        assert matched_rec is not None
        assert matched_rec["type"] == "STATUS_FOLLOWUP"

        # 2. Draft personalized message (MUST NOT send automatically)
        draft = followup_agent.generate_draft_for_recommendation(matched_rec["recommendation_id"])
        assert draft["success"] is True
        assert draft["status"] == "DRAFTED"
        assert "Mustkeem Ahmad" in draft["body"]
        assert "UPES" in draft["body"] or "RLHF" in draft["body"] or "full-stack" in draft["body"]

        # 3. Explicit Approval required
        approval_res = followup_agent.review_and_approve_followup(
            draft_id=draft["draft_id"],
            approved_by="telegram_admin",
            modified_body=draft["body"] + "\n\nPS: Looking forward to connecting."
        )
        assert approval_res["success"] is True
        assert approval_res["status"] == "SENT"

        # Verify Approval record in DB
        appr_db = db.query(FollowupApproval).filter(
            FollowupApproval.followup_draft_id == draft["draft_id"]
        ).first()
        assert appr_db is not None
        assert appr_db.approved_by == "telegram_admin"
    finally:
        db.close()

def test_phase6_personalized_interview_preparation():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        token = uuid.uuid4().hex[:6]
        job = JobPosting(
            title="Lead RLHF & AI Evaluation Specialist",
            company_name=f"Frontier Eval {token}",
            location="Remote",
            is_india_eligible=True,
            employment_type="Full-Time",
            compensation_text="$110k",
            description="Design benchmarks, evaluate LLM outputs for sycophancy and logical consistency.",
            application_url="https://eval.example/jobs",
            source_id="ashby",
            source_job_id=f"eval-{token}",
            status="active"
        )
        db.add(job)
        db.flush()

        app = Application(
            job_id=job.id,
            user_id=user.id if user else 1,
            status=ApplicationStatus.INTERVIEW,
            idempotency_key=f"idemp-prep-{token}",
            match_score=96.0
        )
        db.add(app)
        db.commit()

        prep = interview_intelligence_service.generate_interview_preparation(app.id)
        assert prep["success"] is True
        assert prep["domain"] == "AI_TRAINING_EVAL"
        assert prep["candidate"] == "Mustkeem Ahmad"
        assert len(prep["grounded_credentials"]) >= 4
        assert len(prep["prep_content"]["key_focus_areas"]) >= 3
        # Ensure questions are grounded
        qa = prep["prep_content"]["sample_questions_and_grounded_answers"]
        assert len(qa) >= 1
        assert "Outlier AI" in qa[0]["suggested_answer"] or "RLHF" in qa[0]["suggested_answer"]
    finally:
        db.close()

def test_phase6_application_funnel_and_optimization_metrics():
    metrics = recruiter_analytics.calculate_funnel_metrics()
    assert "total_applications" in metrics
    assert "confirmed_submitted" in metrics
    assert "rates" in metrics
    assert "response_rate" in metrics["rates"]
    assert "interview_rate" in metrics["rates"]
    assert "offer_rate" in metrics["rates"]
    # Check exact numerator / denominator reporting
    resp = metrics["rates"]["response_rate"]
    assert "numerator" in resp
    assert "denominator" in resp
    assert resp["denominator"] >= 1

    # Check search optimization recommendations
    recs = recruiter_analytics.generate_search_optimization_recommendations()
    assert isinstance(recs, list)
    assert len(recs) >= 1

def test_phase6_multi_agent_security_isolation():
    disc_agent = JobDiscoveryAgent()
    rec_agent = RecruiterIntelligenceAgent()

    # 1. Discovery agent must not have permission to execute application submissions
    with pytest.raises(AgentSecurityException) as exc_info:
        disc_agent.verify_permission("EXECUTE_SUBMISSION")
    assert "Security Boundary Violation" in str(exc_info.value)

    # 2. Recruiter agent must not have permission to execute application submissions
    with pytest.raises(AgentSecurityException):
        rec_agent.verify_permission("EXECUTE_SUBMISSION")

    # 3. Discovery agent has READ_JOBS_DISCOVERY
    disc_agent.verify_permission("READ_JOBS_DISCOVERY")

def test_phase6_telegram_recruiter_response_card():
    card = telegram_service.format_recruiter_response_card({
        "company": "Scale Benchmark Corp",
        "role": "AI Evaluator",
        "recruiter": "David Miller",
        "received_at": "Today 10:30 AM",
        "category": "INTERVIEW_INVITATION",
        "confidence": 0.95,
        "application_id": 101,
        "message_id": "msg_test_101",
        "interview_date": "Nov 05, 2026",
        "interview_timezone": "Asia/Kolkata"
    })
    assert "RECRUITER RESPONSE DETECTED" in card["text"]
    assert "Scale Benchmark Corp" in card["text"]
    assert "95%" in card["text"]
    assert "inline_keyboard" in card["reply_markup"]
    buttons = [b["text"] for row in card["reply_markup"]["inline_keyboard"] for b in row]
    assert "👁 View Email" in buttons
    assert "✍️ Prepare Reply" in buttons
    assert "📅 Review Interview" in buttons
