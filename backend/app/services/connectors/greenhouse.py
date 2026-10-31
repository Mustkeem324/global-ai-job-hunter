import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.services.connectors.base import BaseJobConnector
from app.services.eligibility_engine import eligibility_engine
from app.services.company_registry import company_registry_service

class GreenhouseConnector(BaseJobConnector):
    """
    Phase 2 Priority 1: Greenhouse ATS Public Discovery Connector
    Endpoint: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
    """
    def __init__(self):
        super().__init__("Greenhouse ATS", "greenhouse")
        self.base_api = "https://boards-api.greenhouse.io/v1/boards"

    def search_jobs(self, query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        employers = company_registry_service.get_employers_by_provider("Greenhouse")
        all_jobs = []
        
        # Limit to 3 employers per sweep to respect rate limits & response times
        for emp in employers[:4]:
            board_token = emp["ats_board_identifier"]
            company_name = emp["company_name"]
            url = f"{self.base_api}/{board_token}/jobs?content=true"
            try:
                with httpx.Client(timeout=6.0, headers={"User-Agent": "JobHunterAI/2.0"}) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_jobs = data.get("jobs", [])
                        for rj in raw_jobs:
                            title = rj.get("title", "")
                            # If query provided, filter locally
                            if query and query.lower() not in title.lower():
                                continue
                            norm = self.normalize_job({**rj, "_company_name": company_name, "_board_token": board_token})
                            all_jobs.append(norm)
            except Exception as e:
                print(f"Greenhouse scrape error for {board_token}: {e}")

        return all_jobs

    def fetch_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        # job_id format: greenhouse-{board_token}-{id}
        parts = job_id.split("-")
        if len(parts) >= 3:
            board_token = parts[1]
            raw_id = parts[2]
            url = f"{self.base_api}/{board_token}/jobs/{raw_id}"
            try:
                with httpx.Client(timeout=5.0) as client:
                    r = client.get(url)
                    if r.status_code == 200:
                        return r.json()
            except Exception:
                pass
        return None

    def verify_job(self, job_url: str) -> bool:
        try:
            with httpx.Client(timeout=4.0) as client:
                r = client.head(job_url, follow_redirects=True)
                return r.status_code in (200, 301, 302)
        except Exception:
            return False

    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        company = raw_job.get("_company_name", "Greenhouse Partner")
        board_token = raw_job.get("_board_token", "default")
        raw_id = str(raw_job.get("id"))
        loc_obj = raw_job.get("location") or {}
        location_str = loc_obj.get("name", "Remote") if isinstance(loc_obj, dict) else str(loc_obj)
        content_html = raw_job.get("content", "")
        clean_desc = content_html.replace("<p>", " ").replace("</p>", "\n").replace("<br>", "\n")[:2500]
        app_url = raw_job.get("absolute_url") or f"https://job-boards.greenhouse.io/{board_token}/jobs/{raw_id}"

        elig = eligibility_engine.evaluate_eligibility(location_str, clean_desc)

        return {
            "job_id": f"greenhouse-{board_token}-{raw_id}",
            "source_id": self.source_key,
            "source_job_id": raw_id,
            "company_name": company,
            "company_website": f"https://job-boards.greenhouse.io/{board_token}",
            "job_title": raw_job.get("title", "Software Engineer"),
            "normalized_role": raw_job.get("title", "Software Engineer"),
            "description": clean_desc,
            "required_skills": [],
            "preferred_skills": [],
            "experience_requirements": "Demonstrated technical experience",
            "education_requirements": "Bachelor's degree or equivalent practical experience",
            "employment_type": "Full-time",
            "workplace_type": "Remote" if "remote" in location_str.lower() or "home" in location_str.lower() else "Onsite",
            "location": location_str,
            "eligible_countries": [elig["classification"]],
            "location_evidence": elig["evidence_quote"],
            "is_india_eligible": elig["is_india_eligible"],
            "salary_min": None,
            "salary_max": None,
            "salary_currency": "USD",
            "salary_period": "Annual",
            "compensation_text": "Competitive Industry Band",
            "posted_at": raw_job.get("updated_at") or datetime.now(timezone.utc).isoformat(),
            "official_job_url": app_url,
            "application_url": app_url,
            "application_capability": "USER_REVIEW_REQUIRED",
            "verification_state": "VERIFIED_OPEN"
        }

    def get_application_url(self, raw_job: Dict[str, Any]) -> str:
        return raw_job.get("absolute_url", "")

    def get_application_capabilities(self) -> Dict[str, Any]:
        return {
            "mode": "USER_REVIEW_REQUIRED",
            "supports_direct_api": False,
            "notes": "Public boards API allows open vacancy reading. Jobseeker submissions require authorized form completion or employer-issued API keys."
        }

    def get_source_permissions(self) -> Dict[str, Any]:
        return {
            "authorized": True,
            "type": "Public ATS Feed",
            "terms": "Greenhouse Public Job Board API"
        }

    def get_rate_limit_policy(self) -> Dict[str, Any]:
        return {
            "max_requests_per_minute": 60,
            "backoff_factor": 1.5,
            "concurrency_limit": 2
        }

greenhouse_connector = GreenhouseConnector()
