import uuid
import datetime
from typing import Dict, Any, List, Optional

from app.core.database import SessionLocal
from app.models.schema import RecruiterContact, RecruiterInteraction, Application, JobPosting

class RecruiterCRMService:
    """
    Phase 6 Module 3: Recruiter Relationship Database (CRM) Service
    Maintains verified recruiter contacts, interactions, follow-up states,
    and communication restrictions. Strictly forbids scraping or guessing emails.
    """

    def list_contacts(
        self,
        company: Optional[str] = None,
        follow_up_status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            query = db.query(RecruiterContact)
            if company:
                query = query.filter(RecruiterContact.company.ilike(f"%{company}%"))
            if follow_up_status:
                query = query.filter(RecruiterContact.follow_up_status == follow_up_status)

            contacts = query.order_by(RecruiterContact.last_interaction_at.desc()).limit(limit).all()
            return [
                {
                    "id": c.id,
                    "recruiter_id": c.recruiter_id,
                    "company": c.company,
                    "job_position": c.job_position,
                    "contact_name": c.contact_name,
                    "email": c.email,
                    "phone": c.phone,
                    "communication_channel": c.communication_channel,
                    "follow_up_status": c.follow_up_status,
                    "next_permitted_action": c.next_permitted_action,
                    "communication_restrictions": c.communication_restrictions,
                    "is_no_reply": c.is_no_reply,
                    "first_interaction_at": c.first_interaction_at.isoformat() if c.first_interaction_at else None,
                    "last_interaction_at": c.last_interaction_at.isoformat() if c.last_interaction_at else None,
                    "interaction_count": len(c.interactions)
                }
                for c in contacts
            ]
        finally:
            db.close()

    def get_contact_detail(self, contact_id: int) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            c = db.query(RecruiterContact).filter(RecruiterContact.id == contact_id).first()
            if not c:
                return None

            interactions = db.query(RecruiterInteraction).filter(
                RecruiterInteraction.recruiter_contact_id == c.id
            ).order_by(RecruiterInteraction.occurred_at.desc()).all()

            return {
                "id": c.id,
                "recruiter_id": c.recruiter_id,
                "company": c.company,
                "job_position": c.job_position,
                "contact_name": c.contact_name,
                "email": c.email,
                "phone": c.phone,
                "linkedin_url": c.linkedin_url,
                "communication_channel": c.communication_channel,
                "follow_up_status": c.follow_up_status,
                "next_permitted_action": c.next_permitted_action,
                "communication_restrictions": c.communication_restrictions,
                "is_no_reply": c.is_no_reply,
                "interactions": [
                    {
                        "id": i.id,
                        "type": i.interaction_type,
                        "direction": i.direction,
                        "subject": i.subject,
                        "summary": i.body_summary,
                        "message_id": i.message_id,
                        "occurred_at": i.occurred_at.isoformat() if i.occurred_at else None
                    }
                    for i in interactions
                ]
            }
        finally:
            db.close()

    def update_communication_restrictions(
        self,
        contact_id: int,
        restrictions: str,
        opt_out: bool = False
    ) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            c = db.query(RecruiterContact).filter(RecruiterContact.id == contact_id).first()
            if not c:
                return {"success": False, "message": "Contact not found"}

            c.communication_restrictions = restrictions
            if opt_out:
                c.follow_up_status = "OPTED_OUT"
                c.next_permitted_action = "DO_NOT_CONTACT"

            db.commit()
            return {"success": True, "message": f"Updated communication policies for {c.contact_name} ({c.company})."}
        finally:
            db.close()

recruiter_crm = RecruiterCRMService()
