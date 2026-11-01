from typing import Dict, Any, Optional
from app.core.state_machine import ApplicationCapability
from app.core.config import settings

class ApplicationCapabilityDetector:
    """
    Phase 2 Section 5: Application Capability Detector
    Inspects vacancy source, employer endpoint, credentials, and user policy
    to determine the exact permitted submission capability.
    Never assumes job-listing access implies submission access.
    """

    def detect_capability(self, job_dict: Dict[str, Any]) -> ApplicationCapability:
        source_key = (job_dict.get("source_id") or job_dict.get("adapter_key") or "").lower()
        app_url = job_dict.get("application_url", "")

        # 1. Check for dead or missing link
        if not app_url or not app_url.startswith("http"):
            return ApplicationCapability.UNSUPPORTED

        # 2. Authorized Mock / Sandbox ATS (Authorized API)
        if "mock_ats" in source_key or "sandbox" in source_key:
            return ApplicationCapability.AUTHORIZED_API_SUBMISSION

        # 3. Authorized direct allowlist from configuration
        allowed_sources = [s.strip().lower() for s in settings.AUTHORIZED_APPLICATION_SOURCES.split(",")]
        if source_key in allowed_sources and settings.AUTO_APPLY_ENABLED:
            return ApplicationCapability.AUTHORIZED_API_SUBMISSION

        # 4. Greenhouse / Lever / Ashby public boards
        # They publish open vacancies publicly, but submission APIs require employer-issued secret keys.
        if any(ats in source_key for ats in ("greenhouse", "lever", "ashby")):
            return ApplicationCapability.MANUAL_REVIEW_REQUIRED

        # 5. Remote Job Aggregators (Himalayas, Jobicy, Remotive, Arbeitnow)
        # Require candidate routing through canonical destination link with document preparation
        if any(agg in source_key for agg in ("himalayas", "jobicy", "remotive", "arbeitnow", "catalog")):
            return ApplicationCapability.EXTERNAL_APPLICATION_ONLY

        # 6. Default safe state
        return ApplicationCapability.MANUAL_REVIEW_REQUIRED

    def get_capability_explanation(self, capability: ApplicationCapability) -> str:
        explanations = {
            ApplicationCapability.AUTHORIZED_API_SUBMISSION: (
                "Verified direct programmatic API endpoint. Automatic one-click submission permitted under active policy."
            ),
            ApplicationCapability.AUTHORIZED_BROWSER_SUBMISSION: (
                "Permitted browser form automation workflow under user supervision."
            ),
            ApplicationCapability.MANUAL_REVIEW_REQUIRED: (
                "Public ATS board. Direct submission API requires employer API key. Tailored documents prepared for 1-click candidate review and assisted submission."
            ),
            ApplicationCapability.EXTERNAL_APPLICATION_ONLY: (
                "Remote network partner portal. Direct candidate link with tailored application documents prepared."
            ),
            ApplicationCapability.UNSUPPORTED: (
                "Platform endpoint unsupported or link expired. Manual inspection required."
            )
        }
        return explanations.get(capability, "Application capability under evaluation.")

capability_detector = ApplicationCapabilityDetector()
