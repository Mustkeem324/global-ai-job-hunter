from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from app.services.recruiter_crm_service import recruiter_crm
from app.services.followup_agent import followup_agent
from app.services.interview_intelligence_service import interview_intelligence_service
from app.services.recruiter_analytics_service import recruiter_analytics
from app.services.gmail_service import gmail_service

router = APIRouter(prefix="/recruiter", tags=["Recruiter Intelligence & Pipeline"])

class ProcessEmailRequest(BaseModel):
    message_id: str
    sender_email: str
    subject: str
    body: str
    thread_id: Optional[str] = None

class FollowupApprovalRequest(BaseModel):
    approved_by: Optional[str] = "web_ui"
    modified_subject: Optional[str] = None
    modified_body: Optional[str] = None

class RestrictionUpdateRequest(BaseModel):
    restrictions: str
    opt_out: bool = False

@router.get("/contacts")
def list_contacts(
    company: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50)
):
    contacts = recruiter_crm.list_contacts(company=company, follow_up_status=status, limit=limit)
    return {"contacts": contacts, "total": len(contacts)}

@router.get("/contacts/{contact_id}")
def get_contact_detail(contact_id: int):
    detail = recruiter_crm.get_contact_detail(contact_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Contact not found")
    return detail

@router.put("/contacts/{contact_id}/restrictions")
def update_contact_restrictions(contact_id: int, req: RestrictionUpdateRequest):
    res = recruiter_crm.update_communication_restrictions(contact_id, req.restrictions, req.opt_out)
    return res

@router.post("/process-email")
def process_email(req: ProcessEmailRequest):
    res = gmail_service.process_incoming_email(
        message_id=req.message_id,
        sender_email=req.sender_email,
        subject=req.subject,
        body=req.body,
        thread_id=req.thread_id
    )
    return res

@router.get("/followups")
def get_followups():
    recs = followup_agent.scan_for_followup_recommendations()
    return {"recommendations": recs, "count": len(recs)}

@router.post("/followups/{rec_id}/generate-draft")
def generate_draft(rec_id: int):
    res = followup_agent.generate_draft_for_recommendation(rec_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/followups/drafts/{draft_id}/approve")
def approve_draft(draft_id: int, req: FollowupApprovalRequest):
    res = followup_agent.review_and_approve_followup(
        draft_id=draft_id,
        approved_by=req.approved_by or "web_ui",
        modified_subject=req.modified_subject,
        modified_body=req.modified_body
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/followups/drafts/{draft_id}/reject")
def reject_draft(draft_id: int, reason: str = Query("Dismissed by user")):
    res = followup_agent.reject_followup(draft_id=draft_id, reason=reason)
    return res

@router.post("/followups/drafts/{draft_id}/snooze")
def snooze_draft(draft_id: int, days: int = Query(5)):
    res = followup_agent.snooze_followup(draft_id=draft_id, days=days)
    return res

@router.get("/interviews")
def list_interviews(limit: int = Query(20)):
    intvs = interview_intelligence_service.list_upcoming_interviews(limit=limit)
    return {"interviews": intvs, "count": len(intvs)}

@router.post("/interviews/{interview_id}/calendar-sync")
def sync_calendar(interview_id: int):
    res = interview_intelligence_service.stage_google_calendar_event(interview_id)
    return res

@router.get("/interviews/{application_id}/prep")
def get_interview_prep(application_id: int, mode: str = Query("technical_qa")):
    res = interview_intelligence_service.generate_interview_preparation(application_id, mode)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("message"))
    return res

@router.get("/pipeline")
def get_pipeline():
    metrics = recruiter_analytics.calculate_funnel_metrics()
    return metrics

@router.get("/recommendations")
def get_recommendations():
    recs = recruiter_analytics.generate_search_optimization_recommendations()
    return {"recommendations": recs, "count": len(recs)}
