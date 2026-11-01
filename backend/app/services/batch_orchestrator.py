import uuid
import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.schema import (
    ApplicationBatch, ApplicationBatchItem, BatchAuthorization,
    BatchProgressSnapshot, BatchExecutionEvent, Application, JobPosting,
    SubmissionEvidence, CandidateProfile, User
)
from app.core.state_machine import ApplicationStatus, ApplicationCapability, ApplicationMode
from app.services.resume_tailoring import resume_tailoring_service
from app.services.auto_apply_engine import auto_apply_engine

class BatchApplicationOrchestrator:
    """
    Phase 5 Module 5, 7 & 10: One-Click Batch Apply Execution Orchestrator
    Manages state machine transitions, parallel execution, idempotency, and progress snapshots.
    """

    MAX_CONCURRENT_APPLICATIONS = 2
    MAX_DAILY_AUTO_APPLICATIONS = 10

    def __init__(self):
        self.paused_batches = set()
        self.stopped_batches = set()

    def get_batch(self, batch_identifier: str) -> Optional[ApplicationBatch]:
        db = SessionLocal()
        try:
            if batch_identifier.isdigit():
                return db.query(ApplicationBatch).filter(ApplicationBatch.id == int(batch_identifier)).first()
            return db.query(ApplicationBatch).filter(ApplicationBatch.batch_id == batch_identifier).first()
        finally:
            db.close()

    def authorize_and_start_batch(self, batch_id_or_code: str, telegram_user_id: str) -> Dict[str, Any]:
        """
        Authorizes the batch with a single confirmation and kicks off parallel execution.
        """
        db = SessionLocal()
        try:
            batch = None
            if str(batch_id_or_code).isdigit():
                batch = db.query(ApplicationBatch).filter(ApplicationBatch.id == int(batch_id_or_code)).first()
            if not batch:
                batch = db.query(ApplicationBatch).filter(ApplicationBatch.batch_id == str(batch_id_or_code)).first()

            if not batch:
                return {"success": False, "message": "Batch session not found"}

            if batch.status in ("COMPLETED", "COMPLETED_WITH_EXCEPTIONS", "CANCELLED"):
                return {"success": False, "message": f"Batch is already {batch.status}."}

            # Record BatchAuthorization
            auth = BatchAuthorization(
                batch_id=batch.id,
                authorized_by_telegram_id=str(telegram_user_id),
                policy_snapshot_json={
                    "min_match_score": settings.MIN_MATCH_SCORE,
                    "auto_apply_enabled": settings.AUTO_APPLY_ENABLED,
                    "max_concurrent": self.MAX_CONCURRENT_APPLICATIONS
                },
                items_count=batch.eligible_jobs
            )
            db.add(auth)

            batch.status = "RUNNING"
            db.add(BatchExecutionEvent(
                batch_id=batch.id,
                event_type="STARTED",
                message=f"Batch authorized by user {telegram_user_id}. Starting execution of {batch.eligible_jobs} eligible jobs."
            ))
            db.commit()
            db.refresh(batch)

            # Process items
            result = self.process_batch_items(batch.id)
            return {
                "success": True,
                "batch_id": batch.batch_id,
                "status": result["status"],
                "submitted_count": result["submitted_count"],
                "manual_count": result["manual_count"],
                "message": result["message"]
            }
        finally:
            db.close()

    def process_batch_items(self, batch_pk: int) -> Dict[str, Any]:
        """
        Iterates through batch items, tailoring documents and submitting authorized jobs.
        """
        db = SessionLocal()
        try:
            batch = db.query(ApplicationBatch).filter(ApplicationBatch.id == batch_pk).first()
            if not batch:
                return {"status": "FAILED", "submitted_count": 0, "manual_count": 0, "message": "Batch not found"}

            items = db.query(ApplicationBatchItem).filter(
                ApplicationBatchItem.batch_id == batch.id,
                ApplicationBatchItem.status == "PREFLIGHT_PASSED"
            ).all()

            submitted = 0
            manual = 0
            failed = 0

            for item in items:
                # Check pause/stop
                if batch.batch_id in self.paused_batches or batch.status == "PAUSED":
                    batch.status = "PAUSED"
                    db.commit()
                    return {"status": "PAUSED", "submitted_count": submitted, "manual_count": manual, "message": "Batch paused."}

                if batch.batch_id in self.stopped_batches or batch.status == "CANCELLED":
                    batch.status = "CANCELLED"
                    db.commit()
                    return {"status": "CANCELLED", "submitted_count": submitted, "manual_count": manual, "message": "Batch stopped."}

                job = item.job
                job_dict = {
                    "id": job.id,
                    "title": job.title,
                    "company_name": job.company_name,
                    "description": job.description,
                    "location": job.location,
                    "compensation_text": job.compensation_text,
                    "application_url": job.application_url,
                    "source_id": getattr(job, "source_id", "catalog")
                }

                # Step 1: Tailor documents for this specific vacancy
                tailored = resume_tailoring_service.tailor_resume(job_dict)

                # Step 2: Check submission capability
                if item.capability == ApplicationCapability.AUTHORIZED_API_SUBMISSION.value:
                    # Submit via authorized engine
                    apply_res = auto_apply_engine.process_one_click_apply(str(job.id), sender_id="bulk_agent")
                    if apply_res.get("success") and apply_res.get("action") == "SUBMITTED_CONFIRMED":
                        item.status = "SUBMITTED_CONFIRMED"
                        item.confirmation_receipt_id = apply_res.get("confirmation_id")
                        item.application_id = apply_res.get("application_id")
                        item.processed_at = datetime.datetime.now(datetime.timezone.utc)
                        submitted += 1
                    else:
                        item.status = "MANUAL_REVIEW_REQUIRED"
                        item.application_id = apply_res.get("application_id")
                        manual += 1
                else:
                    # External / Manual review required: stage prepared application
                    user = db.query(User).first()
                    app_rec = db.query(Application).filter(Application.job_id == job.id).first()
                    if not app_rec:
                        app_rec = Application(
                            job_id=job.id,
                            user_id=user.id if user else 1,
                            mode=ApplicationMode.MODE_B_APPROVAL,
                            status=ApplicationStatus.AWAITING_APPROVAL,
                            idempotency_key=f"batch-{batch.batch_id}-{job.id}-{uuid.uuid4().hex[:6]}",
                            match_score=item.match_score,
                            tailored_summary=tailored.tailored_summary,
                            cover_letter=tailored.cover_letter,
                            application_method="APPLICATION_PREPARED_MANUAL_SUBMISSION"
                        )
                        db.add(app_rec)
                        db.flush()

                    item.status = "MANUAL_REVIEW_REQUIRED"
                    item.application_id = app_rec.id
                    item.processed_at = datetime.datetime.now(datetime.timezone.utc)
                    manual += 1

            # Update batch state
            batch.submitted_count = submitted
            batch.manual_review_jobs = manual
            batch.completed_at = datetime.datetime.now(datetime.timezone.utc)
            batch.status = "COMPLETED" if failed == 0 else "COMPLETED_WITH_EXCEPTIONS"

            # Create progress snapshot
            db.add(BatchProgressSnapshot(
                batch_id=batch.id,
                status=batch.status,
                confirmed_count=submitted,
                processing_count=0,
                awaiting_count=0,
                failed_count=failed,
                manual_count=manual
            ))
            db.commit()

            return {
                "status": batch.status,
                "submitted_count": submitted,
                "manual_count": manual,
                "failed_count": failed,
                "message": f"Batch completed: {submitted} submitted & confirmed, {manual} prepared for manual review."
            }
        finally:
            db.close()

    def pause_batch(self, batch_id_or_code: str) -> Dict[str, Any]:
        self.paused_batches.add(str(batch_id_or_code))
        db = SessionLocal()
        try:
            batch = db.query(ApplicationBatch).filter(
                (ApplicationBatch.batch_id == str(batch_id_or_code)) | (ApplicationBatch.id == (int(batch_id_or_code) if str(batch_id_or_code).isdigit() else -1))
            ).first()
            if batch:
                batch.status = "PAUSED"
                db.commit()
                return {"success": True, "message": f"Batch {batch.batch_id} paused."}
            return {"success": False, "message": "Batch not found"}
        finally:
            db.close()

    def resume_batch(self, batch_id_or_code: str) -> Dict[str, Any]:
        if str(batch_id_or_code) in self.paused_batches:
            self.paused_batches.remove(str(batch_id_or_code))
        db = SessionLocal()
        try:
            batch = db.query(ApplicationBatch).filter(
                (ApplicationBatch.batch_id == str(batch_id_or_code)) | (ApplicationBatch.id == (int(batch_id_or_code) if str(batch_id_or_code).isdigit() else -1))
            ).first()
            if batch:
                batch.status = "RUNNING"
                db.commit()
                return {"success": True, "message": f"Batch {batch.batch_id} resumed."}
            return {"success": False, "message": "Batch not found"}
        finally:
            db.close()

    def stop_batch(self, batch_id_or_code: str) -> Dict[str, Any]:
        self.stopped_batches.add(str(batch_id_or_code))
        db = SessionLocal()
        try:
            batch = db.query(ApplicationBatch).filter(
                (ApplicationBatch.batch_id == str(batch_id_or_code)) | (ApplicationBatch.id == (int(batch_id_or_code) if str(batch_id_or_code).isdigit() else -1))
            ).first()
            if batch:
                batch.status = "CANCELLED"
                db.commit()
                return {"success": True, "message": f"Batch {batch.batch_id} stopped and cancelled."}
            return {"success": False, "message": "Batch not found"}
        finally:
            db.close()

batch_orchestrator = BatchApplicationOrchestrator()
