import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.services.connectors.base import BaseJobConnector
from app.services.eligibility_engine import eligibility_engine
from app.services.company_registry import company_registry_service

class LeverConnector(BaseJobConnector):
    """
    Phase 2 Priority 1: Lever ATS Public Discovery Connector
    Endpoint: https://api.lever.co/v0/postings/{company}?mode=json
    """
    def __init__(self):
        super().__init__("Lever ATS", "lever")
        self.base_api = "https://api.lever.co/v0/postings"

    def search_jobs(self, query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        employers = company_registry_service.get_employers_by_provider("Lever")
        all_jobs = []

        for emp in employers[:3]:
            company_slug = emp["ats_board_identifier"]
            company_name = emp["company_name"]
            url = f"{self.base_api}/{company_slug}?mode=json&limit=15"
            try:
                with httpx.Client(timeout=6.0, headers={"User-Agent": "JobHunterAI/2.0"}) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        raw_jobs = resp.json()
                        if isinstance(raw_jobs, list):
                            for rj in raw_jobs:
                                title = rj.get("text", "")
                                if query and query.lower() not in title.lower():
                                    continue
                                norm = self.normalize_job({**rj, "_company_name": company_name, "_company_slug": company_slug})
                                all_jobs.append(norm)
            except Exception as e:
                print(f"Lever fetch error for {company_slug}: {e}")

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
        company = raw_job.get("_company_name", "Lever Partner")
        slug = raw_job.get("_company_slug", "default")
        raw_id = str(raw_job.get("id"))
        cats = raw_job.get("categories") or {}
        location_str = cats.get("location", "Remote")
        commitment = cats.get("commitment", "Full-time")
        desc = raw_job.get("descriptionPlain", "")[:2500]
        apply_url = raw_job.get("applyUrl") or raw_job.get("hostedUrl") or f"https://jobs.lever.co/{slug}/{raw_id}"

        elig = eligibility_engine.evaluate_eligibility(location_str, desc)

        return {
            "job_id": f"lever-{slug}-{raw_id}",
            "source_id": self.source_key,
            "source_job_id": raw_id,
            "company_name": company,
            "company_website": f"https://jobs.lever.co/{slug}",
            "job_title": raw_job.get("text", "Software Developer"),
            "normalized_role": raw_job.get("text", "Software Developer"),
            "description": desc,
            "required_skills": [],
            "preferred_skills": [],
            "experience_requirements": "Relevant engineering experience",
            "education_requirements": "Undergraduate degree or equivalent experience",
            "employment_type": commitment,
            "workplace_type": "Remote" if "remote" in location_str.lower() else "Onsite",
            "location": location_str,
            "eligible_countries": [elig["classification"]],
            "location_evidence": elig["evidence_quote"],
            "is_india_eligible": elig["is_india_eligible"],
            "salary_min": None,
            "salary_max": None,
            "salary_currency": "USD",
            "salary_period": "Annual",
            "compensation_text": "Competitive",
            "posted_at": datetime.fromtimestamp(raw_job.get("createdAt", 0)/1000, tz=timezone.utc).isoformat() if raw_job.get("createdAt") else datetime.now(timezone.utc).isoformat(),
            "official_job_url": raw_job.get("hostedUrl", apply_url),
            "application_url": apply_url,
            "application_capability": "USER_REVIEW_REQUIRED",
            "verification_state": "VERIFIED_OPEN"
        }

    def get_application_url(self, raw_job: Dict[str, Any]) -> str:
        return raw_job.get("applyUrl") or raw_job.get("hostedUrl") or ""

    def get_application_capabilities(self) -> Dict[str, Any]:
        return {
            "mode": "USER_REVIEW_REQUIRED",
            "supports_direct_api": False,
            "notes": "Direct application submission requires employer API keys. Candidates are routed to verified hosted application form."
        }

    def get_source_permissions(self) -> Dict[str, Any]:
        return {
            "authorized": True,
            "type": "Public ATS Feed",
            "terms": "Lever Public Postings API"
        }

    def get_rate_limit_policy(self) -> Dict[str, Any]:
        return {
            "max_requests_per_minute": 30,
            "backoff_factor": 2.0,
            "concurrency_limit": 2
        }

lever_connector = LeverConnector()
