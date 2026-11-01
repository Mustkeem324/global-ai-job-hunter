import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Index, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.state_machine import ApplicationStatus, ApplicationMode

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="candidate")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    profile = relationship("CandidateProfile", back_populates="user", uselist=False)
    applications = relationship("Application", back_populates="user")
    automation_policy = relationship("AutomationPolicy", back_populates="user", uselist=False)

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), default="Hyderabad / New Delhi, India")
    country = Column(String(100), default="India")
    headline = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    github_url = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    portfolio_url = Column(String(255), nullable=True)
    total_experience_months = Column(Integer, default=25)
    education_data = Column(JSON, default=list) # degrees, institutions, grades
    certifications_data = Column(JSON, default=list)
    projects_data = Column(JSON, default=list) # professional projects with descriptions & technologies
    work_authorization = Column(JSON, default=dict) # international remote eligibility, tax compliance
    uncertain_claims = Column(JSON, default=list) # ambiguous items needing candidate confirmation
    traceable_claims = Column(JSON, default=list) # full audit trail of evidence text spans
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="profile")
    experiences = relationship("ProfessionalExperience", back_populates="profile", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="profile", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="profile")

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False) # pdf, docx, txt, md
    file_size_bytes = Column(Integer, default=0)
    raw_text = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=False)
    parsed_at = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)

    profile = relationship("CandidateProfile", back_populates="resumes")
    versions = relationship("ResumeVersion", back_populates="resume", cascade="all, delete-orphan")

class ResumeVersion(Base):
    __tablename__ = "resume_versions"
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    version_tag = Column(String(100), nullable=False) # e.g. "Tailored_HTTPie_AI_FullStack"
    tailored_text = Column(Text, nullable=False)
    target_job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    resume = relationship("Resume", back_populates="versions")

class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False) # "AI/LLM", "Backend", "Frontend", "Cloud/Data"
    proficiency_level = Column(String(50), default="Advanced")
    evidence_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    profile = relationship("CandidateProfile", back_populates="skills")

class ProfessionalExperience(Base):
    __tablename__ = "professional_experiences"
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    company = Column(String(255), nullable=False)
    role_title = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    is_remote = Column(Boolean, default=True)
    start_date = Column(String(50), nullable=False)
    end_date = Column(String(50), default="Present")
    is_current = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    skills_used = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)

    profile = relationship("CandidateProfile", back_populates="experiences")

class JobSource(Base):
    __tablename__ = "job_sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False) # e.g. "Greenhouse", "Ashby", "Remotive"
    adapter_key = Column(String(100), nullable=False)
    base_url = Column(String(500), nullable=True)
    is_enabled = Column(Boolean, default=True)
    supports_auto_apply = Column(Boolean, default=False)
    last_discovered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    job_postings = relationship("JobPosting", back_populates="source")

class JobPosting(Base):
    __tablename__ = "job_postings"
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("job_sources.id"), nullable=True)
    source_job_id = Column(String(255), nullable=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    category = Column(String(100), default="Software Engineering")
    employment_type = Column(String(100), default="Contract") # Full-time, Contract, Freelance
    work_arrangement = Column(String(50), default="Remote") # Remote, Hybrid, Onsite
    country_eligibility = Column(String(100), default="Worldwide") # India confirmed, Worldwide, Restricted
    is_india_eligible = Column(Boolean, default=True)
    compensation_text = Column(String(255), default="Not disclosed")
    currency = Column(String(20), default="USD")
    min_comp = Column(Float, nullable=True)
    max_comp = Column(Float, nullable=True)
    required_experience = Column(String(255), default="2+ years")
    location = Column(String(255), default="Remote")
    application_url = Column(String(1000), nullable=False)
    description = Column(Text, nullable=False)
    company_website = Column(String(500), nullable=True)
    normalized_role = Column(String(255), nullable=True)
    required_skills = Column(JSON, default=list)
    preferred_skills = Column(JSON, default=list)
    location_evidence = Column(Text, nullable=True)
    verification_state = Column(String(50), default="VERIFIED_OPEN") # VERIFIED_OPEN, PROBABLY_OPEN, UNVERIFIED, EXPIRED, CLOSED
    application_capability = Column(String(50), default="USER_REVIEW_REQUIRED") # API_SUBMISSION_AUTHORIZED, AUTHORIZED_FORM_WORKFLOW, USER_REVIEW_REQUIRED, MANUAL_SUBMISSION_ONLY, UNSUPPORTED
    status = Column(String(50), default="Active") # Active, Expired, Removed
    posted_date = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("idx_company_title", "company_name", "title"),
    )

    source = relationship("JobSource", back_populates="job_postings")
    requirements = relationship("JobRequirement", back_populates="job_posting", cascade="all, delete-orphan")
    matches = relationship("JobMatch", back_populates="job_posting", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job_posting")

class CompanyRegistry(Base):
    __tablename__ = "company_registry"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), unique=True, nullable=False, index=True)
    official_website = Column(String(500), nullable=True)
    career_page = Column(String(500), nullable=True)
    ats_provider = Column(String(50), nullable=False) # Greenhouse, Lever, Ashby, Workable
    ats_board_identifier = Column(String(100), nullable=False, index=True)
    supported_locations = Column(JSON, default=list)
    source_status = Column(String(50), default="Active") # Active, Deprecated, Protected
    last_successful_scan = Column(DateTime, nullable=True)
    latest_synchronization_status = Column(String(50), default="Pending")
    last_verification_timestamp = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)

