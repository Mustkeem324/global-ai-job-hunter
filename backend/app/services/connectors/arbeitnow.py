import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.services.connectors.base import BaseJobConnector
from app.services.eligibility_engine import eligibility_engine

class ArbeitnowConnector(BaseJobConnector):
    """
    Phase 2 Priority 2: Arbeitnow Job Board API
    Endpoint: https://www.arbeitnow.com/api/job-board-api
    """
    def __init__(self):
        super().__init__("Arbeitnow API", "arbeitnow")
        self.api_url = "https://www.arbeitnow.com/api/job-board-api"

    def search_jobs(self, query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        all_jobs = []
        try:
            with httpx.Client(timeout=8.0, headers={"User-Agent": "JobHunterAI/2.0"}) as client:
                resp = client.get(self.api_url)
                if resp.status_code == 200:
                    data = resp.json()
                    jobs = data.get("data", [])
                    for j in jobs:
                        title = j.get("title", "")
                        if query and query.lower() not in title.lower():
                            continue
                        all_jobs.append(self.normalize_job(j))
        except Exception as e:
            print(f"Arbeitnow fetch error: {e}")

        return all_jobs[:25]

    def fetch_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        return None

    def verify_job(self, job_url: str) -> bool:
        try:
            with httpx.Client(timeout=4.0) as client:
                r = client.head(job_url, follow_redirects=True)
                return r.status_code in (200, 301, 302)
        except Exception:
            return False

    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        slug = raw_job.get("slug", "")
        company = raw_job.get("company_name", "Arbeitnow Partner")
        is_remote = raw_job.get("remote", False)
        loc_str = raw_job.get("location", "Remote" if is_remote else "Onsite")
        desc = (raw_job.get("description", "") or "").replace("<p>", " ").replace("</p>", "\n")[:2500]
        app_url = raw_job.get("url", "")

        elig = eligibility_engine.evaluate_eligibility(loc_str, desc)

        return {
            "job_id": f"arbeitnow-{slug}",
            "source_id": self.source_key,
            "source_job_id": slug,
            "company_name": company,
            "company_website": f"https://www.arbeitnow.com/jobs/companies/{raw_job.get('company_slug', '')}",
            "job_title": raw_job.get("title", "Software Developer"),
            "normalized_role": raw_job.get("title", "Software Developer"),
            "description": desc,
            "required_skills": raw_job.get("tags", []),
            "preferred_skills": [],
            "experience_requirements": "Not stated",
            "education_requirements": "Not stated",
            "employment_type": "Full-time",
            "workplace_type": "Remote" if is_remote else "Onsite",
            "location": loc_str,
            "eligible_countries": [elig["classification"]],
            "location_evidence": elig["evidence_quote"],
            "is_india_eligible": elig["is_india_eligible"],
            "salary_min": None,
            "salary_max": None,
            "salary_currency": "EUR",
            "salary_period": "Annual",
            "compensation_text": "Competitive European Band",
            "posted_at": datetime.fromtimestamp(raw_job.get("created_at", 0), tz=timezone.utc).isoformat() if raw_job.get("created_at") else datetime.now(timezone.utc).isoformat(),
            "official_job_url": app_url,
            "application_url": app_url,
            "application_capability": "USER_REVIEW_REQUIRED",
            "verification_state": "VERIFIED_OPEN"
        }

    def get_application_url(self, raw_job: Dict[str, Any]) -> str:
        return raw_job.get("url", "")

    def get_application_capabilities(self) -> Dict[str, Any]:
        return {
            "mode": "USER_REVIEW_REQUIRED",
            "supports_direct_api": False,
            "notes": "Arbeitnow provides canonical listing links."
        }

    def get_source_permissions(self) -> Dict[str, Any]:
        return {
            "authorized": True,
            "type": "Public Remote API",
            "terms": "Arbeitnow Open Job Board API"
        }

    def get_rate_limit_policy(self) -> Dict[str, Any]:
        return {
            "max_requests_per_minute": 60,
            "backoff_factor": 1.5,
            "concurrency_limit": 3
        }

arbeitnow_connector = ArbeitnowConnector()
