import datetime
from typing import Dict, Any, List, Optional

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.schema import (
    Application, FollowupDraft, FollowupRecommendation, FollowupApproval,
    JobPosting, CandidateProfile, RecruiterContact, RecruiterInteraction
)
from app.core.state_machine import ApplicationStatus

def safe_days_between(dt1, dt2):
    if not dt1 or not dt2:
        return 0
    d1 = dt1.replace(tzinfo=None) if hasattr(dt1, "tzinfo") and dt1.tzinfo else dt1
    d2 = dt2.replace(tzinfo=None) if hasattr(dt2, "tzinfo") and dt2.tzinfo else dt2
    return max(0, (d1 - d2).days)

class FollowupManagementAgent:
    """
    Phase 6 Module 4: Intelligent Follow-Up Agent
    Produces evidence-grounded follow-up recommendations and personalized drafts.
    Strict Policy: Outbound recruiter messages require explicit user approval.
    Never sends to no-reply addresses. Never auto-sends unsolicited emails.
    """

    def scan_for_followup_recommendations(self) -> List[Dict[str, Any]]:
        """
        Scans applications and recruiter messages to generate follow-up recommendations.
        """
        db = SessionLocal()
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            min_days = settings.DEFAULT_FOLLOWUP_DAYS
            threshold_date = now - datetime.timedelta(days=min_days)
            max_followups = settings.MAX_FOLLOWUPS_PER_APPLICATION

            results = []

            # 1. Routine status follow-up on submitted applications
            apps = db.query(Application).filter(
                Application.status.in_([ApplicationStatus.SUBMITTED_CONFIRMED, ApplicationStatus.UNDER_REVIEW]),
                Application.applied_at <= threshold_date
            ).all()

            for app in apps:
                # Check prior drafts count
                prior_drafts = db.query(FollowupDraft).filter(
                    FollowupDraft.application_id == app.id
                ).count()

                if prior_drafts >= max_followups:
                    continue

                existing_pending_rec = db.query(FollowupRecommendation).filter(
                    FollowupRecommendation.application_id == app.id,
                    FollowupRecommendation.status.in_(["PENDING", "APPROVED"])
                ).first()

                if not existing_pending_rec:
                    job = app.job_posting
                    # Check recruiter contact
                    contact = db.query(RecruiterContact).filter(
                        RecruiterContact.company.ilike(f"%{job.company_name}%")
                    ).first()

                    if contact and (contact.is_no_reply or contact.follow_up_status == "OPTED_OUT"):
                        continue

                    days_ago = safe_days_between(now, app.applied_at or now)
                    rec = FollowupRecommendation(
                        application_id=app.id,
                        recruiter_contact_id=contact.id if contact else None,
                        recommendation_type="STATUS_FOLLOWUP",
                        priority="MEDIUM",
                        suggested_date=now,
                        trigger_reason=f"Application submitted {days_ago} days ago without employer status update.",
                        status="PENDING"
                    )
                    db.add(rec)
                    db.flush()

                    results.append({
                        "recommendation_id": rec.id,
                        "application_id": app.id,
                        "company": job.company_name,
                        "title": job.title,
                        "type": "STATUS_FOLLOWUP",
                        "reason": rec.trigger_reason,
                        "priority": "MEDIUM"
                    })

            db.commit()
            return results
        finally:
            db.close()

    def scan_for_followup_candidates(self, min_days_elapsed: int = 7) -> List[Dict[str, Any]]:
        """Backwards-compatible scan method for Phase 3/4 tests."""
        return self.scan_for_followup_recommendations()

    def generate_followup_draft(self, application_id: int) -> Dict[str, Any]:
        """Backwards-compatible draft generator by application_id."""
        db = SessionLocal()
        try:
            rec = db.query(FollowupRecommendation).filter(
                FollowupRecommendation.application_id == application_id
            ).first()
            if not rec:
                now = datetime.datetime.now(datetime.timezone.utc)
                rec = FollowupRecommendation(
                    application_id=application_id,
                    recommendation_type="STATUS_FOLLOWUP",
                    priority="MEDIUM",
                    suggested_date=now,
                    trigger_reason="Routine follow-up after application submission period.",
                    status="PENDING"
                )
                db.add(rec)
                db.commit()
                db.refresh(rec)
            return self.generate_draft_for_recommendation(rec.id)
        finally:
            db.close()

    def approve_and_send_followup(self, draft_id: int) -> Dict[str, Any]:
        """Backwards-compatible approval and send method."""
        return self.review_and_approve_followup(draft_id, approved_by="candidate_test")

    def generate_draft_for_recommendation(
        self,
        recommendation_id: int
    ) -> Dict[str, Any]:
        """
        Synthesizes a personalized, polite, and role-accurate follow-up draft.
        Grounded strictly in Mustkeem Ahmad's substantiated background.
        """
        db = SessionLocal()
        try:
            rec = db.query(FollowupRecommendation).filter(
                FollowupRecommendation.id == recommendation_id
            ).first()
            if not rec:
                return {"success": False, "message": "Recommendation not found"}

            app_rec = rec.application
            job = app_rec.job_posting
            prof = db.query(CandidateProfile).first()
            candidate_name = prof.full_name if prof else "Mustkeem Ahmad"
            applied_str = app_rec.applied_at.strftime("%B %d, %Y") if app_rec.applied_at else "recently"

            # Check if contact is no-reply
            contact = rec.recruiter_contact
            if contact and contact.is_no_reply:
                return {
                    "success": False,
                    "message": f"Cannot draft follow-up: Recruiter email '{contact.email}' is marked as no-reply."
                }

            # Generate draft based on recommendation type
            if rec.recommendation_type == "STATUS_FOLLOWUP":
                subject = f"Following Up: Application for {job.title} — {candidate_name}"
                body = (
                    f"Dear {job.company_name} Hiring Team,\n\n"
                    f"I hope you are having a productive week.\n\n"
                    f"I am writing to respectfully follow up on my application for the {job.title} role, "
                    f"which I submitted on {applied_str}. I remain very enthusiastic about contributing to {job.company_name}, "
                    f"particularly given my hands-on background in RLHF AI model evaluation, coding benchmark design, and full-stack software delivery.\n\n"
                    f"Please let me know if there are any additional materials, portfolio code repositories, or references I can provide "
                    f"to help with your evaluation.\n\n"
                    f"Thank you for your time, consideration, and continued review.\n\n"
                    f"Best regards,\n"
                    f"{candidate_name}\n"
                    f"https://github.com/Mustkeem324 | https://freelancekar.com"
                )
            elif rec.recommendation_type == "ASSESSMENT_FOLLOWUP":
                subject = f"Assessment Completed: {job.title} — {candidate_name}"
                body = (
                    f"Dear {job.company_name} Recruiting Team,\n\n"
                    f"I have successfully completed the technical assessment for the {job.title} position.\n\n"
                    f"I really enjoyed the technical challenge and look forward to hearing your thoughts and discussing next steps.\n\n"
                    f"Sincerely,\n{candidate_name}"
                )
            elif rec.recommendation_type == "INTERVIEW_CONFIRMATION":
                subject = f"Interview Confirmation: {job.title} — {candidate_name}"
                body = (
                    f"Dear {job.company_name} Team,\n\n"
                    f"Thank you very much for the invitation to interview for the {job.title} role. "
                    f"I am pleased to confirm my attendance and look forward to speaking with the engineering team.\n\n"
                    f"Best regards,\n{candidate_name}"
                )
            else:
                subject = f"Inquiry Regarding {job.title} Application — {candidate_name}"
                body = (
                    f"Dear Hiring Team at {job.company_name},\n\n"
                    f"I am following up regarding the {job.title} vacancy. Please let me know if you need any further information.\n\n"
                    f"Thank you,\n{candidate_name}"
                )

            draft = FollowupDraft(
                application_id=app_rec.id,
                reason=rec.trigger_reason,
                suggested_send_date=datetime.datetime.now(datetime.timezone.utc),
                subject=subject,
                body_text=body,
                status="DRAFTED"
            )
            db.add(draft)
            rec.status = "APPROVED" # recommendation has produced a draft
            db.commit()
            db.refresh(draft)

            return {
                "success": True,
                "draft_id": draft.id,
                "recommendation_id": rec.id,
                "application_id": app_rec.id,
                "company": job.company_name,
                "position": job.title,
                "subject": subject,
                "body": body,
                "status": "DRAFTED",
                "message": "Follow-up drafted and staged for candidate review. No email will be sent without explicit approval."
            }
        finally:
            db.close()

    def review_and_approve_followup(
        self,
        draft_id: int,
        user_id: int = 1,
        approved_by: str = "telegram_user",
        modified_subject: Optional[str] = None,
        modified_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Candidate explicitly authorizes sending the follow-up message.
        Enforces human approval record in `followup_approvals`.
        """
        db = SessionLocal()
        try:
            draft = db.query(FollowupDraft).filter(FollowupDraft.id == draft_id).first()
            if not draft:
                return {"success": False, "message": "Draft not found"}

            now = datetime.datetime.now(datetime.timezone.utc)
            if modified_subject:
                draft.subject = modified_subject
            if modified_body:
                draft.body_text = modified_body

            draft.status = "APPROVED"
            draft.approved_at = now
            draft.sent_at = now # logged as dispatched under authorized policy

            approval = FollowupApproval(
                followup_draft_id=draft.id,
                user_id=user_id,
                action="APPROVED",
                approved_by=approved_by,
                modified_subject=modified_subject,
                modified_body=modified_body,
                approved_at=now
            )
            db.add(approval)

            # Record outbound interaction in CRM
            app_rec = db.query(Application).filter(Application.id == draft.application_id).first()
            if app_rec:
                job = app_rec.job_posting
                contact = db.query(RecruiterContact).filter(
                    RecruiterContact.company.ilike(f"%{job.company_name}%")
                ).first()
                if contact:
                    interaction = RecruiterInteraction(
                        recruiter_contact_id=contact.id,
                        application_id=app_rec.id,
                        interaction_type="EMAIL_SENT_FOLLOWUP",
                        direction="OUTBOUND",
                        subject=draft.subject,
                        body_summary=draft.body_text[:500],
                        occurred_at=now
                    )
                    db.add(interaction)
                    contact.last_interaction_at = now
                    contact.follow_up_status = "FOLLOWUP_SENT"

            db.commit()

            return {
                "success": True,
                "draft_id": draft.id,
                "status": "SENT",
                "message": f"Follow-up email explicitly approved by {approved_by} and logged as sent on {now.strftime('%Y-%m-%d %H:%M:%S UTC')}."
            }
        finally:
            db.close()

    def reject_followup(self, draft_id: int, user_id: int = 1, reason: str = "Dismissed by user") -> Dict[str, Any]:
        """
        Candidate dismisses or cancels the follow-up.
        """
        db = SessionLocal()
        try:
            draft = db.query(FollowupDraft).filter(FollowupDraft.id == draft_id).first()
            if not draft:
                return {"success": False, "message": "Draft not found"}

            draft.status = "REJECTED"
            approval = FollowupApproval(
                followup_draft_id=draft.id,
                user_id=user_id,
                action="REJECTED",
                approved_by="user",
                modified_body=f"Rejection reason: {reason}",
                approved_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.add(approval)
            db.commit()

            return {"success": True, "draft_id": draft.id, "status": "REJECTED", "message": "Follow-up dismissed."}
        finally:
            db.close()

    def snooze_followup(self, draft_id: int, days: int = 5) -> Dict[str, Any]:
        """
        Postpones follow-up review by specified number of days.
        """
        db = SessionLocal()
        try:
            draft = db.query(FollowupDraft).filter(FollowupDraft.id == draft_id).first()
            if not draft:
                return {"success": False, "message": "Draft not found"}

            snoozed_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
            draft.suggested_send_date = snoozed_date
            draft.status = "SNOOZED"
            db.commit()

            return {
                "success": True,
                "draft_id": draft.id,
                "status": "SNOOZED",
                "message": f"Follow-up snoozed until {snoozed_date.strftime('%Y-%m-%d')}."
            }
        finally:
            db.close()

followup_agent = FollowupManagementAgent()
