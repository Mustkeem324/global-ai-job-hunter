from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schema import AutomationPolicy, User

router = APIRouter(prefix="/settings", tags=["Settings & Policies"])

@router.get("/")
def get_settings(db: Session = Depends(get_db)):
    user = db.query(User).first()
    policy = db.query(AutomationPolicy).first()
    if not policy:
        policy = AutomationPolicy(
            user_id=user.id if user else 1,
            auto_apply_enabled=False,
            approval_required=True,
            min_match_score=80,
            max_daily_applications=10,
            allowed_sources=["mock_ats", "greenhouse_sandbox"],
            cooling_off_days=30
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
    return {
        "auto_apply_enabled": policy.auto_apply_enabled,
        "approval_required": policy.approval_required,
        "min_match_score": policy.min_match_score,
        "max_daily_applications": policy.max_daily_applications,
        "allowed_sources": policy.allowed_sources,
        "cooling_off_days": policy.cooling_off_days
    }

@router.put("/")
def update_settings(
    auto_apply_enabled: bool = Body(...),
    approval_required: bool = Body(...),
    min_match_score: int = Body(...),
    max_daily_applications: int = Body(...),
    allowed_sources: list = Body(...),
    cooling_off_days: int = Body(30),
    db: Session = Depends(get_db)
):
    policy = db.query(AutomationPolicy).first()
    if not policy:
        user = db.query(User).first()
        policy = AutomationPolicy(user_id=user.id if user else 1)
        db.add(policy)
        
    policy.auto_apply_enabled = auto_apply_enabled
    policy.approval_required = approval_required
    policy.min_match_score = min_match_score
    policy.max_daily_applications = max_daily_applications
    policy.allowed_sources = allowed_sources
    policy.cooling_off_days = cooling_off_days
    
    db.commit()
    return {"status": "success", "message": "Automation settings updated successfully."}
