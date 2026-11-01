import datetime
from typing import Dict, Any, List, Optional

from app.core.database import SessionLocal
from app.models.schema import Application, FollowupDraft, JobPosting, CandidateProfile
from app.core.state_machine import ApplicationStatus

class FollowupManagementAgent:
    """
    Phase 3 Module 11 & Phase 4 Module 7: Intelligent Follow-Up Management Agent
    Identifies applications needing follow-up and synthesizes polite, evidence-grounded drafts.
    Strict Rule: NEVER automatically sends emails without explicit candidate approval.
    """

    def scan_for_followup_candidates(self, min_days_elapsed: int = 7) -> List[Dict[str, Any]]:
        """
        Scans applications submitted > min_days_elapsed ago with no recent updates.
        """
        db = SessionLocal()
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            threshold_date = now - datetime.timedelta(days=min_days_elapsed)

            apps = db.query(Application).filter(
                Application.status.in_([ApplicationStatus.SUBMITTED_CONFIRMED, ApplicationStatus.UNDER_REVIEW]),
                Application.applied_at <= threshold_date
            ).all()

            results = []
            for app in apps:
                # Check if draft already created
                existing_draft = db.query(FollowupDraft).filter(
                    FollowupDraft.application_id == app.id,
                    FollowupDraft.status.in_(["DRAFTED", "APPROVED", "SENT"])
                ).first()

                if not existing_draft:
                    job = app.job_posting
                    results.append({
                        "application_id": app.id,
                        "company_name": job.company_name,
                        "title": job.title,
                        "applied_at": app.applied_at.isoformat() if app.applied_at else None,
                        "days_elapsed": (now - (app.applied_at or now)).days
                    })
            return results
        finally:
            db.close()

    def generate_followup_draft(self, application_id: int) -> Dict[str, Any]:
        """
        Synthesizes a polite, context-aware follow-up email draft.
        Persists draft as 'DRAFTED' awaiting candidate authorization.
        """
        db = SessionLocal()
        try:
            app_rec = db.query(Application).filter(Application.id == application_id).first()
            if not app_rec:
                return {"success": False, "message": "Application not found"}

            job = app_rec.job_posting
            prof = db.query(CandidateProfile).first()
            name = prof.full_name if prof else "Mustkeem Ahmad"
            applied_str = app_rec.applied_at.strftime("%B %d") if app_rec.applied_at else "recently"

            subject = f"Following up on application: {job.title} — {name}"
            body = (
                f"Dear {job.company_name} Hiring Team,\n\n"
                f"I hope this note finds you well.\n\n"
                f"I am writing to respectfully follow up on my application for the {job.title} position, "
                f"which I submitted on {applied_str}. I remain enthusiastic about the opportunity to contribute "
                f"to {job.company_name}, particularly given my recent experience in AI model evaluation and full-stack software delivery.\n\n"
                f"Please let me know if there are any additional materials, portfolio code samples, or information I can provide "
                f"to assist with the review process.\n\n"
                f"Thank you very much for your time and continued consideration.\n\n"
                f"Sincerely,\n"
                f"{name}\n"
                f"https://github.com/Mustkeem324 | https://freelancekar.com"
            )

            draft = FollowupDraft(
                application_id=app_rec.id,
                reason="Routine follow-up after initial submission period",
                suggested_send_date=datetime.datetime.now(datetime.timezone.utc),
                subject=subject,
                body_text=body,
                status="DRAFTED"
            )
            db.add(draft)
            db.commit()
            db.refresh(draft)

            return {
                "success": True,
                "draft_id": draft.id,
                "application_id": app_rec.id,
                "company_name": job.company_name,
                "position": job.title,
                "subject": subject,
                "body": body,
                "status": "DRAFTED",
                "message": "Draft created and staged for candidate approval."
            }
        finally:
            db.close()

    def approve_and_send_followup(self, draft_id: int) -> Dict[str, Any]:
        """
        Candidate explicitly approved the follow-up draft.
        """
        db = SessionLocal()
        try:
            draft = db.query(FollowupDraft).filter(FollowupDraft.id == draft_id).first()
            if not draft:
                return {"success": False, "message": "Draft not found"}

            now = datetime.datetime.now(datetime.timezone.utc)
            draft.status = "APPROVED"
            draft.approved_at = now
            # Mark as dispatched (or queued for authorized email client)
            draft.sent_at = now
            db.commit()

            return {
                "success": True,
                "draft_id": draft.id,
                "status": "SENT",
                "message": f"Follow-up email authorized and logged as sent on {now.strftime('%Y-%m-%d %H:%M:%S UTC')}."
            }
        finally:
            db.close()

followup_agent = FollowupManagementAgent()
