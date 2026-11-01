import time
import datetime
from typing import Dict, Any, List, Optional

from app.core.database import SessionLocal
from app.models.schema import AgentExecutionLog

class AgentSecurityException(Exception):
    """Raised when an agent attempts an action outside its narrow granted scope."""
    pass

class BaseSpecializedAgent:
    def __init__(self, agent_name: str, granted_scopes: List[str]):
        self.agent_name = agent_name
        self.granted_scopes = set(granted_scopes)

    def verify_permission(self, required_scope: str):
        if required_scope not in self.granted_scopes:
            raise AgentSecurityException(
                f"Security Boundary Violation: Agent '{self.agent_name}' with scopes {list(self.granted_scopes)} "
                f"attempted unauthorized action requiring scope '{required_scope}'."
            )

    def log_execution(
        self,
        action: str,
        scope: str,
        input_data: Any,
        output_data: Any,
        success: bool = True,
        error_msg: Optional[str] = None,
        latency_ms: int = 0
    ):
        db = SessionLocal()
        try:
            log_entry = AgentExecutionLog(
                agent_name=self.agent_name,
                permission_scope=scope,
                action_taken=action,
                input_summary=str(input_data)[:300],
                output_summary=str(output_data)[:300] if output_data else None,
                success=success,
                error_message=error_msg,
                latency_ms=latency_ms,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            db.add(log_entry)
            db.commit()
        except Exception:
            pass
        finally:
            db.close()

# 1. Job Discovery Agent
class JobDiscoveryAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__("DiscoveryAgent", ["READ_JOBS_DISCOVERY"])

    def discover_jobs(self, query: str = ""):
        self.verify_permission("READ_JOBS_DISCOVERY")
        t0 = time.time()
        # Cannot send email or submit applications
        from app.services.discovery_service import discovery_service
        jobs = discovery_service.discover_jobs(query=query)
        latency = int((time.time() - t0) * 1000)
        self.log_execution("discover_jobs", "READ_JOBS_DISCOVERY", query, f"Found {len(jobs)} jobs", True, latency_ms=latency)
        return jobs

# 2. Matching Agent
class ResumeMatchingAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__("MatchingAgent", ["READ_JOBS_RESUMES"])

    def score_job(self, job_dict: Dict[str, Any]):
        self.verify_permission("READ_JOBS_RESUMES")
        t0 = time.time()
        from app.services.matching_engine import matching_engine
        score = matching_engine.calculate_match_score(job_dict)
        latency = int((time.time() - t0) * 1000)
        self.log_execution("score_job", "READ_JOBS_RESUMES", job_dict.get("title"), f"Score: {score}", True, latency_ms=latency)
        return score

# 3. Application Agent
class ApplicationExecutionAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__("ApplicationAgent", ["EXECUTE_SUBMISSION"])

    def execute_submission(self, application_id: int):
        self.verify_permission("EXECUTE_SUBMISSION")
        t0 = time.time()
        from app.services.application_executor import application_executor
        result = application_executor.execute_application(application_id)
        latency = int((time.time() - t0) * 1000)
        self.log_execution("execute_submission", "EXECUTE_SUBMISSION", f"App #{application_id}", result.get("status"), result.get("success", False), latency_ms=latency)
        return result

# 4. Recruiter Intelligence Agent
class RecruiterIntelligenceAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__("RecruiterIntelligenceAgent", ["GMAIL_READ_CLASSIFY"])

    def process_email(self, message_id: str, sender: str, subject: str, body: str, thread_id: Optional[str] = None):
        self.verify_permission("GMAIL_READ_CLASSIFY")
        t0 = time.time()
        from app.services.gmail_service import gmail_service
        res = gmail_service.process_incoming_email(message_id, sender, subject, body, thread_id)
        latency = int((time.time() - t0) * 1000)
        self.log_execution("process_email", "GMAIL_READ_CLASSIFY", f"{sender}: {subject}", res.get("classification"), True, latency_ms=latency)
        return res

# 5. Follow-Up Agent
class FollowUpAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__("FollowUpAgent", ["DRAFT_FOLLOWUPS", "APPROVE_FOLLOWUPS"])

    def create_draft(self, recommendation_id: int):
        self.verify_permission("DRAFT_FOLLOWUPS")
        t0 = time.time()
        from app.services.followup_agent import followup_agent
        res = followup_agent.generate_draft_for_recommendation(recommendation_id)
        latency = int((time.time() - t0) * 1000)
        self.log_execution("create_draft", "DRAFT_FOLLOWUPS", f"Rec #{recommendation_id}", res.get("status"), res.get("success", False), latency_ms=latency)
        return res

# 6. Interview Agent
class InterviewAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__("InterviewAgent", ["INTERVIEW_CALENDAR_PREP"])

    def generate_prep(self, application_id: int, mode: str = "technical_qa"):
        self.verify_permission("INTERVIEW_CALENDAR_PREP")
        t0 = time.time()
        from app.services.interview_intelligence_service import interview_intelligence_service
        res = interview_intelligence_service.generate_interview_preparation(application_id, mode)
        latency = int((time.time() - t0) * 1000)
        self.log_execution("generate_prep", "INTERVIEW_CALENDAR_PREP", f"App #{application_id}", res.get("domain"), res.get("success", False), latency_ms=latency)
        return res

# 7. Analytics Agent
class AnalyticsAgent(BaseSpecializedAgent):
    def __init__(self):
        super().__init__("AnalyticsAgent", ["READ_ANALYTICS"])

    def get_funnel(self):
        self.verify_permission("READ_ANALYTICS")
        t0 = time.time()
        from app.services.recruiter_analytics_service import recruiter_analytics
        res = recruiter_analytics.calculate_funnel_metrics()
        latency = int((time.time() - t0) * 1000)
        self.log_execution("get_funnel", "READ_ANALYTICS", "funnel_metrics", f"{res.get('confirmed_submitted')} submissions", True, latency_ms=latency)
        return res

# 8. Supervisor Agent
class MultiAgentSupervisor:
    """Coordinates specialized agent execution and validates security scopes."""
    def __init__(self):
        self.discovery = JobDiscoveryAgent()
        self.matching = ResumeMatchingAgent()
        self.application = ApplicationExecutionAgent()
        self.recruiter_intelligence = RecruiterIntelligenceAgent()
        self.followup = FollowUpAgent()
        self.interview = InterviewAgent()
        self.analytics = AnalyticsAgent()

multi_agent_supervisor = MultiAgentSupervisor()
