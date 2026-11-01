from typing import Dict, Any, Optional
from app.core.database import SessionLocal
from app.models.schema import Application, JobPosting, CandidateProfile, ApplicationEvent
from app.core.state_machine import ApplicationStatus

class TelegramApprovalService:
    """
    Phase 2 Section 7: Telegram Approval Queue & Document Review Service
    """

    def format_approval_card(self, application_id: int) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            app_rec = db.query(Application).filter(Application.id == application_id).first()
            if not app_rec:
                return None

            job = app_rec.job_posting
            resume_name = app_rec.resume_version or "resume.pdf"
            cover_excerpt = (app_rec.cover_letter or "Tailored cover letter generated from resume evidence.")[:350]
            method = app_rec.application_method or "USER_REVIEW_REQUIRED"

            text = (
                f"📋 <b>APPLICATION READY FOR REVIEW</b>\n\n"
                f"🏢 <b>Company:</b> {job.company_name}\n"
                f"💼 <b>Position:</b> {job.title}\n"
                f"🎯 <b>Match Score:</b> <b>{int(app_rec.match_score)}/100</b>\n"
                f"📄 <b>Resume:</b> <code>{resume_name}</code>\n"
                f"⚙️ <b>Application Method:</b> <code>{method}</code>\n\n"
                f"📝 <b>Generated Cover Letter Excerpt:</b>\n"
                f"<i>\"{cover_excerpt}...\"</i>\n\n"
                f"Review the staged documents above and authorize submission below:"
            )

            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "✅ Approve", "callback_data": f"appr:{application_id}"},
                        {"text": "✏️ Edit", "callback_data": f"edit:{application_id}"}
                    ],
                    [
                        {"text": "❌ Reject", "callback_data": f"rej:{application_id}"},
                        {"text": "🌐 Open Application", "url": job.application_url}
                    ]
                ]
            }

            return {"text": text, "reply_markup": reply_markup}
        finally:
            db.close()

    def handle_approve(self, application_id: int) -> Dict[str, Any]:
        """Candidate authorized submission of staged application."""
        db = SessionLocal()
        try:
            app_rec = db.query(Application).filter(Application.id == application_id).first()
            if not app_rec:
                return {"success": False, "message": "Application record not found."}

            job = app_rec.job_posting
            # Mark authorized
            app_rec.status = ApplicationStatus.AUTHORIZED_TO_SUBMIT
            db.add(ApplicationEvent(
                application_id=app_rec.id,
                from_status="AWAITING_APPROVAL",
                to_status="AUTHORIZED_TO_SUBMIT",
                trigger_source="telegram_approval_button",
                message=f"Candidate approved application for {job.company_name}."
            ))
            db.commit()

            return {
                "success": True,
                "application_id": app_rec.id,
                "company_name": job.company_name,
                "title": job.title,
                "application_url": job.application_url,
                "message": f"✅ Approved application #{app_rec.id} for {job.company_name}."
            }
        finally:
            db.close()

    def handle_reject(self, application_id: int, reason: str = "Rejected by candidate in Telegram") -> Dict[str, Any]:
        """Candidate rejected staged application."""
        db = SessionLocal()
        try:
            app_rec = db.query(Application).filter(Application.id == application_id).first()
            if not app_rec:
                return {"success": False, "message": "Application record not found."}

            job = app_rec.job_posting
            app_rec.status = ApplicationStatus.REJECTED
            app_rec.failure_reason = reason
            db.add(ApplicationEvent(
                application_id=app_rec.id,
                from_status="AWAITING_APPROVAL",
                to_status="REJECTED",
                trigger_source="telegram_reject_button",
                message=f"Candidate rejected opportunity: {reason}"
            ))
            db.commit()

            return {
                "success": True,
                "application_id": app_rec.id,
                "company_name": job.company_name,
                "message": f"❌ Rejected application #{app_rec.id} for {job.company_name}."
            }
        finally:
            db.close()

approval_service = TelegramApprovalService()
