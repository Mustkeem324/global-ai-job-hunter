from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schema import ApplicationEvent, AuditLog

router = APIRouter(prefix="/audit", tags=["Security & Audit Logs"])

@router.get("/logs")
def get_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    events = db.query(ApplicationEvent).order_by(ApplicationEvent.id.desc()).limit(limit).all()
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    
    return {
        "events": [
            {
                "id": e.id,
                "application_id": e.application_id,
                "from_status": e.from_status,
                "to_status": e.to_status,
                "trigger": e.trigger_source,
                "message": e.message,
                "timestamp": e.timestamp.isoformat()
            } for e in events
        ],
        "audit_logs": [
            {
                "id": l.id,
                "event_type": l.event_type,
                "actor": l.actor,
                "target": l.target,
                "details": l.details,
                "timestamp": l.created_at.isoformat()
            } for l in logs
        ]
    }