class SearchQueryRecord(Base):
    __tablename__ = "search_queries"
    id = Column(Integer, primary_key=True, index=True)
    seed_keyword = Column(String(100), nullable=False)
    expanded_terms = Column(JSON, default=list)
    last_executed_at = Column(DateTime, default=utcnow)
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

class JobRequirement(Base):
    __tablename__ = "job_requirements"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    requirement_text = Column(Text, nullable=False)
    is_mandatory = Column(Boolean, default=True)
    category = Column(String(50), default="Skill") # Skill, Education, Experience, Location
    created_at = Column(DateTime, default=utcnow)

    job_posting = relationship("JobPosting", back_populates="requirements")

class JobMatch(Base):
    __tablename__ = "job_matches"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    overall_score = Column(Float, nullable=False) # 0 to 100
    skills_score = Column(Float, nullable=False) # max 30
    experience_score = Column(Float, nullable=False) # max 20
    eligibility_score = Column(Float, nullable=False) # max 20
    education_score = Column(Float, nullable=False) # max 10
    preferences_score = Column(Float, nullable=False) # max 10
    recency_score = Column(Float, nullable=False) # max 10
    match_tier = Column(String(50), nullable=False) # Highly suitable, Suitable, Review required, Not suitable
    is_india_eligible = Column(Boolean, default=True)
    explanation_json = Column(JSON, default=dict) # breakdown and evidence
    is_eligible_india = Column(Boolean, default=True)
    calculated_at = Column(DateTime, default=utcnow)

    job_posting = relationship("JobPosting", back_populates="matches")

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    mode = Column(SQLEnum(ApplicationMode), default=ApplicationMode.MODE_B_APPROVAL)
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.DISCOVERED, index=True)
    idempotency_key = Column(String(255), unique=True, nullable=False)
    match_score = Column(Float, default=0.0)
    tailored_headline = Column(String(500), nullable=True)
    tailored_summary = Column(Text, nullable=True)
    cover_letter = Column(Text, nullable=True)
    answers_payload = Column(JSON, default=dict)
    application_method = Column(String(100), default="USER_REVIEW_REQUIRED")
    resume_version = Column(String(255), default="Primary Resume")
    failure_reason = Column(Text, nullable=True)
    confirmation_receipt_id = Column(String(255), nullable=True, index=True)
    applied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="applications")
    job_posting = relationship("JobPosting", back_populates="applications")
    documents = relationship("ApplicationDocument", back_populates="application", cascade="all, delete-orphan")
    events = relationship("ApplicationEvent", back_populates="application", cascade="all, delete-orphan")
    evidence = relationship("SubmissionEvidence", back_populates="application", uselist=False, cascade="all, delete-orphan")
    approval_request = relationship("ApprovalRequest", back_populates="application", uselist=False, cascade="all, delete-orphan")

