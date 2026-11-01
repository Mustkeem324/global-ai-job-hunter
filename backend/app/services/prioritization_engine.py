import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.core.database import SessionLocal
from app.models.schema import JobPosting, JobMatch, JobPriority, UserFeedback, CandidateProfile

@dataclass
class PrioritizationScoreResult:
    job_id: int
    priority_tier: str # PRIORITY_A, PRIORITY_B, PRIORITY_C, PRIORITY_D
    priority_score: float # 0 to 100
    compatibility_score: float
    eligibility_score: float
    preference_score: float
    freshness_score: float
    effort_score: float
    feedback_adjustment: float
    explanation: Dict[str, Any]

class IntelligentOpportunityPrioritizer:
    """
    Phase 4 Module 4: Intelligent Opportunity Prioritization & User Feedback Engine
    Ranks discovered vacancies transparently across 6 multi-dimensional factors.
    """

    def calculate_priority(self, job_dict: Dict[str, Any], match_score: float = 85.0) -> PrioritizationScoreResult:
        job_id = job_dict.get("id", 1)
        db = SessionLocal()
        try:
            # 1. Compatibility Score (Max 30)
            compat_score = round(min(30.0, (match_score / 100.0) * 30.0), 2)

            # 2. Eligibility & Mandatory Criteria (Max 25)
            is_india_eligible = job_dict.get("is_india_eligible", True)
            elig_score = 25.0 if is_india_eligible else 0.0

            # 3. Compensation & User Preferences (Max 15)
            comp_text = str(job_dict.get("compensation_text", "")).lower()
            emp_type = str(job_dict.get("employment_type", "")).lower()
            pref_score = 10.0
            if any(sym in comp_text for sym in ("$", "€", "£", "₹", "usd", "eur")):
                pref_score += 3.0
            if "remote" in str(job_dict.get("location", "")).lower():
                pref_score += 2.0
            pref_score = min(15.0, pref_score)

            # 4. Job Freshness & Source Reliability (Max 15)
            source_id = str(job_dict.get("source_id", "greenhouse")).lower()
            freshness_score = 12.0
            if source_id in ("greenhouse", "lever", "ashby", "himalayas"):
                freshness_score += 3.0
            freshness_score = min(15.0, freshness_score)

            # 5. Application Effort & Readiness (Max 10)
            capability = str(job_dict.get("application_capability", "MANUAL_REVIEW_REQUIRED"))
            effort_score = 10.0 if capability == "AUTHORIZED_API_SUBMISSION" else 8.0

            # 6. User Feedback Learning Adjustment (-5 to +5)
            category = job_dict.get("category", "")
            feedbacks = db.query(UserFeedback).filter(UserFeedback.role_category == category).all()
            feedback_delta = sum(f.affinity_delta for f in feedbacks)
            feedback_adj = round(max(-5.0, min(5.0, feedback_delta)), 2)

            # Total Priority Score (0 - 100)
            raw_score = compat_score + elig_score + pref_score + freshness_score + effort_score + feedback_adj
            total_priority = round(max(0.0, min(100.0, raw_score)), 1)

            # Tier Classification
            if not is_india_eligible:
                tier = "PRIORITY_D"
            elif total_priority >= 85.0:
                tier = "PRIORITY_A"
            elif total_priority >= 70.0:
                tier = "PRIORITY_B"
            elif total_priority >= 50.0:
                tier = "PRIORITY_C"
            else:
                tier = "PRIORITY_D"

            explanation = {
                "compatibility": f"{compat_score}/30",
                "eligibility": f"{elig_score}/25",
                "preferences": f"{pref_score}/15",
                "freshness_and_source": f"{freshness_score}/15",
                "effort_readiness": f"{effort_score}/10",
                "feedback_adjustment": f"{feedback_adj}/5",
                "tier_rationale": "High candidate match with verified location eligibility." if tier == "PRIORITY_A" else "Standard qualified vacancy."
            }

            # Upsert into JobPriority table
            p_rec = db.query(JobPriority).filter(JobPriority.job_id == job_id).first()
            if not p_rec:
                p_rec = JobPriority(
                    job_id=job_id,
                    priority_tier=tier,
                    priority_score=total_priority,
                    compatibility_score=compat_score,
                    eligibility_score=elig_score,
                    preference_score=pref_score,
                    freshness_score=freshness_score,
                    effort_score=effort_score,
                    feedback_adjustment=feedback_adj,
                    explanation_json=explanation
                )
                db.add(p_rec)
            else:
                p_rec.priority_tier = tier
                p_rec.priority_score = total_priority
                p_rec.explanation_json = explanation
                p_rec.calculated_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()

            return PrioritizationScoreResult(
                job_id=job_id,
                priority_tier=tier,
                priority_score=total_priority,
                compatibility_score=compat_score,
                eligibility_score=elig_score,
                preference_score=pref_score,
                freshness_score=freshness_score,
                effort_score=effort_score,
                feedback_adjustment=feedback_adj,
                explanation=explanation
            )
        finally:
            db.close()

    def record_user_feedback(self, job_id: int, action: str) -> Dict[str, Any]:
        """
        Records user interaction (SAVED, SKIPPED, APPROVED, REJECTED)
        and adjusts future category scoring dynamically.
        """
        db = SessionLocal()
        try:
            job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
            category = job.category if job else "General"

            deltas = {
                "SAVED": 0.5,
                "APPROVED": 1.0,
                "APPLIED": 1.5,
                "SKIPPED": -0.2,
                "REJECTED": -0.8
            }
            delta = deltas.get(action.upper(), 0.0)

            fb = UserFeedback(
                job_id=job_id,
                action=action.upper(),
                role_category=category,
                affinity_delta=delta
            )
            db.add(fb)
            db.commit()

            return {
                "success": True,
                "job_id": job_id,
                "action": action.upper(),
                "category": category,
                "affinity_delta": delta
            }
        finally:
            db.close()

prioritization_engine = IntelligentOpportunityPrioritizer()
