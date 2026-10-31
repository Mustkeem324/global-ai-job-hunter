from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.schema import JobPosting, Application, JobMatch
from app.core.state_machine import ApplicationStatus

router = APIRouter(prefix="/analytics", tags=["Analytics & KPIs"])

@router.get("/overview")
def get_analytics_overview(db: Session = Depends(get_db)):
    total_jobs = db.query(JobPosting).count()
    active_jobs = db.query(JobPosting).filter(JobPosting.status == "Active").count()
    high_match_jobs = db.query(JobMatch).filter(JobMatch.overall_score >= 85).count()
    
    total_apps = db.query(Application).count()
    submitted_confirmed = db.query(Application).filter(Application.status == ApplicationStatus.SUBMITTED_CONFIRMED).count()
    awaiting_approval = db.query(Application).filter(Application.status == ApplicationStatus.AWAITING_APPROVAL).count()
    interviews = db.query(Application).filter(Application.status == ApplicationStatus.INTERVIEW).count()
    offers = db.query(Application).filter(Application.status == ApplicationStatus.OFFER).count()
    failed = db.query(Application).filter(Application.status == ApplicationStatus.FAILED).count()
    
    response_rate = round((interviews / max(1, submitted_confirmed)) * 100, 1)

    return {
        "total_jobs_discovered": total_jobs,
        "active_jobs": active_jobs,
        "high_match_jobs": high_match_jobs,
        "total_applications": total_apps,
        "submitted_confirmed": submitted_confirmed,
        "awaiting_approval": awaiting_approval,
        "interviews": interviews,
        "offers": offers,
        "failed_submissions": failed,
        "response_rate_percent": response_rate
    }

@router.get("/categories")
def get_categories_breakdown(db: Session = Depends(get_db)):
    cats = db.query(JobPosting.category, func.count(JobPosting.id)).group_by(JobPosting.category).all()
    return [{"category": c[0], "count": c[1]} for c in cats]