class ApplicationDocument(Base):
    __tablename__ = "application_documents"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    document_type = Column(String(50), nullable=False) # resume, cover_letter, portfolio_snippet
    title = Column(String(255), nullable=False)
    content_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    application = relationship("Application", back_populates="documents")

class ApplicationEvent(Base):
    __tablename__ = "application_events"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    from_status = Column(String(50), nullable=False)
    to_status = Column(String(50), nullable=False)
    trigger_source = Column(String(100), default="system") # system, user, worker
    message = Column(Text, nullable=True)
    payload = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=utcnow)

    application = relationship("Application", back_populates="events")

class SubmissionEvidence(Base):
    __tablename__ = "submission_evidence"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, nullable=False)
    confirmation_id = Column(String(255), nullable=False)
    confirmation_method = Column(String(100), nullable=False) # api_response, confirmation_page, acknowledgment_email
    raw_evidence_text = Column(Text, nullable=False)
    verified = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=utcnow)

    application = relationship("Application", back_populates="evidence")

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, nullable=False)
    status = Column(String(50), default="PENDING") # PENDING, APPROVED, REJECTED, EDITED
    user_decision_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    application = relationship("Application", back_populates="approval_request")

class NotificationEvent(Base):
    __tablename__ = "notification_events"
    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String(50), default="TELEGRAM") # TELEGRAM, EMAIL, IN_APP
    category = Column(String(100), nullable=False) # NEW_HIGH_MATCH, READY_FOR_APPROVAL, SUBMITTED_CONFIRMED, SUBMISSION_UNCERTAIN
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

class AutomationPolicy(Base):
    __tablename__ = "automation_policies"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    auto_apply_enabled = Column(Boolean, default=False)
    approval_required = Column(Boolean, default=True)
    min_match_score = Column(Integer, default=80)
    max_daily_applications = Column(Integer, default=10)
    allowed_sources = Column(JSON, default=list) # e.g. ["mock_ats", "greenhouse_sandbox"]
    cooling_off_days = Column(Integer, default=30)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="automation_policy")

class ScheduledRun(Base):
    __tablename__ = "scheduled_runs"
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(100), nullable=False)
    status = Column(String(50), default="SUCCESS") # SUCCESS, FAILED, RUNNING
    jobs_discovered = Column(Integer, default=0)
    matches_calculated = Column(Integer, default=0)
    applications_processed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)

class AgentRun(Base):
    __tablename__ = "agent_runs"
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    status = Column(String(50), default="COMPLETED")
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)
    actor = Column(String(100), default="system")
    target = Column(String(255), nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)

class IntegrationCredential(Base):
    __tablename__ = "integration_credentials"
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(100), unique=True, nullable=False)
    encrypted_credentials = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

class TelegramCallbackAction(Base):
    __tablename__ = "telegram_callback_actions"
    id = Column(Integer, primary_key=True, index=True)
    callback_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    target_id = Column(String(100), nullable=False)
    payload = Column(JSON, default=dict)
    executed_at = Column(DateTime, default=utcnow)

class AutomationSetting(Base):
    __tablename__ = "automation_settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

# =========================================================
# PHASE 3 & 4 DATABASE MODELS
# =========================================================

class CandidateFact(Base):
    __tablename__ = "candidate_facts"
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    category = Column(String(100), nullable=False) # education, experience, skill, project, claim
    fact_key = Column(String(255), nullable=False)
    fact_value = Column(Text, nullable=False)
    source_document = Column(String(255), default="resume.pdf")
    source_location = Column(String(255), default="Page 1")
    confidence = Column(Float, default=1.0)
    user_verified = Column(Boolean, default=True)
    last_confirmed_at = Column(DateTime, default=utcnow)

class TailoredResumeVariant(Base):
    __tablename__ = "tailored_resume_variants"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    variant_type = Column(String(100), nullable=False) # AI_TRAINING, LLM_EVALUATION, AI_CODING, FULLSTACK, GENERATIVE_AI, GENERAL_SWE
    title = Column(String(255), nullable=False)
    content_text = Column(Text, nullable=False)
    pdf_path = Column(String(500), nullable=True)
    docx_path = Column(String(500), nullable=True)
    validation_status = Column(String(50), default="VALIDATED") # VALIDATED, REJECTED_UNSUPPORTED_CLAIMS
    source_claims = Column(JSON, default=list)
    unsupported_claims = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)

