from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.models.schema import ApplicationBatch, ApplicationBatchItem
from app.services.batch_discovery_engine import batch_discovery_engine
from app.services.batch_orchestrator import batch_orchestrator

router = APIRouter(prefix="/batches", tags=["Bulk Job Application Engine"])

@router.get("/")
def list_batches(db: Session = Depends(get_db)):
    batches = db.query(ApplicationBatch).order_by(ApplicationBatch.id.desc()).all()
    return [
        {
            "id": b.id,
            "batch_id": b.batch_id,
            "name": b.name,
            "status": b.status,
            "target_size": b.target_size,
            "total_jobs": b.total_jobs,
            "eligible_jobs": b.eligible_jobs,
            "auto_submittable_jobs": b.auto_submittable_jobs,
            "manual_review_jobs": b.manual_review_jobs,
            "submitted_count": b.submitted_count,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "completed_at": b.completed_at.isoformat() if b.completed_at else None
        } for b in batches
    ]

@router.post("/create")
def create_batch(target_size: int = Body(25, embed=True), db: Session = Depends(get_db)):
    batch = batch_discovery_engine.create_batch_session(target_size=target_size)
    return {
        "success": True,
        "batch_id": batch.batch_id,
        "name": batch.name,
        "target_size": batch.target_size,
        "total_jobs": batch.total_jobs,
        "eligible_jobs": batch.eligible_jobs,
        "auto_submittable_jobs": batch.auto_submittable_jobs,
        "manual_review_jobs": batch.manual_review_jobs,
        "status": batch.status
    }

@router.get("/{batch_id}")
def get_batch_detail(batch_id: str, db: Session = Depends(get_db)):
    batch = db.query(ApplicationBatch).filter(
        (ApplicationBatch.batch_id == batch_id) | (ApplicationBatch.id == (int(batch_id) if batch_id.isdigit() else -1))
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    items = db.query(ApplicationBatchItem).filter(ApplicationBatchItem.batch_id == batch.id).all()
    return {
        "id": batch.id,
        "batch_id": batch.batch_id,
        "name": batch.name,
        "status": batch.status,
        "target_size": batch.target_size,
        "total_jobs": batch.total_jobs,
        "eligible_jobs": batch.eligible_jobs,
        "auto_submittable_jobs": batch.auto_submittable_jobs,
        "manual_review_jobs": batch.manual_review_jobs,
        "submitted_count": batch.submitted_count,
        "items": [
            {
                "id": it.id,
                "job_id": it.job_id,
                "company_name": it.job.company_name,
                "title": it.job.title,
                "status": it.status,
                "match_score": it.match_score,
                "capability": it.capability,
                "receipt_id": it.confirmation_receipt_id,
                "application_id": it.application_id,
                "exclusion_reason": it.exclusion_reason
            } for it in items
        ]
    }

@router.post("/{batch_id}/apply")
def apply_batch(batch_id: str, user_id: str = Body("web_admin", embed=True)):
    res = batch_orchestrator.authorize_and_start_batch(batch_id, telegram_user_id=user_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/{batch_id}/pause")
def pause_batch(batch_id: str):
    res = batch_orchestrator.pause_batch(batch_id)
    return res

@router.post("/{batch_id}/resume")
def resume_batch(batch_id: str):
    res = batch_orchestrator.resume_batch(batch_id)
    return res

@router.post("/{batch_id}/stop")
def stop_batch(batch_id: str):
    res = batch_orchestrator.stop_batch(batch_id)
    return res
