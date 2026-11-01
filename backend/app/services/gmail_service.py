import uuid
import datetime
from typing import Dict, Any, List, Optional

from app.core.database import SessionLocal
from app.models.schema import Application, JobPosting, RecruiterMessage, RecruiterEvent
from app.core.state_machine import ApplicationStatus
from app.services.email_classifier import email_classifier

class GmailMonitoringService:
    """
    Phase 3 Module 9 & Phase 4 Module 6: Gmail Employer Response Monitoring Service
    Synchronizes recruitment correspondence, extracts status changes, and correlates messages.
    """

    def __init__(self):
        self.is_connected = False
        self.last_history_id = None

    def correlate_message_to_application(self, sender_email: str, subject: str, body: str) -> Optional[int]:
        """
        Correlates incoming email to an existing application record
        using employer domain, company name, or ATS receipt numbers.
        """
        db = SessionLocal()
        try:
            apps = db.query(Application).all()
            sender_domain = sender_email.split("@")[-1].lower() if "@" in sender_email else ""
            full_text = f"{subject} {body}".lower()

            for app in apps:
                job = app.job_posting
                company = (job.company_name or "").lower()
                receipt = (app.confirmation_receipt_id or "").lower()

                # Strong Match 1: Confirmation ID present in email
                if receipt and receipt in full_text:
                    return app.id

                # Match 2: Company name or domain in text
                if len(company) > 3 and (company in full_text or company in sender_domain):
                    return app.id

            return None
        finally:
            db.close()

    def process_incoming_email(
        self,
        message_id: str,
        sender_email: str,
        subject: str,
        body: str,
        received_at: Optional[datetime.datetime] = None
    ) -> Dict[str, Any]:
        """
        Classifies incoming email, correlates with application, persists record,
        and triggers state machine update if applicable.
        """
        dt = received_at or datetime.datetime.now(datetime.timezone.utc)
        classification = email_classifier.classify_email(subject, body, sender_email)
        app_id = self.correlate_message_to_application(sender_email, subject, body)

        db = SessionLocal()
        try:
            # Check deduplication
            existing = db.query(RecruiterMessage).filter(RecruiterMessage.message_id == message_id).first()
            if existing:
                return {"status": "ALREADY_PROCESSED", "id": existing.id}

            domain = sender_email.split("@")[-1] if "@" in sender_email else "unknown"
            msg_rec = RecruiterMessage(
                application_id=app_id,
                message_id=message_id,
                sender_email=sender_email,
                sender_domain=domain,
                subject=subject,
                body_text=body,
                received_at=dt,
                classification=classification.category,
                confidence=classification.confidence,
                matched_criteria=classification.matched_criteria,
                requires_action=classification.category in ("INTERVIEW_INVITATION", "ASSESSMENT_INVITATION", "OFFER_RECEIVED", "RECRUITER_QUESTION")
            )
            db.add(msg_rec)
            db.flush()

            # State transition if correlated and high confidence
            new_status = None
            if app_id and classification.confidence >= 0.80:
                app_rec = db.query(Application).filter(Application.id == app_id).first()
                if app_rec:
                    if classification.category == "INTERVIEW_INVITATION":
                        app_rec.status = ApplicationStatus.INTERVIEW
                        new_status = "INTERVIEW"
                    elif classification.category == "OFFER_RECEIVED":
                        app_rec.status = ApplicationStatus.OFFER
                        new_status = "OFFER"
                    elif classification.category == "REJECTION":
                        app_rec.status = ApplicationStatus.REJECTED
                        app_rec.failure_reason = "Employer notification received: Not proceeding."
                        new_status = "REJECTED"
                    elif classification.category == "APPLICATION_UNDER_REVIEW":
                        app_rec.status = ApplicationStatus.UNDER_REVIEW
                        new_status = "UNDER_REVIEW"

            db.commit()

            return {
                "status": "PROCESSED",
                "message_id": message_id,
                "classification": classification.category,
                "confidence": classification.confidence,
                "correlated_application_id": app_id,
                "new_application_status": new_status,
                "requires_action": msg_rec.requires_action
            }
        finally:
            db.close()

gmail_service = GmailMonitoringService()
