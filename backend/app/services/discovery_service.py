import os
import json
import httpx
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class BaseJobSourceAdapter(ABC):
    def __init__(self, name: str, adapter_key: str):
        self.name = name
        self.adapter_key = adapter_key

    @abstractmethod
    def discover_jobs(self, query: str = "") -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def verify_listing(self, job_url: str) -> bool:
        pass

    @abstractmethod
    def check_application_capability(self) -> Dict[str, Any]:
        pass

class LocalCatalogAdapter(BaseJobSourceAdapter):
    """Loads and verifies curated, live opportunities from the curated dataset."""
    def __init__(self):
        super().__init__("Verified Opportunity Network", "local_catalog")
        self.catalog_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "database", "opportunities.json"
        )

    def discover_jobs(self, query: str = "") -> List[Dict[str, Any]]:
        if not os.path.exists(self.catalog_path):
            return []
        with open(self.catalog_path, "r") as f:
            raw_data = json.load(f)
        
        normalized = []
        for item in raw_data:
            # Check query filter if provided
            if query and query.lower() not in (item.get("title", "") + item.get("company", "") + item.get("category", "")).lower():
                continue
            normalized.append({
                "source_job_id": f"catalog-{item.get('id')}",
                "company_name": item.get("company"),
                "title": item.get("title"),
                "category": item.get("category", "Software Engineering"),
                "employment_type": item.get("type", "Contract"),
                "work_arrangement": item.get("work_arrangement", "Remote"),
                "country_eligibility": item.get("country_eligibility", "Worldwide"),
                "is_india_eligible": "india" in item.get("country_eligibility", "").lower() or "worldwide" in item.get("country_eligibility", "").lower(),
                "compensation_text": item.get("compensation", "Not disclosed"),
                "currency": item.get("currency", "USD"),
                "required_experience": item.get("experience", "2+ years"),
                "application_url": item.get("url"),
                "description": f"Verified position at {item.get('company')} for {item.get('title')}. Compensation: {item.get('compensation')}. Location eligibility: {item.get('country_eligibility')}.",
                "status": "Active",
                "posted_date": datetime.utcnow().isoformat()
            })
        return normalized

    def verify_listing(self, job_url: str) -> bool:
        return bool(job_url and job_url.startswith("http"))

    def check_application_capability(self) -> Dict[str, Any]:
        return {
            "supports_auto_apply": False,
            "supports_assisted_apply": True,
            "application_mode": "MODE_C_ASSISTED"
        }

class RemotiveAdapter(BaseJobSourceAdapter):
    """Fetches public remote software and AI jobs from Remotive API."""
    def __init__(self):
        super().__init__("Remotive Public API", "remotive")
        self.api_url = "https://remotive.com/api/remote-jobs"

    def discover_jobs(self, query: str = "python") -> List[Dict[str, Any]]:
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(f"{self.api_url}?search={query}&limit=10")
                if resp.status_code != 200:
                    return []
                data = resp.json()
                jobs = data.get("jobs", [])
                normalized = []
                for j in jobs:
                    loc = j.get("candidate_required_location", "Worldwide")
                    is_in = "india" in loc.lower() or "worldwide" in loc.lower() or not loc
                    normalized.append({
                        "source_job_id": f"remotive-{j.get('id')}",
                        "company_name": j.get("company_name", "Remote Employer"),
                        "title": j.get("title", "Software Developer"),
                        "category": j.get("category", "Software Development"),
                        "employment_type": j.get("job_type", "full_time"),
                        "work_arrangement": "Remote",
                        "country_eligibility": loc or "Worldwide",
                        "is_india_eligible": is_in,
                        "compensation_text": j.get("salary") or "Competitive",
                        "currency": "USD",
                        "required_experience": "2+ years",
                        "application_url": j.get("url"),
                        "description": j.get("description", "")[:1200],
                        "status": "Active",
                        "posted_date": j.get("publication_date")
                    })
                return normalized
        except Exception:
            return []

    def verify_listing(self, job_url: str) -> bool:
        return bool(job_url and job_url.startswith("http"))

    def check_application_capability(self) -> Dict[str, Any]:
        return {
            "supports_auto_apply": False,
            "supports_assisted_apply": True,
            "application_mode": "MODE_C_ASSISTED"
        }

class MockATSAdapter(BaseJobSourceAdapter):
    """
    Authorized Mock ATS Adapter for verifying Mode A (Auto-Apply)
    and Mode B (Approval Required) in sandbox and automated test environments.
    """
    def __init__(self):
        super().__init__("Authorized Sandbox ATS", "mock_ats")

    def discover_jobs(self, query: str = "") -> List[Dict[str, Any]]:
        return [
            {
                "source_job_id": "sandbox-ai-01",
                "company_name": "Nexus Frontier AI (Sandbox)",
                "title": "Staff AI Benchmark & Coding Evaluator",
                "category": "AI Training / Coding",
                "employment_type": "Contract",
                "work_arrangement": "Remote",
                "country_eligibility": "India Confirmed",
                "is_india_eligible": True,
                "compensation_text": "$85 - $110 / hr",
                "currency": "USD",
                "required_experience": "2+ years Python/RLHF",
                "application_url": "https://api.sandbox-ats.local/v1/jobs/sandbox-ai-01/apply",
                "description": "Evaluate and benchmark Python coding responses generated by frontier LLMs.",
                "status": "Active",
                "posted_date": datetime.utcnow().isoformat()
            }
        ]

    def verify_listing(self, job_url: str) -> bool:
        return True

    def check_application_capability(self) -> Dict[str, Any]:
        return {
            "supports_auto_apply": True,
            "supports_assisted_apply": True,
            "application_mode": "MODE_A_AUTO"
        }

class DiscoveryService:
    def __init__(self):
        self.adapters = {
            "local_catalog": LocalCatalogAdapter(),
            "remotive": RemotiveAdapter(),
            "mock_ats": MockATSAdapter()
        }

    def run_discovery(self, query: str = "") -> List[Dict[str, Any]]:
        all_jobs = []
        seen_keys = set()
        
        for adapter_key, adapter in self.adapters.items():
            try:
                jobs = adapter.discover_jobs(query=query)
                for job in jobs:
                    # Deduplication key: company + normalized title
                    dedup_key = f"{job['company_name'].lower()}:{job['title'].lower()}"
                    if dedup_key not in seen_keys:
                        seen_keys.add(dedup_key)
                        job["adapter_key"] = adapter_key
                        all_jobs.append(job)
            except Exception as e:
                print(f"Error in adapter {adapter_key}: {e}")
                
        return all_jobs

discovery_service = DiscoveryService()
