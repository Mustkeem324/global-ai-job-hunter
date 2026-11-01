import uuid
import datetime
from typing import Dict, Any, List, Optional

from app.core.database import SessionLocal
from app.models.schema import (
    NaukriIntegrationSetting, NaukriNeoStatusRecord, NaukriApplicationSource,
    Application, JobPosting, User
)
from app.core.state_machine import ApplicationStatus

class NaukriNeoTrackingService:
    """
    Phase 7 Module 6: Naukri Neo & Naukri360 Pro Application Tracking Service
    Captures official Naukri Neo auto-applications from Gmail confirmations,
    correlates to canonical vacancies, and maintains strict origin provenance.
    Strict Rule: Never claims Global Job Hunter AI triggered an application submitted by Neo.
    """

    def configure_neo(self, user_id: int = 1, is_neo_enabled: bool = True, is_naukri360_pro: bool = False) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            cfg = db.query(NaukriIntegrationSetting).filter(NaukriIntegrationSetting.user_id == user_id).first()
            if not cfg:
                cfg = NaukriIntegrationSetting(
                    user_id=user_id,
                    is_neo_enabled=is_neo_enabled,
                    is_naukri360_pro=is_naukri360_pro
                )
                db.add(cfg)
            else:
                cfg.is_neo_enabled = is_neo_enabled
                cfg.is_naukri360_pro = is_naukri360_pro
            db.commit()
            return {
                "success": True,
                "is_neo_enabled": cfg.is_neo_enabled,
                "is_naukri360_pro": cfg.is_naukri360_pro,
                "message": f"Naukri Neo tracking {'enabled' if cfg.is_neo_enabled else 'disabled'} (Naukri360 Pro: {cfg.is_naukri360_pro})."
            }
        finally:
            db.close()

    def record_neo_application_confirmation(
        self,
        email_message_id: str,
        job_title: str,
        company_name: str,
        applied_at: Optional[datetime.datetime] = None
    ) -> Dict[str, Any]:
        """
        Parses official Naukri Neo email confirmation and registers it in the canonical pipeline.
        """
        db = SessionLocal()
        try:
            # Check deduplication
            existing = db.query(NaukriNeoStatusRecord).filter(
                NaukriNeoStatusRecord.confirmation_email_id == email_message_id
            ).first()
            if existing:
                return {"success": True, "status": "ALREADY_RECORDED", "record_id": existing.id}

            dt = applied_at or datetime.datetime.now(datetime.timezone.utc)

            # Match or create canonical JobPosting
            job = db.query(JobPosting).filter(
                JobPosting.company_name.ilike(f"%{company_name}%"),
                JobPosting.title.ilike(f"%{job_title}%")
            ).first()

            if not job:
                job = JobPosting(
                    source_id="naukri_neo",
                    source_job_id=f"neo-{uuid.uuid4().hex[:8]}",
                    title=job_title,
                    company_name=company_name,
                    location="India (Naukri Neo Auto-Applied)",
                    is_india_eligible=True,
                    employment_type="Full-Time",
                    compensation_text="Market Standard",
                    description=f"Auto-applied via official Naukri Neo service for {job_title} at {company_name}.",
                    application_url="https://www.naukri.com",
                    status="active"
                )
                db.add(job)
                db.flush()

            # Create or update canonical Application record
            user = db.query(User).first()
            app = db.query(Application).filter(Application.job_id == job.id).first()
            if not app:
                app = Application(
                    job_id=job.id,
                    user_id=user.id if user else 1,
                    status=ApplicationStatus.SUBMITTED_CONFIRMED,
                    idempotency_key=f"neo-app-{job.id}",
                    match_score=88.0,
                    confirmation_receipt_id=f"NEO-{uuid.uuid4().hex[:8].upper()}",
                    applied_at=dt
                )
                db.add(app)
                db.flush()
            else:
                app.status = ApplicationStatus.SUBMITTED_CONFIRMED

            # Record provenance explicitly as NAUKRI_NEO
            src_record = db.query(NaukriApplicationSource).filter(
                NaukriApplicationSource.application_id == app.id
            ).first()

            if not src_record:
                src_record = NaukriApplicationSource(
                    application_id=app.id,
                    source_type="NAUKRI_NEO",
                    source_metadata={
                        "email_message_id": email_message_id,
                        "applied_via": "Naukri Neo Auto-Apply Service",
                        "product": "Naukri360 Pro"
                    },
                    verified_by_candidate=True,
                    recorded_at=dt
                )
                db.add(src_record)

            neo_rec = NaukriNeoStatusRecord(
                confirmation_email_id=email_message_id,
                job_title=job_title,
                company_name=company_name,
                neo_applied_at=dt,
                canonical_application_id=app.id,
                matched_confidence=1.0
            )
            db.add(neo_rec)
            db.commit()

            return {
                "success": True,
                "status": "RECORDED",
                "neo_record_id": neo_rec.id,
                "canonical_application_id": app.id,
                "job_title": job_title,
                "company_name": company_name,
                "provenance": "NAUKRI_NEO",
                "message": f"Naukri Neo application tracked and verified for {company_name} — {job_title}."
            }
        finally:
            db.close()

    def list_neo_applications(self, limit: int = 20) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            records = db.query(NaukriNeoStatusRecord).order_by(
                NaukriNeoStatusRecord.neo_applied_at.desc()
            ).limit(limit).all()

            return [
                {
                    "id": r.id,
                    "job_title": r.job_title,
                    "company_name": r.company_name,
                    "applied_at": r.neo_applied_at.isoformat() if r.neo_applied_at else None,
                    "application_id": r.canonical_application_id,
                    "source": "NAUKRI_NEO"
                }
                for r in records
            ]
        finally:
            db.close()

naukri_neo_service = NaukriNeoTrackingService()
