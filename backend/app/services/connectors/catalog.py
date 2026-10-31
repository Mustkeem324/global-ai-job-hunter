import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.services.connectors.base import BaseJobConnector
from app.services.eligibility_engine import eligibility_engine

class LocalVerifiedCatalogConnector(BaseJobConnector):
    """
    Curated Verified Opportunities Connector
    Loads verified vacancies from database/opportunities.json
    """
    def __init__(self):
        super().__init__("Verified Opportunity Network", "catalog")
        self.catalog_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "database", "opportunities.json")
        )

    def search_jobs(self, query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not os.path.exists(self.catalog_path):
            return []
        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception:
            return []

        all_jobs = []
        for item in raw_data:
            title = item.get("title", "")
            comp = item.get("company", "")
            cat = item.get("category", "")
            if query and query.lower() not in f"{title} {comp} {cat}".lower():
                continue
            all_jobs.append(self.normalize_job(item))
        return all_jobs

    def fetch_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        return None

    def verify_job(self, job_url: str) -> bool:
        return bool(job_url and job_url.startswith("http"))

    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        raw_id = str(raw_job.get("id"))
        company = raw_job.get("company", "Verified Partner")
        loc_str = raw_job.get("country_eligibility", "Worldwide")
        elig = eligibility_engine.evaluate_eligibility(loc_str, raw_job.get("description", ""))

        return {
            "job_id": f"catalog-{raw_id}",
            "source_id": self.source_key,
            "source_job_id": raw_id,
            "company_name": company,
            "company_website": raw_job.get("url", "https://freelancekar.com"),
            "job_title": raw_job.get("title", "AI Specialist"),
            "normalized_role": raw_job.get("title", "AI Specialist"),
            "description": f"Verified position at {company} for {raw_job.get('title')}. Compensation: {raw_job.get('compensation')}. Location eligibility: {loc_str}.",
            "required_skills": [],
            "preferred_skills": [],
            "experience_requirements": raw_job.get("experience", "2+ years"),
            "education_requirements": "Undergraduate degree or equivalent",
            "employment_type": raw_job.get("type", "Contract"),
            "workplace_type": raw_job.get("work_arrangement", "Remote"),
            "location": loc_str,
            "eligible_countries": [elig["classification"]],
            "location_evidence": elig["evidence_quote"],
            "is_india_eligible": elig["is_india_eligible"],
            "salary_min": None,
            "salary_max": None,
            "salary_currency": raw_job.get("currency", "USD"),
            "salary_period": "Contract / Hourly",
            "compensation_text": raw_job.get("compensation", "Not disclosed"),
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "official_job_url": raw_job.get("url", ""),
            "application_url": raw_job.get("url", ""),
            "application_capability": "AUTHORIZED_FORM_WORKFLOW",
            "verification_state": "VERIFIED_OPEN"
        }

    def get_application_url(self, raw_job: Dict[str, Any]) -> str:
        return raw_job.get("url", "")

    def get_application_capabilities(self) -> Dict[str, Any]:
        return {
            "mode": "AUTHORIZED_FORM_WORKFLOW",
            "supports_direct_api": False,
            "notes": "Verified partner catalog with automated document preparation."
        }

    def get_source_permissions(self) -> Dict[str, Any]:
        return {
            "authorized": True,
            "type": "Curated Verified Catalog",
            "terms": "Internal Verified Opportunity Catalog"
        }

    def get_rate_limit_policy(self) -> Dict[str, Any]:
        return {
            "max_requests_per_minute": 1000,
            "backoff_factor": 1.0,
            "concurrency_limit": 10
        }

class MockATSConnector(BaseJobConnector):
    """
    Authorized Sandbox ATS Connector for automated testing and Mode A verification.
    """
    def __init__(self):
        super().__init__("Authorized Sandbox ATS", "mock_ats")

    def search_jobs(self, query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return [
            {
                "job_id": "sandbox-ai-01",
                "source_id": self.source_key,
                "source_job_id": "sandbox-ai-01",
                "company_name": "Nexus Frontier AI (Sandbox)",
                "company_website": "https://api.sandbox-ats.local",
                "job_title": "Staff AI Benchmark & Coding Evaluator",
                "normalized_role": "AI Coding Evaluator",
                "description": "Evaluate and benchmark Python coding responses generated by frontier LLMs under strict task rubrics.",
                "required_skills": ["Python", "RLHF", "LLM Evaluation"],
                "preferred_skills": ["Prompt Engineering"],
                "experience_requirements": "2+ years Python/RLHF",
                "education_requirements": "B.Tech or equivalent degree",
                "employment_type": "Contract",
                "workplace_type": "Remote",
                "location": "India Confirmed",
                "eligible_countries": ["Remote — India"],
                "location_evidence": "Sandbox confirmed eligibility for India",
                "is_india_eligible": True,
                "salary_min": 85.0,
                "salary_max": 110.0,
                "salary_currency": "USD",
                "salary_period": "Hourly",
                "compensation_text": "$85 - $110 / hr",
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "official_job_url": "https://api.sandbox-ats.local/v1/jobs/sandbox-ai-01/apply",
                "application_url": "https://api.sandbox-ats.local/v1/jobs/sandbox-ai-01/apply",
                "application_capability": "API_SUBMISSION_AUTHORIZED",
                "verification_state": "VERIFIED_OPEN"
            }
        ]

    def fetch_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.search_jobs()[0]

    def verify_job(self, job_url: str) -> bool:
        return True

    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        return raw_job

    def get_application_url(self, raw_job: Dict[str, Any]) -> str:
        return "https://api.sandbox-ats.local/v1/jobs/sandbox-ai-01/apply"

    def get_application_capabilities(self) -> Dict[str, Any]:
        return {
            "mode": "API_SUBMISSION_AUTHORIZED",
            "supports_direct_api": True,
            "notes": "Sandbox authorized API endpoint permits direct programmatic application submission."
        }

    def get_source_permissions(self) -> Dict[str, Any]:
        return {
            "authorized": True,
            "type": "Authorized Sandbox API",
            "terms": "Local Sandbox Terms"
        }

    def get_rate_limit_policy(self) -> Dict[str, Any]:
        return {
            "max_requests_per_minute": 1000,
            "backoff_factor": 1.0,
            "concurrency_limit": 10
        }

catalog_connector = LocalVerifiedCatalogConnector()
mock_ats_connector = MockATSConnector()
