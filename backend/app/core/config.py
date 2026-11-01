import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Global Job Hunter AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Storage & Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:////home/nx-pro/global-ai-job-hunter/backend/job_hunter.db"
    )
    RESUME_FOLDER: str = os.getenv("RESUME_FOLDER", "/home/nx-pro")
    STORAGE_DIR: str = os.getenv(
        "STORAGE_DIR", 
        "/home/nx-pro/global-ai-job-hunter/backend/storage"
    )
    
    # Security & API
    SECRET_KEY: str = os.getenv("SECRET_KEY", "global-job-hunter-ai-secret-key-324-secure")
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Telegram Notifications
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    TELEGRAM_OWNER_ID: str = os.getenv("TELEGRAM_OWNER_ID", "")
    TELEGRAM_ENABLED: bool = os.getenv("TELEGRAM_ENABLED", "true").lower() in ("true", "1")
    
    # AI Engine
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gemini-2.5-flash")
    
    # Application & Matching Policies
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata")
    DEFAULT_COUNTRY: str = os.getenv("DEFAULT_COUNTRY", "IN")
    ALLOW_WORLDWIDE_REMOTE: bool = os.getenv("ALLOW_WORLDWIDE_REMOTE", "true").lower() in ("true", "1")
    RESTRICT_TO_INDIA_ELIGIBLE: bool = os.getenv("RESTRICT_TO_INDIA_ELIGIBLE", "true").lower() in ("true", "1")
    MIN_MATCH_SCORE: int = int(os.getenv("MIN_MATCH_SCORE", "80"))
    MAX_DAILY_APPLICATIONS: int = int(os.getenv("MAX_DAILY_APPLICATIONS", "10"))
    JOB_SEARCH_INTERVAL_HOURS: int = int(os.getenv("JOB_SEARCH_INTERVAL_HOURS", "6"))
    
    AUTO_APPLY_ENABLED: bool = os.getenv("AUTO_APPLY_ENABLED", "false").lower() in ("true", "1")
    APPLICATION_APPROVAL_REQUIRED: bool = os.getenv("APPLICATION_APPROVAL_REQUIRED", "true").lower() in ("true", "1")
    
    ENABLED_JOB_SOURCES: str = os.getenv(
        "ENABLED_JOB_SOURCES", 
        "greenhouse,lever,ashby,remotive,remoteok,outlier,alignerr,mercor,handshake,contra,braintrust"
    )
    AUTHORIZED_APPLICATION_SOURCES: str = os.getenv(
        "AUTHORIZED_APPLICATION_SOURCES", 
        "mock_ats,greenhouse_sandbox"
    )

    # Phase 6: Recruiter Response & Interview Management Settings
    RECRUITER_MONITORING_ENABLED: bool = os.getenv("RECRUITER_MONITORING_ENABLED", "true").lower() in ("true", "1")
    GMAIL_SYNC_ENABLED: bool = os.getenv("GMAIL_SYNC_ENABLED", "false").lower() in ("true", "1")
    GMAIL_OAUTH_CLIENT_ID: str = os.getenv("GMAIL_OAUTH_CLIENT_ID", "")
    GMAIL_OAUTH_CLIENT_SECRET: str = os.getenv("GMAIL_OAUTH_CLIENT_SECRET", "")

    FOLLOWUP_RECOMMENDATIONS_ENABLED: bool = os.getenv("FOLLOWUP_RECOMMENDATIONS_ENABLED", "true").lower() in ("true", "1")
    AUTO_SEND_RECRUITER_EMAILS: bool = os.getenv("AUTO_SEND_RECRUITER_EMAILS", "false").lower() in ("true", "1")
    DEFAULT_FOLLOWUP_DAYS: int = int(os.getenv("DEFAULT_FOLLOWUP_DAYS", "10"))
    MAX_FOLLOWUPS_PER_APPLICATION: int = int(os.getenv("MAX_FOLLOWUPS_PER_APPLICATION", "2"))

    INTERVIEW_MONITORING_ENABLED: bool = os.getenv("INTERVIEW_MONITORING_ENABLED", "true").lower() in ("true", "1")
    GOOGLE_CALENDAR_ENABLED: bool = os.getenv("GOOGLE_CALENDAR_ENABLED", "false").lower() in ("true", "1")
    INTERVIEW_TIMEZONE: str = os.getenv("INTERVIEW_TIMEZONE", "Asia/Kolkata")
    INTERVIEW_REMINDER_HOURS: str = os.getenv("INTERVIEW_REMINDER_HOURS", "24,2")
    INTERVIEW_REMINDER_MINUTES: int = int(os.getenv("INTERVIEW_REMINDER_MINUTES", "30"))

    APPLICATION_ANALYTICS_ENABLED: bool = os.getenv("APPLICATION_ANALYTICS_ENABLED", "true").lower() in ("true", "1")
    AI_RECOMMENDATIONS_ENABLED: bool = os.getenv("AI_RECOMMENDATIONS_ENABLED", "true").lower() in ("true", "1")

    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