class FormSchema(Base):
    __tablename__ = "form_schemas"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    form_url = Column(String(500), nullable=False)
    fields_json = Column(JSON, default=list)
    discovered_at = Column(DateTime, default=utcnow)

class JobPriority(Base):
    __tablename__ = "job_priorities"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), unique=True, nullable=False)
    priority_tier = Column(String(50), nullable=False) # PRIORITY_A, PRIORITY_B, PRIORITY_C, PRIORITY_D
    priority_score = Column(Float, nullable=False) # 0 to 100
    compatibility_score = Column(Float, default=0.0)
    eligibility_score = Column(Float, default=0.0)
    preference_score = Column(Float, default=0.0)
    freshness_score = Column(Float, default=0.0)
    effort_score = Column(Float, default=0.0)
    feedback_adjustment = Column(Float, default=0.0)
    explanation_json = Column(JSON, default=dict)
    calculated_at = Column(DateTime, default=utcnow)

class UserFeedback(Base):
    __tablename__ = "user_feedbacks"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    action = Column(String(50), nullable=False) # SAVED, SKIPPED, APPROVED, REJECTED, APPLIED
    role_category = Column(String(100), nullable=True)
    affinity_delta = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utcnow)

class RecruiterMessage(Base):
    __tablename__ = "recruiter_messages"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    message_id = Column(String(255), unique=True, nullable=False)
    thread_id = Column(String(255), nullable=True)
    sender_email = Column(String(255), nullable=False)
    sender_domain = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body_text = Column(Text, nullable=False)
    received_at = Column(DateTime, default=utcnow)
    classification = Column(String(100), default="UNCERTAIN")
    confidence = Column(Float, default=0.0)
    matched_criteria = Column(JSON, default=dict)
    requires_action = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)

class RecruiterEvent(Base):
    __tablename__ = "recruiter_events"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("recruiter_messages.id"), nullable=False)
    event_type = Column(String(100), nullable=False) # INTERVIEW_INVITE, ASSESSMENT_DEADLINE, OFFER, REJECTION
    event_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

class FollowupDraft(Base):
    __tablename__ = "followup_drafts"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    reason = Column(String(255), nullable=False)
    suggested_send_date = Column(DateTime, default=utcnow)
    subject = Column(String(500), nullable=False)
    body_text = Column(Text, nullable=False)
    status = Column(String(50), default="DRAFTED") # DRAFTED, APPROVED, SENT, CANCELLED
    approved_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    application = relationship("Application")

class SourceHealth(Base):
    __tablename__ = "source_health"
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(100), unique=True, nullable=False)
    status = Column(String(50), default="HEALTHY") # HEALTHY, DEGRADED, RATE_LIMITED, DOWN
    last_sync_at = Column(DateTime, default=utcnow)
    error_count = Column(Integer, default=0)
    circuit_breaker_open = Column(Boolean, default=False)
    avg_latency_ms = Column(Float, default=0.0)

class SourceSyncCursor(Base):
    __tablename__ = "source_sync_cursors"
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(100), unique=True, nullable=False)
    cursor_value = Column(String(500), nullable=False)
    last_updated_at = Column(DateTime, default=utcnow)

class CostUsage(Base):
    __tablename__ = "cost_usage"
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(100), nullable=False) # gemini, playwright, search_api
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    date_str = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=utcnow)

class CloudHealthCheck(Base):
    __tablename__ = "cloud_health_checks"
    id = Column(Integer, primary_key=True, index=True)
    component = Column(String(100), nullable=False) # database, redis, worker, telegram, scheduler
    status = Column(String(50), default="HEALTHY")
    details_json = Column(JSON, default=dict)
    checked_at = Column(DateTime, default=utcnow)

class BackupRun(Base):
    __tablename__ = "backup_runs"
    id = Column(Integer, primary_key=True, index=True)
    backup_type = Column(String(50), default="FULL_DB")
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    status = Column(String(50), default="SUCCESS")
    verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

