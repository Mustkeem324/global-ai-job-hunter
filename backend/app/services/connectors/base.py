from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseJobConnector(ABC):
    """
    Common Interface for Every Global Job Discovery Connector (Phase 2 Standard)
    """
    def __init__(self, name: str, source_key: str):
        self.name = name
        self.source_key = source_key

    @abstractmethod
    def search_jobs(self, query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute vacancy search and return a list of normalized canonical job objects."""
        pass

    @abstractmethod
    def fetch_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full job posting details including comprehensive description and requirements."""
        pass

    @abstractmethod
    def verify_job(self, job_url: str) -> bool:
        """Verify if a vacancy URL is currently open and responding with HTTP 200."""
        pass

    @abstractmethod
    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Convert provider-specific payload into standard Canonical Job Object."""
        pass

    @abstractmethod
    def get_application_url(self, raw_job: Dict[str, Any]) -> str:
        """Extract verified official destination URL for candidate submission."""
        pass

    @abstractmethod
    def get_application_capabilities(self) -> Dict[str, Any]:
        """
        Return source application submission capability classification:
        API_SUBMISSION_AUTHORIZED, AUTHORIZED_FORM_WORKFLOW, USER_REVIEW_REQUIRED, 
        MANUAL_SUBMISSION_ONLY, or UNSUPPORTED.
        """
        pass

    @abstractmethod
    def get_source_permissions(self) -> Dict[str, Any]:
        """Return legal/API authorization terms, authentication requirements, and compliance policies."""
        pass

    @abstractmethod
    def get_rate_limit_policy(self) -> Dict[str, Any]:
        """Return rate limit quota, recommended backoff, and concurrency constraints."""
        pass
