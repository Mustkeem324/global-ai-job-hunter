import uuid
import datetime
from typing import Dict, Any, Optional
from app.core.state_machine import ApplicationStatus, ApplicationMode, ApplicationStateMachine

class ApplicationExecutorService:
    def evaluate_mode(self, job_dict: Dict[str, Any], policy_dict: Dict[str, Any]) -> ApplicationMode:
        """
        Determine execution mode based on job source capability and user policy.
        """
        source_key = job_dict.get("adapter_key", "unknown")
        allowed_auto_sources = policy_dict.get("allowed_sources", [])
        auto_enabled = policy_dict.get("auto_apply_enabled", False)
        approval_required = policy_dict.get("approval_required", True)

        # Mode A check: explicitly enabled, source in allowlist, approval not strictly forced
        if auto_enabled and source_key in allowed_auto_sources and not approval_required:
            return ApplicationMode.MODE_A_AUTO
        
        # Mode B check: source supports programmatic submission but user requires approval
        if source_key in ("mock_ats", "greenhouse_sandbox", "direct_api"):
            return ApplicationMode.MODE_B_APPROVAL
        
        # Mode C: default safe assisted mode for web applications
        return ApplicationMode.MODE_C_ASSISTED

    def submit_application(
        self,
        application_id: int,
        job_dict: Dict[str, Any],
        candidate_dict: Dict[str, Any],
        documents_dict: Dict[str, Any],
        mode: ApplicationMode
    ) -> Dict[str, Any]:
        """
        Execute application submission with strict verification and confirmation evidence.
        """
        source_key = job_dict.get("adapter_key", "local_catalog")
        
        # For Mock / Authorized Sandbox ATS
        if source_key == "mock_ats":
            # Deterministic, authoritative submission confirmation
            confirmation_id = f"CONF-{uuid.uuid4().hex[:10].upper()}"
            evidence = {
                "confirmation_id": confirmation_id,
                "confirmation_method": "authorized_sandbox_api_response",
                "raw_evidence_text": f"HTTP 201 Created: Application {confirmation_id} accepted by {job_dict.get('company_name')}.",
                "verified": True,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            return {
                "status": ApplicationStatus.SUBMITTED_CONFIRMED,
                "evidence": evidence,
                "message": f"Successfully submitted and verified with confirmation ID {confirmation_id}."
            }
            
        elif mode == ApplicationMode.MODE_C_ASSISTED:
            # Assisted mode: Form payload prepared for user-controlled manual submission
            return {
                "status": ApplicationStatus.PREPARED,
                "evidence": None,
                "message": "Application documents and tailored answers are prepared for assisted manual submission."
            }
            
        else:
            # If external endpoint cannot be authoritatively verified
            return {
                "status": ApplicationStatus.SUBMISSION_UNCERTAIN,
                "evidence": None,
                "message": "Submission status uncertain. Direct automated submission is not authorized for this platform."
            }

application_executor = ApplicationExecutorService()