# =========================================================
# PHASE 5: BULK JOB APPLICATION & BATCH ORCHESTRATION MODELS
# =========================================================

class ApplicationBatch(Base):
    __tablename__ = "application_batches"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="CREATED", index=True) 
    # CREATED, PREFLIGHT_RUNNING, PREFLIGHT_COMPLETE, AWAITING_AUTHORIZATION, AUTHORIZED, RUNNING, PAUSED, COMPLETED, COMPLETED_WITH_EXCEPTIONS, FAILED, CANCELLED
    target_size = Column(Integer, default=25)
    total_jobs = Column(Integer, default=0)
    eligible_jobs = Column(Integer, default=0)
    auto_submittable_jobs = Column(Integer, default=0)
    manual_review_jobs = Column(Integer, default=0)
    submitted_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    completed_at = Column(DateTime, nullable=True)

    items = relationship("ApplicationBatchItem", back_populates="batch", cascade="all, delete-orphan")
    authorizations = relationship("BatchAuthorization", back_populates="batch", cascade="all, delete-orphan")
    progress_snapshots = relationship("BatchProgressSnapshot", back_populates="batch", cascade="all, delete-orphan")
    events = relationship("BatchExecutionEvent", back_populates="batch", cascade="all, delete-orphan")

class ApplicationBatchItem(Base):
    __tablename__ = "application_batch_items"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("application_batches.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    status = Column(String(50), default="SELECTED", index=True)
    # SELECTED, PREFLIGHT_PASSED, EXCLUDED, AUTHORIZED, SUBMITTING, SUBMITTED_CONFIRMED, MANUAL_REVIEW_REQUIRED, FAILED, SKIPPED
    match_score = Column(Float, default=0.0)
    capability = Column(String(100), default="MANUAL_REVIEW_REQUIRED")
    exclusion_reason = Column(String(255), nullable=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    confirmation_receipt_id = Column(String(255), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    batch = relationship("ApplicationBatch", back_populates="items")
    job = relationship("JobPosting")
    application = relationship("Application")

class BatchAuthorization(Base):
    __tablename__ = "batch_authorizations"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("application_batches.id"), nullable=False)
    authorized_by_telegram_id = Column(String(100), nullable=False)
    authorized_at = Column(DateTime, default=utcnow)
    policy_snapshot_json = Column(JSON, default=dict)
    items_count = Column(Integer, default=0)

    batch = relationship("ApplicationBatch", back_populates="authorizations")

class BatchProgressSnapshot(Base):
    __tablename__ = "batch_progress_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("application_batches.id"), nullable=False)
    status = Column(String(50), default="RUNNING")
    confirmed_count = Column(Integer, default=0)
    processing_count = Column(Integer, default=0)
    awaiting_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    manual_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=utcnow)

    batch = relationship("ApplicationBatch", back_populates="progress_snapshots")

class BatchExecutionEvent(Base):
    __tablename__ = "batch_execution_events"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("application_batches.id"), nullable=False)
    item_id = Column(Integer, nullable=True)
    event_type = Column(String(100), nullable=False) # STARTED, SUBMITTED, PREPARED, FAILED, PAUSED, RESUMED, COMPLETED
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utcnow)

    batch = relationship("ApplicationBatch", back_populates="events")

# =========================================================
# PHASE 6: RECRUITER INTELLIGENCE, CRM & INTERVIEW MODELS
# =========================================================

class RecruiterContact(Base):
    __tablename__ = "recruiter_contacts"
    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(String(100), unique=True, index=True, nullable=False)
    company = Column(String(255), nullable=False, index=True)
    job_position = Column(String(255), nullable=True)
    contact_name = Column(String(255), nullable=False)
    professional_title = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    communication_channel = Column(String(50), default="EMAIL") # EMAIL, LINKEDIN, PORTAL
    follow_up_status = Column(String(50), default="IDLE") # IDLE, FOLLOWUP_DRAFTED, FOLLOWUP_SENT, SNOOZED, OPTED_OUT
    next_permitted_action = Column(String(100), default="AWAIT_REPLY")
    communication_restrictions = Column(String(255), nullable=True) # e.g. "Do not contact before 14 days"
    is_no_reply = Column(Boolean, default=False)
    first_interaction_at = Column(DateTime, default=utcnow)
    last_interaction_at = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    interactions = relationship("RecruiterInteraction", back_populates="recruiter_contact", cascade="all, delete-orphan")
    interviews = relationship("InterviewEvent", back_populates="recruiter_contact")
    assessments = relationship("AssessmentEvent", back_populates="recruiter_contact")
    offers = relationship("OfferRecord", back_populates="recruiter_contact")

