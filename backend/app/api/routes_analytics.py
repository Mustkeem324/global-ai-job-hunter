from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
import io
import csv
from app.core.database import get_db
from app.models.schema import JobPosting, Application, JobMatch, SourceHealth, CostUsage
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

@router.get("/source-health")
def get_source_health(db: Session = Depends(get_db)):
    sources = db.query(SourceHealth).all()
    return [
        {
            "source_name": s.source_name,
            "status": s.status,
            "error_count": s.error_count,
            "circuit_breaker_open": s.circuit_breaker_open,
            "avg_latency_ms": s.avg_latency_ms,
            "last_sync_at": s.last_sync_at.isoformat() if s.last_sync_at else None
        } for s in sources
    ]

@router.get("/cost")
def get_cost_usage(db: Session = Depends(get_db)):
    usage_rows = db.query(CostUsage).all()
    total_usd = sum(u.estimated_cost_usd for u in usage_rows)
    return {
        "total_cost_usd": round(total_usd, 4),
        "daily_budget_limit_usd": 5.0,
        "items": [
            {
                "service": u.service_name,
                "tokens_in": u.tokens_in,
                "tokens_out": u.tokens_out,
                "cost_usd": u.estimated_cost_usd,
                "date": u.date_str
            } for u in usage_rows
        ]
    }

@router.get("/export/csv")
def export_applications_csv(db: Session = Depends(get_db)):
    """Phase 4 Module 10: Downloadable CSV Export of Application History."""
    apps = db.query(Application).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Application ID", "Company Name", "Job Title", "Status",
        "Match Score", "Application Method", "Receipt ID", "Applied At", "Official URL"
    ])
    for a in apps:
        job = a.job_posting
        receipt = a.confirmation_receipt_id or (a.evidence.confirmation_id if a.evidence else "N/A")
        writer.writerow([
            a.id,
            job.company_name,
            job.title,
            a.status.value if hasattr(a.status, 'value') else a.status,
            a.match_score,
            a.application_method,
            receipt,
            a.applied_at.isoformat() if a.applied_at else "",
            job.application_url
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=applications_history.csv"}
    )
