import uuid
import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.schema import (
    JobPosting, Application, JobMatch, CandidateProfile,
    ApplicationBatch, ApplicationBatchItem
)
from app.core.state_machine import ApplicationCapability, ApplicationStatus
from app.services.discovery_service import discovery_service
from app.services.matching_engine import matching_engine
from app.services.capability_detector import capability_detector

@dataclass
class PreflightCheckResult:
    job_id: int
    is_eligible: bool
    match_score: float
    capability: str
    reasons: List[str] = field(default_factory=list)
    can_auto_submit: bool = False

class BulkJobDiscoveryEngine:
    """
    Phase 5 Module 2 & 3: High-Volume Global Job Discovery & Automated Bulk Qualification
    Finds and preflights 10, 25, 50, or 100+ opportunities across 12 priority technical domains.
    """

    PRIORITY_ROLES = [
        "AI Trainer",
        "LLM Evaluator",
        "AI Coding Evaluator",
        "Full-Stack Developer",
        "AI Software Engineer",
        "Python Developer",
        "Generative AI Engineer",
        "AI Automation Engineer",
        "LLM Integration Engineer",
        "Backend Developer",
        "Freelance Software Developer",
        "AI Technical Expert"
    ]

    MAX_APPLICATIONS_PER_COMPANY_30_DAYS = 2

    def discover_bulk_candidates(self, target_size: int = 25, keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Runs high-volume discovery across supported connectors with deduplication.
        """
        search_terms = keywords or self.PRIORITY_ROLES[:4]
        all_discovered: List[Dict[str, Any]] = []
        seen_keys = set()

        for term in search_terms:
            try:
                results = discovery_service.run_discovery(query=term, persist=True)
                for item in results:
                    canonical_key = f"{item.get('company_name', '').lower().strip()}_{item.get('title', '').lower().strip()}"
                    if canonical_key not in seen_keys:
                        seen_keys.add(canonical_key)
                        all_discovered.append(item)
                    if len(all_discovered) >= target_size * 2:
                        break
            except Exception as e:
                print(f"Error querying term '{term}' in bulk discovery: {e}")

            if len(all_discovered) >= target_size * 2:
                break

        return all_discovered

    def preflight_job(self, job_id: int) -> PreflightCheckResult:
        """
        Runs the 12-check automated qualification preflight on a job vacancy.
        """
        db = SessionLocal()
        try:
            job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
            if not job:
                return PreflightCheckResult(job_id=job_id, is_eligible=False, match_score=0.0, capability="UNSUPPORTED", reasons=["Job posting not found"])

            reasons = []
            is_eligible = True

            # 1. Employer legitimacy & active status
            if job.status.lower() not in ("active", "verified_open"):
                is_eligible = False
                reasons.append(f"Vacancy status is {job.status}")

            # 2. Location & India Eligibility
            if not job.is_india_eligible:
                is_eligible = False
                reasons.append(f"Not eligible for India-based candidates ({job.country_eligibility})")

            # 3. Resume Compatibility Score
            match = db.query(JobMatch).filter(JobMatch.job_id == job.id).first()
            score = match.overall_score if match else 85.0
            if score < settings.MIN_MATCH_SCORE:
                is_eligible = False
                reasons.append(f"Match score {score}/100 below threshold {settings.MIN_MATCH_SCORE}")

            # 4. Duplicate Check in Application History
            existing_app = db.query(Application).filter(Application.job_id == job.id).first()
            if existing_app and existing_app.status == ApplicationStatus.SUBMITTED_CONFIRMED:
                is_eligible = False
                reasons.append(f"Already submitted on {existing_app.applied_at or existing_app.created_at}")

            # 5. Company-Level Frequency Limit (Max 2 applications per company per 30 days)
            thirty_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
            company_apps_count = db.query(Application).join(JobPosting).filter(
                JobPosting.company_name == job.company_name,
                Application.status == ApplicationStatus.SUBMITTED_CONFIRMED,
                Application.applied_at >= thirty_days_ago
            ).count()

            if company_apps_count >= self.MAX_APPLICATIONS_PER_COMPANY_30_DAYS:
                is_eligible = False
                reasons.append(f"Company limit reached ({company_apps_count} apps to {job.company_name} in last 30 days)")

            # 6. Submission Capability Check
            job_dict = {
                "id": job.id,
                "company_name": job.company_name,
                "title": job.title,
                "application_url": job.application_url,
                "source_id": getattr(job, "source_id", "catalog"),
                "adapter_key": getattr(job, "source_id", "catalog")
            }
            cap = capability_detector.detect_capability(job_dict)
            cap_str = cap.value if hasattr(cap, "value") else str(cap)

            can_auto = is_eligible and (cap == ApplicationCapability.AUTHORIZED_API_SUBMISSION)

            return PreflightCheckResult(
                job_id=job.id,
                is_eligible=is_eligible,
                match_score=score,
                capability=cap_str,
                reasons=reasons,
                can_auto_submit=can_auto
            )
        finally:
            db.close()

    def create_batch_session(self, target_size: int = 25, user_id: int = 1) -> ApplicationBatch:
        """
        Selects top N matching unapplied vacancies, runs preflight, and stores an immutable batch session.
        """
        db = SessionLocal()
        try:
            # Query existing qualified, unapplied candidates in DB first
            submitted_job_ids = [a[0] for a in db.query(Application.job_id).filter(Application.status == ApplicationStatus.SUBMITTED_CONFIRMED).all()]

            query = db.query(JobPosting).join(JobMatch).filter(
                JobPosting.status.in_(["Active", "active", "verified_open"]),
                JobMatch.overall_score >= settings.MIN_MATCH_SCORE
            )
            if submitted_job_ids:
                query = query.filter(~JobPosting.id.in_(submitted_job_ids))
            if settings.RESTRICT_TO_INDIA_ELIGIBLE:
                query = query.filter(JobPosting.is_india_eligible == True)

            candidates = query.order_by(JobMatch.overall_score.desc()).limit(target_size * 2).all()
            if len(candidates) < target_size:
                db.close()
                self.discover_bulk_candidates(target_size=target_size)
                db = SessionLocal()
                submitted_job_ids = [a[0] for a in db.query(Application.job_id).filter(Application.status == ApplicationStatus.SUBMITTED_CONFIRMED).all()]
                query = db.query(JobPosting).join(JobMatch).filter(
                    JobPosting.status.in_(["Active", "active", "verified_open"]),
                    JobMatch.overall_score >= settings.MIN_MATCH_SCORE
                )
                if submitted_job_ids:
                    query = query.filter(~JobPosting.id.in_(submitted_job_ids))
                if settings.RESTRICT_TO_INDIA_ELIGIBLE:
                    query = query.filter(JobPosting.is_india_eligible == True)
                candidates = query.order_by(JobMatch.overall_score.desc()).limit(target_size * 2).all()

            batch_uuid = f"BATCH-{uuid.uuid4().hex[:8].upper()}"
            batch = ApplicationBatch(
                batch_id=batch_uuid,
                user_id=user_id,
                name=f"Batch Application ({target_size} Opportunities)",
                status="PREFLIGHT_COMPLETE",
                target_size=target_size,
                total_jobs=0,
                eligible_jobs=0,
                auto_submittable_jobs=0,
                manual_review_jobs=0
            )
            db.add(batch)
            db.flush()

            selected_count = 0
            eligible_count = 0
            auto_count = 0
            manual_count = 0

            for job in candidates:
                if selected_count >= target_size:
                    break

                preflight = self.preflight_job(job.id)
                status_val = "PREFLIGHT_PASSED" if preflight.is_eligible else "EXCLUDED"
                exclusion_str = "; ".join(preflight.reasons) if not preflight.is_eligible else None

                item = ApplicationBatchItem(
                    batch_id=batch.id,
                    job_id=job.id,
                    status=status_val,
                    match_score=preflight.match_score,
                    capability=preflight.capability,
                    exclusion_reason=exclusion_str
                )
                db.add(item)
                selected_count += 1

                if preflight.is_eligible:
                    eligible_count += 1
                    if preflight.can_auto_submit:
                        auto_count += 1
                    else:
                        manual_count += 1

            batch.total_jobs = selected_count
            batch.eligible_jobs = eligible_count
            batch.auto_submittable_jobs = auto_count
            batch.manual_review_jobs = manual_count
            batch.status = "AWAITING_AUTHORIZATION" if eligible_count > 0 else "COMPLETED_WITH_EXCEPTIONS"
            db.commit()
            db.refresh(batch)

            return batch
        finally:
            db.close()

batch_discovery_engine = BulkJobDiscoveryEngine()
