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
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
