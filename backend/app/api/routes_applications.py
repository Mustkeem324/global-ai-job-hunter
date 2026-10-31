import datetime
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.core.database import get_db
from app.models.schema import Application, JobPosting, SubmissionEvidence, ApplicationEvent, CandidateProfile, AutomationPolicy
from app.core.state_machine import ApplicationStatus, ApplicationMode, ApplicationStateMachine
from app.services.application_executor import application_executor
from app.services.telegram_service import telegram_service

router = APIRouter(prefix="/applications", tags=["Applications & State Machine"])

@router.get("/")
def get_applications(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Application).join(JobPosting)
    if status:
        query = query.filter(Application.status == status)
    apps = query.order_by(Application.id.desc()).all()
    
    results = []
    for a in apps:
        job = a.job_posting
        evidence = a.evidence
        results.append({
            "id": a.id,
            "job_id": job.id,
            "company_name": job.company_name,
            "title": job.title,
            "compensation": job.compensation_text,
            "application_url": job.application_url,
            "mode": a.mode,
            "status": a.status,
            "match_score": a.match_score,
            "tailored_headline": a.tailored_headline,
            "cover_letter_preview": a.cover_letter[:180] + "..." if a.cover_letter else "",
            "confirmation_id": evidence.confirmation_id if evidence else None,
            "applied_at": a.applied_at.isoformat() if a.applied_at else None,
            "created_at": a.created_at.isoformat()
        })
    return {"total": len(results), "applications": results}

@router.get("/{app_id}")
def get_application_detail(app_id: int, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    job = app.job_posting
    evidence = app.evidence
    events = db.query(ApplicationEvent).filter(ApplicationEvent.application_id == app.id).order_by(ApplicationEvent.id.desc()).all()
    
    return {
        "id": app.id,
        "job": {
            "id": job.id,
            "company_name": job.company_name,
            "title": job.title,
            "compensation": job.compensation_text,
            "location": job.location,
            "country_eligibility": job.country_eligibility,
            "application_url": job.application_url,
            "description": job.description
        },
        "mode": app.mode,
        "status": app.status,
        "match_score": app.match_score,
        "tailored_headline": app.tailored_headline,
        "tailored_summary": app.tailored_summary,
        "cover_letter": app.cover_letter,
        "answers_payload": app.answers_payload,
        "applied_at": app.applied_at.isoformat() if app.applied_at else None,
        "evidence": {
            "confirmation_id": evidence.confirmation_id,
            "confirmation_method": evidence.confirmation_method,
            "raw_evidence_text": evidence.raw_evidence_text,
            "timestamp": evidence.timestamp.isoformat()
        } if evidence else None,
        "events": [
            {
                "from_status": ev.from_status,
                "to_status": ev.to_status,
                "trigger_source": ev.trigger_source,
                "message": ev.message,
                "timestamp": ev.timestamp.isoformat()
            } for ev in events
        ]
    }

@router.post("/{app_id}/approve")
def approve_application(app_id: int, db: Session = Depends(get_db)):
    """Approve application in queue and transition state machine."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    if app.status != ApplicationStatus.AWAITING_APPROVAL:
        raise HTTPException(status_code=400, detail=f"Application cannot be approved from status {app.status}")

    job = app.job_posting
    profile = db.query(CandidateProfile).first()
    
    # State transition: AWAITING_APPROVAL -> SUBMITTING
    ApplicationStateMachine.validate_transition(app.status, ApplicationStatus.SUBMITTING)
    prev_status = app.status
    app.status = ApplicationStatus.SUBMITTING
    
    event = ApplicationEvent(
        application_id=app.id,
        from_status=prev_status.value,
        to_status=ApplicationStatus.SUBMITTING.value,
        trigger_source="user_approval",
        message="User approved application in dashboard queue."
    )
    db.add(event)
    db.flush()

    # Execute submission via executor
    job_dict = {
        "title": job.title,
        "company_name": job.company_name,
        "location": job.location,
        "application_url": job.application_url,
        "adapter_key": job.source.adapter_key if job.source else "local_catalog"
    }
    
    sub_res = application_executor.submit_application(
        application_id=app.id,
        job_dict=job_dict,
        candidate_dict={},
        documents_dict={"cover_letter": app.cover_letter},
        mode=app.mode
    )

    next_status = sub_res["status"]
    ApplicationStateMachine.validate_transition(app.status, next_status)
    app.status = next_status
    app.applied_at = datetime.datetime.now(datetime.timezone.utc)

    # If authoritative confirmation returned
    if sub_res.get("evidence"):
        ev_data = sub_res["evidence"]
        evidence = SubmissionEvidence(
            application_id=app.id,
            confirmation_id=ev_data["confirmation_id"],
            confirmation_method=ev_data["confirmation_method"],
            raw_evidence_text=ev_data["raw_evidence_text"],
            verified=ev_data["verified"]
        )
        db.add(evidence)
        
        # Deliver Telegram confirmation alert
        telegram_service.notify_application_confirmed(
            app.id, 
            job_dict, 
            ev_data["confirmation_id"], 
            app.applied_at.strftime("%d %b %Y, %I:%M %p IST")
        )

    event2 = ApplicationEvent(
        application_id=app.id,
        from_status=ApplicationStatus.SUBMITTING.value,
        to_status=next_status.value,
        trigger_source="application_executor",
        message=sub_res["message"]
    )
    db.add(event2)
    db.commit()

    return {
        "status": "success",
        "application_id": app.id,
        "current_status": app.status,
        "message": sub_res["message"]
    }

@router.post("/{app_id}/reject")
def reject_application(app_id: int, reason: str = Body("Rejected by candidate", embed=True), db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    prev = app.status
    app.status = ApplicationStatus.REJECTED
    event = ApplicationEvent(
        application_id=app.id,
        from_status=prev.value,
        to_status=ApplicationStatus.REJECTED.value,
        trigger_source="user_reject",
        message=f"Rejected: {reason}"
    )
    db.add(event)
    db.commit()
    return {"status": "success", "application_id": app.id, "current_status": app.status}

@router.post("/{app_id}/mark-submitted")
def mark_assisted_submitted(
    app_id: int, 
    confirmation_notes: str = Body("Submitted via official portal", embed=True),
    db: Session = Depends(get_db)
):
    """Mark assisted application as submitted after user completes form."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    prev = app.status
    app.status = ApplicationStatus.SUBMITTED_CONFIRMED
    app.applied_at = datetime.datetime.now(datetime.timezone.utc)
    
    evidence = SubmissionEvidence(
        application_id=app.id,
        confirmation_id=f"MANUAL-{app.id}",
        confirmation_method="user_manual_verification",
        raw_evidence_text=confirmation_notes,
        verified=True
    )
    db.add(evidence)
    
    event = ApplicationEvent(
        application_id=app.id,
        from_status=prev.value,
        to_status=ApplicationStatus.SUBMITTED_CONFIRMED.value,
        trigger_source="user_assisted_confirmation",
        message=f"Confirmed by user: {confirmation_notes}"
    )
    db.add(event)
    db.commit()
    return {"status": "success", "application_id": app.id, "current_status": app.status}

@router.put("/{app_id}/documents")
def update_application_documents(
    app_id: int,
    cover_letter: Optional[str] = Body(None),
    tailored_headline: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if cover_letter:
        app.cover_letter = cover_letter
    if tailored_headline:
        app.tailored_headline = tailored_headline
    db.commit()
    return {"status": "success", "message": "Documents updated successfully."}