class RecruiterInteraction(Base):
    __tablename__ = "recruiter_interactions"
    id = Column(Integer, primary_key=True, index=True)
    recruiter_contact_id = Column(Integer, ForeignKey("recruiter_contacts.id"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    interaction_type = Column(String(100), nullable=False) # EMAIL_RECEIVED, EMAIL_SENT, INTERVIEW_SCHEDULED, REJECTION_RECEIVED, OFFER_RECEIVED
    direction = Column(String(20), default="INBOUND") # INBOUND, OUTBOUND
    subject = Column(String(500), nullable=True)
    body_summary = Column(Text, nullable=True)
    message_id = Column(String(255), nullable=True, index=True)
    thread_id = Column(String(255), nullable=True, index=True)
    occurred_at = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)

    recruiter_contact = relationship("RecruiterContact", back_populates="interactions")
    application = relationship("Application")

class RecruiterMessageMatch(Base):
    __tablename__ = "recruiter_message_matches"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(255), nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    recruiter_contact_id = Column(Integer, ForeignKey("recruiter_contacts.id"), nullable=True)
    match_type = Column(String(50), nullable=False) # EXACT_RECEIPT_ID, THREAD_ID, COMPANY_TITLE_DOMAIN, AMBIGUOUS
    confidence = Column(Float, default=0.0)
    evidence_notes = Column(Text, nullable=True)
    status = Column(String(50), default="CONFIRMED") # CONFIRMED, UNDER_REVIEW, DISMISSED
    created_at = Column(DateTime, default=utcnow)

    application = relationship("Application")
    recruiter_contact = relationship("RecruiterContact")

class FollowupRecommendation(Base):
    __tablename__ = "followup_recommendations"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    recruiter_contact_id = Column(Integer, ForeignKey("recruiter_contacts.id"), nullable=True)
    recommendation_type = Column(String(50), nullable=False) # STATUS_FOLLOWUP, QUESTION_RESPONSE, ASSESSMENT_FOLLOWUP, INTERVIEW_CONFIRMATION, OFFER_DISCUSSION
    priority = Column(String(20), default="MEDIUM") # HIGH, MEDIUM, LOW
    suggested_date = Column(DateTime, nullable=False)
    trigger_reason = Column(String(500), nullable=False)
    status = Column(String(50), default="PENDING") # PENDING, APPROVED, REJECTED, SNOOZED, EXPIRED
    created_at = Column(DateTime, default=utcnow)

    application = relationship("Application")
    recruiter_contact = relationship("RecruiterContact")

class FollowupApproval(Base):
    __tablename__ = "followup_approvals"
    id = Column(Integer, primary_key=True, index=True)
    followup_draft_id = Column(Integer, ForeignKey("followup_drafts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False) # APPROVED, REJECTED, SNOOZED, EDITED
    approved_by = Column(String(100), default="user_telegram")
    modified_subject = Column(String(500), nullable=True)
    modified_body = Column(Text, nullable=True)
    approved_at = Column(DateTime, default=utcnow)

    draft = relationship("FollowupDraft")
    user = relationship("User")

class InterviewEvent(Base):
    __tablename__ = "interview_events"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    recruiter_contact_id = Column(Integer, ForeignKey("recruiter_contacts.id"), nullable=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True)
    title = Column(String(255), nullable=False)
    original_datetime_str = Column(String(100), nullable=True)
    original_timezone = Column(String(50), default="UTC")
    scheduled_at_kolkata = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=45)
    meeting_platform = Column(String(50), default="GOOGLE_MEET") # GOOGLE_MEET, ZOOM, TEAMS, CALENDLY, PHONE, IN_PERSON
    meeting_url = Column(String(500), nullable=True)
    tentative_or_confirmed = Column(String(20), default="CONFIRMED") # CONFIRMED, TENTATIVE
    interviewer_names = Column(String(255), nullable=True)
    documents_requested = Column(Text, nullable=True)
    preparation_instructions = Column(Text, nullable=True)
    google_calendar_event_id = Column(String(255), nullable=True)
    google_calendar_synced = Column(Boolean, default=False)
    status = Column(String(50), default="SCHEDULED") # SCHEDULED, RESCHEDULED, COMPLETED, CANCELLED
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    application = relationship("Application")
    recruiter_contact = relationship("RecruiterContact", back_populates="interviews")
    reminders = relationship("InterviewReminder", back_populates="interview", cascade="all, delete-orphan")

class InterviewReminder(Base):
    __tablename__ = "interview_reminders"
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interview_events.id"), nullable=False)
    reminder_type = Column(String(50), nullable=False) # 24_HOURS, 2_HOURS, 30_MINUTES
    scheduled_for = Column(DateTime, nullable=False, index=True)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    notification_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    interview = relationship("InterviewEvent", back_populates="reminders")

class AssessmentEvent(Base):
    __tablename__ = "assessment_events"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    recruiter_contact_id = Column(Integer, ForeignKey("recruiter_contacts.id"), nullable=True)
    assessment_title = Column(String(255), nullable=False)
    platform = Column(String(100), default="HACKERRANK") # HACKERRANK, CODESIGNAL, TAKE_HOME, OTHER
    test_url = Column(String(500), nullable=True)
    deadline_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    instructions = Column(Text, nullable=True)
    status = Column(String(50), default="PENDING") # PENDING, IN_PROGRESS, COMPLETED, EXPIRED
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    application = relationship("Application")
    recruiter_contact = relationship("RecruiterContact", back_populates="assessments")

class OfferRecord(Base):
    __tablename__ = "offer_records"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    recruiter_contact_id = Column(Integer, ForeignKey("recruiter_contacts.id"), nullable=True)
    company = Column(String(255), nullable=False)
    position = Column(String(255), nullable=False)
    base_salary = Column(String(100), nullable=True)
    currency = Column(String(10), default="USD")
    equity_details = Column(String(255), nullable=True)
    signing_bonus = Column(String(100), nullable=True)
    deadline_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="RECEIVED") # RECEIVED, UNDER_REVIEW, ACCEPTED, DECLINED, EXPIRED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    application = relationship("Application")
    recruiter_contact = relationship("RecruiterContact", back_populates="offers")

class ApplicationConversionEvent(Base):
    __tablename__ = "application_conversion_events"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    from_status = Column(String(50), nullable=False)
    to_status = Column(String(50), nullable=False)
    trigger_source = Column(String(100), default="RECRUITER_EMAIL") # RECRUITER_EMAIL, USER_INPUT, AGENT_ACTION, SYSTEM
    event_details = Column(JSON, default=dict)
    occurred_at = Column(DateTime, default=utcnow)

    application = relationship("Application")

class ResumeExperiment(Base):
    __tablename__ = "resume_experiments"
    id = Column(Integer, primary_key=True, index=True)
    experiment_name = Column(String(255), nullable=False)
    resume_version_id = Column(Integer, ForeignKey("resume_versions.id"), nullable=True)
    role_category = Column(String(100), nullable=False)
    total_applications = Column(Integer, default=0)
    interviews_received = Column(Integer, default=0)
    offers_received = Column(Integer, default=0)
    response_rate = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), nullable=False) # DiscoveryAgent, MatchingAgent, ApplicationAgent, etc.
    permission_scope = Column(String(100), nullable=False)
    action_taken = Column(String(255), nullable=False)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0)
    timestamp = Column(DateTime, default=utcnow)

class RecommendationEvidence(Base):
    __tablename__ = "recommendation_evidence"
    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(String(100), nullable=False, index=True)
    evidence_type = Column(String(100), nullable=False) # FUNNEL_CONVERSION, ROLE_PERFORMANCE, ATS_SUCCESS_RATE
    metric_key = Column(String(100), nullable=False)
    sample_size = Column(Integer, default=0)
    numerator = Column(Integer, default=0)
    denominator = Column(Integer, default=0)
    observation_text = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utcnow)

