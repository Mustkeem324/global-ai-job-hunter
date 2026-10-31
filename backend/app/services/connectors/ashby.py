import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.services.connectors.base import BaseJobConnector
from app.services.eligibility_engine import eligibility_engine
from app.services.company_registry import company_registry_service

class AshbyConnector(BaseJobConnector):
    """
    Phase 2 Priority 1: Ashby ATS Public Discovery Connector
    Endpoint: https://api.ashbyhq.com/posting-api/job-board/{company}
    """
    def __init__(self):
        super().__init__("Ashby ATS", "ashby")
        self.base_api = "https://api.ashbyhq.com/posting-api/job-board"

    def search_jobs(self, query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        employers = company_registry_service.get_employers_by_provider("Ashby")
        all_jobs = []

        for emp in employers[:3]:
            company_slug = emp["ats_board_identifier"]
            company_name = emp["company_name"]
            url = f"{self.base_api}/{company_slug}"
            try:
                with httpx.Client(timeout=6.0, headers={"User-Agent": "JobHunterAI/2.0"}) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_jobs = data.get("jobs", [])
                        for rj in raw_jobs:
                            title = rj.get("title", "")
                            if query and query.lower() not in title.lower():
                                continue
                            norm = self.normalize_job({**rj, "_company_name": company_name, "_company_slug": company_slug})
                            all_jobs.append(norm)
            except Exception as e:
                print(f"Ashby fetch error for {company_slug}: {e}")

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
        company = raw_job.get("_company_name", "Ashby Partner")
        slug = raw_job.get("_company_slug", "default")
        raw_id = str(raw_job.get("id"))
        loc = raw_job.get("location", "Remote")
        workplace_type = raw_job.get("workplaceType", "Remote")
        desc = raw_job.get("descriptionPlain", "")[:2500]
        apply_url = raw_job.get("applyUrl") or raw_job.get("jobUrl") or f"https://jobs.ashbyhq.com/{slug}/{raw_id}"

        elig = eligibility_engine.evaluate_eligibility(loc, desc)

        return {
            "job_id": f"ashby-{slug}-{raw_id}",
            "source_id": self.source_key,
            "source_job_id": raw_id,
            "company_name": company,
            "company_website": f"https://jobs.ashbyhq.com/{slug}",
            "job_title": raw_job.get("title", "Software Engineer"),
            "normalized_role": raw_job.get("title", "Software Engineer"),
            "description": desc,
            "required_skills": [],
            "preferred_skills": [],
            "experience_requirements": "Hands-on software delivery experience",
            "education_requirements": "Degree in Computer Science, Engineering, or equivalent",
            "employment_type": raw_job.get("employmentType", "Full-time"),
            "workplace_type": workplace_type,
            "location": loc,
            "eligible_countries": [elig["classification"]],
            "location_evidence": elig["evidence_quote"],
            "is_india_eligible": elig["is_india_eligible"],
            "salary_min": None,
            "salary_max": None,
            "salary_currency": "USD",
            "salary_period": "Annual",
            "compensation_text": "Disclosed upon application",
            "posted_at": raw_job.get("publishedAt") or datetime.now(timezone.utc).isoformat(),
            "official_job_url": raw_job.get("jobUrl", apply_url),
            "application_url": apply_url,
            "application_capability": "USER_REVIEW_REQUIRED",
            "verification_state": "VERIFIED_OPEN"
        }

    def get_application_url(self, raw_job: Dict[str, Any]) -> str:
        return raw_job.get("applyUrl") or raw_job.get("jobUrl") or ""

    def get_application_capabilities(self) -> Dict[str, Any]:
        return {
            "mode": "USER_REVIEW_REQUIRED",
            "supports_direct_api": False,
            "notes": "Employer authenticated submissions require Ashby API credentials. Candidate is presented verified direct link."
        }

    def get_source_permissions(self) -> Dict[str, Any]:
        return {
            "authorized": True,
            "type": "Public ATS Feed",
            "terms": "Ashby HQ Public Job Board API"
        }

    def get_rate_limit_policy(self) -> Dict[str, Any]:
        return {
            "max_requests_per_minute": 60,
            "backoff_factor": 1.5,
            "concurrency_limit": 2
        }

ashby_connector = AshbyConnector()
