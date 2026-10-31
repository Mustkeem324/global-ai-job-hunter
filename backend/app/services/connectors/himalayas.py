import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.services.connectors.base import BaseJobConnector
from app.services.eligibility_engine import eligibility_engine

class HimalayasConnector(BaseJobConnector):
    """
    Phase 2 Priority 2: Himalayas Remote Jobs API
    Endpoint: https://himalayas.app/jobs/api
    Requires preserving original applicationLink unchanged.
    """
    def __init__(self):
        super().__init__("Himalayas Remote API", "himalayas")
        self.api_url = "https://himalayas.app/jobs/api"

    def search_jobs(self, query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        url = f"{self.api_url}?limit=25"
        all_jobs = []
        try:
            with httpx.Client(timeout=8.0, headers={"User-Agent": "JobHunterAI/2.0"}) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    jobs = data.get("jobs", [])
                    for j in jobs:
                        title = j.get("title", "")
                        if query and query.lower() not in title.lower():
                            continue
                        all_jobs.append(self.normalize_job(j))
        except Exception as e:
            print(f"Himalayas fetch error: {e}")

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
        raw_id = str(raw_job.get("id") or raw_job.get("slug") or raw_job.get("title"))
        company = raw_job.get("companyName", "Remote Employer")
        restrictions = raw_job.get("locationRestrictions", [])
        loc_str = ", ".join(restrictions) if restrictions else "Worldwide Remote"
        desc = raw_job.get("excerpt", "") or raw_job.get("description", "")
        # Designated unchanged application link
        app_url = raw_job.get("applicationLink") or f"https://himalayas.app/companies/{raw_job.get('companySlug')}/jobs/{raw_job.get('slug')}"

        elig = eligibility_engine.evaluate_eligibility(loc_str, desc)

        min_sal = raw_job.get("minSalary")
        max_sal = raw_job.get("maxSalary")
        currency = raw_job.get("currency", "USD")
        comp_text = f"${min_sal:,} - ${max_sal:,} {currency}" if (min_sal and max_sal) else "Disclosed in listing"

        return {
            "job_id": f"himalayas-{raw_id}",
            "source_id": self.source_key,
            "source_job_id": raw_id,
            "company_name": company,
            "company_website": raw_job.get("companyWebsite") or f"https://himalayas.app/companies/{raw_job.get('companySlug')}",
            "job_title": raw_job.get("title", "Remote Engineer"),
            "normalized_role": raw_job.get("title", "Remote Engineer"),
            "description": desc[:2500],
            "required_skills": raw_job.get("skills", []),
            "preferred_skills": [],
            "experience_requirements": raw_job.get("seniority", "Mid - Senior"),
            "education_requirements": "Not explicitly specified",
            "employment_type": "Full-time",
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
            "official_job_url": app_url,
            "application_url": app_url,
            "application_capability": "USER_REVIEW_REQUIRED",
            "verification_state": "VERIFIED_OPEN"
        }

    def get_application_url(self, raw_job: Dict[str, Any]) -> str:
        return raw_job.get("applicationLink", "")

    def get_application_capabilities(self) -> Dict[str, Any]:
        return {
            "mode": "USER_REVIEW_REQUIRED",
            "supports_direct_api": False,
            "notes": "Himalayas requires routing candidate through unchanged official applicationLink."
        }

    def get_source_permissions(self) -> Dict[str, Any]:
        return {
            "authorized": True,
            "type": "Public Remote API",
            "terms": "Himalayas Public API Terms"
        }

    def get_rate_limit_policy(self) -> Dict[str, Any]:
        return {
            "max_requests_per_minute": 60,
            "backoff_factor": 1.5,
            "concurrency_limit": 3
        }

himalayas_connector = HimalayasConnector()
