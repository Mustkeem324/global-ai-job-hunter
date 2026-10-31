import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.services.connectors.base import BaseJobConnector
from app.services.eligibility_engine import eligibility_engine

class JobicyConnector(BaseJobConnector):
    """
    Phase 2 Priority 2: Jobicy Remote Jobs API
    Endpoint: https://jobicy.com/api/v2/remote-jobs
    Distinguishes public listing URLs from optional direct ATS URLs.
    """
    def __init__(self):
        super().__init__("Jobicy Remote API", "jobicy")
        self.api_url = "https://jobicy.com/api/v2/remote-jobs"

    def search_jobs(self, query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        url = f"{self.api_url}?count=25"
        if query:
            url += f"&tag={query.replace(' ', '+')}"
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
            print(f"Jobicy fetch error: {e}")

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
        company = raw_job.get("companyName", "Jobicy Employer")
        loc_str = raw_job.get("jobGeo", "Anywhere")
        desc_html = raw_job.get("jobDescription", "")
        clean_desc = desc_html.replace("<p>", " ").replace("</p>", "\n")[:2500]
        # Distinguish public listing URL
        public_url = raw_job.get("url", "")

        elig = eligibility_engine.evaluate_eligibility(loc_str, clean_desc)

        min_sal = raw_job.get("annualSalaryMin")
        max_sal = raw_job.get("annualSalaryMax")
        currency = raw_job.get("salaryCurrency", "USD")
        comp_text = f"${min_sal:,} - ${max_sal:,} {currency}" if (min_sal and max_sal) else "Disclosed in posting"

        return {
            "job_id": f"jobicy-{raw_id}",
            "source_id": self.source_key,
            "source_job_id": raw_id,
            "company_name": company,
            "company_website": f"https://jobicy.com/jobs/by/{raw_job.get('companySlug', '')}",
            "job_title": raw_job.get("jobTitle", "Remote Engineer"),
            "normalized_role": raw_job.get("jobTitle", "Remote Engineer"),
            "description": clean_desc,
            "required_skills": [raw_job.get("jobCategory")] if raw_job.get("jobCategory") else [],
            "preferred_skills": [],
            "experience_requirements": raw_job.get("jobLevel", "Any"),
            "education_requirements": "Not stated",
            "employment_type": raw_job.get("jobType", "Full-time"),
            "workplace_type": "Remote",
            "location": loc_str,
            "eligible_countries": [elig["classification"]],
            "location_evidence": elig["evidence_quote"],
            "is_india_eligible": elig["is_india_eligible"],
            "salary_min": min_sal,
            "salary_max": max_sal,
            "salary_currency": currency,
            "salary_period": "Annual",
            "compensation_text": comp_text,
            "posted_at": raw_job.get("pubDate") or datetime.now(timezone.utc).isoformat(),
            "official_job_url": public_url,
            "application_url": public_url,
            "application_capability": "USER_REVIEW_REQUIRED",
            "verification_state": "VERIFIED_OPEN"
        }

    def get_application_url(self, raw_job: Dict[str, Any]) -> str:
        return raw_job.get("url", "")

    def get_application_capabilities(self) -> Dict[str, Any]:
        return {
            "mode": "USER_REVIEW_REQUIRED",
            "supports_direct_api": False,
            "notes": "Jobicy free tier provides canonical listing URL with direct company routing."
        }

    def get_source_permissions(self) -> Dict[str, Any]:
        return {
            "authorized": True,
            "type": "Public Remote API",
            "terms": "Jobicy Public API v2"
        }

    def get_rate_limit_policy(self) -> Dict[str, Any]:
        return {
            "max_requests_per_minute": 30,
            "backoff_factor": 2.0,
            "concurrency_limit": 2
        }

jobicy_connector = JobicyConnector()
