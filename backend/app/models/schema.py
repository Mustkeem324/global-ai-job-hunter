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
