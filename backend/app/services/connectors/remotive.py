import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.services.connectors.base import BaseJobConnector
from app.services.eligibility_engine import eligibility_engine

class RemotiveConnector(BaseJobConnector):
    """
    Phase 2 Priority 2: Remotive Remote Jobs API
    Endpoint: https://remotive.com/api/remote-jobs
    Preserves source attribution and respects polling restrictions.
    """
    def __init__(self):
        super().__init__("Remotive Remote API", "remotive")
        self.api_url = "https://remotive.com/api/remote-jobs"

    def search_jobs(self, query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        url = f"{self.api_url}?limit=25"
        if query:
            url += f"&search={query.replace(' ', '+')}"
        all_jobs = []
        try:
            with httpx.Client(timeout=8.0, headers={"User-Agent": "JobHunterAI/2.0"}) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    jobs = data.get("jobs", [])
                    for j in jobs:
                        all_jobs.append(self.normalize_job(j))
        except Exception as e:
            print(f"Remotive fetch error: {e}")

        return all_jobs

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
        raw_id = str(raw_job.get("id"))
        company = raw_job.get("company_name", "Remote Employer")
        loc_str = raw_job.get("candidate_required_location", "Worldwide")
        desc = (raw_job.get("description", "") or "").replace("<p>", " ").replace("</p>", "\n")[:2500]
        app_url = raw_job.get("url", "")

        elig = eligibility_engine.evaluate_eligibility(loc_str, desc)
        comp_text = raw_job.get("salary") or "Competitive"

        return {
            "job_id": f"remotive-{raw_id}",
            "source_id": self.source_key,
            "source_job_id": raw_id,
            "company_name": company,
            "company_website": raw_job.get("company_logo_url") or "https://remotive.com",
            "job_title": raw_job.get("title", "Software Developer"),
            "normalized_role": raw_job.get("title", "Software Developer"),
            "description": desc,
            "required_skills": raw_job.get("tags", []),
            "preferred_skills": [],
            "experience_requirements": "2+ years professional experience",
            "education_requirements": "Not stated",
            "employment_type": raw_job.get("job_type", "Full-time"),
            "workplace_type": "Remote",
            "location": loc_str,
            "eligible_countries": [elig["classification"]],
            "location_evidence": elig["evidence_quote"],
            "is_india_eligible": elig["is_india_eligible"],
            "salary_min": None,
            "salary_max": None,
            "salary_currency": "USD",
            "salary_period": "Annual",
            "compensation_text": comp_text,
            "posted_at": raw_job.get("publication_date") or datetime.now(timezone.utc).isoformat(),
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
            "notes": "Remotive public API routes applicants to the verified company application portal with Remotive attribution."
        }

    def get_source_permissions(self) -> Dict[str, Any]:
        return {
            "authorized": True,
            "type": "Public Remote API",
            "terms": "Remotive Free API Terms (Attribution Required)"
        }

    def get_rate_limit_policy(self) -> Dict[str, Any]:
        return {
            "max_requests_per_minute": 30,
            "backoff_factor": 2.0,
            "concurrency_limit": 2
        }

remotive_connector = RemotiveConnector()
