import re
import datetime
from typing import Dict, Any, List, Optional

from app.core.database import SessionLocal
from app.models.schema import JobPosting, Application, NaukriJobImport
from app.services.naukri_adapter import naukri_adapter, NaukriCapabilityMode
from app.core.state_machine import ApplicationStatus

class NaukriDiscoveryService:
    """
    Phase 7 Module 3 & Module 9: Naukri Discovery & Multi-Job Application Workflow
    Discovers Naukri vacancies via user URLs, email alerts, or ATS redirects.
    Supports multi-job preparation for 10, 25, 50, 100 listings with cross-source deduplication.
    """

    def parse_naukri_alert_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Parses raw email alert body from alerts@naukri.com or jobalerts@naukri.com.
        Extracts titles, companies, locations, and direct job links.
        """
        jobs = []
        # Find all job URLs
        url_matches = re.findall(r"(https?://(?:www\.)?naukri\.com/job-listings-[a-zA-Z0-9\-_]+)", text)
        for url in set(url_matches):
            slug = url.split("job-listings-")[-1]
            parts = slug.split("-")
            title = "Software Engineer"
            company = "Naukri Hiring Partner"
            if len(parts) >= 2:
                title = " ".join(parts[:-2]).title() or "Software Engineer"
                company = parts[-2].title() or "Enterprise"

            jobs.append({
                "job_url": url,
                "title": title,
                "company": company,
                "location": "India (Remote / Hybrid)",
                "snippet": f"Naukri.com email alert recommendation for {title}."
            })
        return jobs

    def ingest_naukri_url(self, url: str) -> Dict[str, Any]:
        """
        Directly ingests a user-provided Naukri link.
        """
        return naukri_adapter.import_user_provided_jobs(url)

    def prepare_naukri_batch(self, batch_size: int = 10, min_match_score: int = 85) -> Dict[str, Any]:
        """
        Module 9: Prepares a multi-job application batch from discovered Naukri listings.
        Categorizes outcomes:
        - AUTHORIZED_AUTO_SUBMISSION (for verified external sandbox ATS)
        - READY_FOR_MANUAL_APPLICATION (standard Naukri portal)
        - ALREADY_APPLIED
        - INELIGIBLE
        - INVALID_JOB
        """
        db = SessionLocal()
        try:
            # Query candidate Naukri jobs
            jobs = db.query(JobPosting).filter(
                JobPosting.source_id.in_(["naukri", "naukri_neo"]),
                JobPosting.status == "active"
            ).order_by(JobPosting.id.desc()).all()

            results = {
                "batch_size": batch_size,
                "total_evaluated": 0,
                "READY_FOR_MANUAL_APPLICATION": [],
                "AUTHORIZED_AUTO_SUBMISSION": [],
                "ALREADY_APPLIED": [],
                "INELIGIBLE": [],
                "INVALID_JOB": []
            }

            for job in jobs:
                if len(results["READY_FOR_MANUAL_APPLICATION"]) + len(results["AUTHORIZED_AUTO_SUBMISSION"]) >= batch_size:
                    break

                results["total_evaluated"] += 1

                # 1. Check duplicate application
                existing_app = db.query(Application).filter(Application.job_id == job.id).first()
                if existing_app:
                    results["ALREADY_APPLIED"].append({
                        "job_id": job.id,
                        "company": job.company_name,
                        "title": job.title,
                        "status": existing_app.status.value if hasattr(existing_app.status, "value") else str(existing_app.status)
                    })
                    continue

                # 2. Check Match Score
                score = naukri_adapter.calculate_match({
                    "title": job.title,
                    "description": job.description,
                    "company_name": job.company_name,
                    "location": job.location,
                    "is_india_eligible": job.is_india_eligible
                })

                if score < min_match_score:
                    results["INELIGIBLE"].append({
                        "job_id": job.id,
                        "company": job.company_name,
                        "title": job.title,
                        "match_score": score,
                        "reason": f"Compatibility {score}% is below threshold {min_match_score}%."
                    })
                    continue

                # 3. Prepare Package
                pkg = naukri_adapter.create_application_package(job.id)
                cap = pkg.get("capability")

                item_summary = {
                    "job_id": job.id,
                    "company": job.company_name,
                    "title": job.title,
                    "match_score": score,
                    "application_url": job.application_url,
                    "capability": cap
                }

                if cap == NaukriCapabilityMode.AUTHORIZED_AUTO_SUBMISSION:
                    results["AUTHORIZED_AUTO_SUBMISSION"].append(item_summary)
                else:
                    results["READY_FOR_MANUAL_APPLICATION"].append(item_summary)

            return {
                "success": True,
                "summary": {
                    "requested_size": batch_size,
                    "total_evaluated": results["total_evaluated"],
                    "ready_for_manual": len(results["READY_FOR_MANUAL_APPLICATION"]),
                    "authorized_auto": len(results["AUTHORIZED_AUTO_SUBMISSION"]),
                    "already_applied": len(results["ALREADY_APPLIED"]),
                    "ineligible": len(results["INELIGIBLE"])
                },
                "prepared_jobs": results["READY_FOR_MANUAL_APPLICATION"] + results["AUTHORIZED_AUTO_SUBMISSION"]
            }
        finally:
            db.close()

naukri_discovery_service = NaukriDiscoveryService()
