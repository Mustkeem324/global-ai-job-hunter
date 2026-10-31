import os
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.core.config import settings
from app.models.schema import AutomationPolicy, User
from app.services.telegram_service import telegram_service

router = APIRouter(prefix="/settings", tags=["Settings & Policies"])

ENV_FILE_PATHS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
]

def load_stored_env() -> Dict[str, str]:
    env_dict = {}
    for p in ENV_FILE_PATHS:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_dict[k.strip()] = v.strip()
            break
    return env_dict

def persist_to_env_files(updates: Dict[str, Any]):
    current_env = load_stored_env()
    for k, v in updates.items():
        if v is not None:
            current_env[k] = str(v)
            os.environ[k] = str(v)

    lines = ["# =======================================================",
             "# GLOBAL JOB HUNTER AI — RUNTIME ENVIRONMENT CONFIG",
             "# Auto-updated from Web Dashboard Settings",
             "# =======================================================\n"]
    for k in sorted(current_env.keys()):
        lines.append(f"{k}={current_env[k]}")

    content = "\n".join(lines) + "\n"
    for p in ENV_FILE_PATHS:
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Error persisting .env to {p}: {e}")

@router.get("/")
def get_settings(db: Session = Depends(get_db)):
    user = db.query(User).first()
    policy = db.query(AutomationPolicy).first()
    if not policy:
        policy = AutomationPolicy(
            user_id=user.id if user else 1,
            auto_apply_enabled=False,
            approval_required=True,
            min_match_score=80,
            max_daily_applications=10,
            allowed_sources=["mock_ats", "greenhouse_sandbox"],
            cooling_off_days=30
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)

    file_env = load_stored_env()
    
    return {
        # Environment Variables
        "telegram_bot_token": file_env.get("TELEGRAM_BOT_TOKEN", settings.TELEGRAM_BOT_TOKEN),
        "telegram_chat_id": file_env.get("TELEGRAM_CHAT_ID", settings.TELEGRAM_CHAT_ID),
        "gemini_api_key": file_env.get("GEMINI_API_KEY", settings.GEMINI_API_KEY),
        "resume_folder": file_env.get("RESUME_FOLDER", settings.RESUME_FOLDER),
        "timezone": file_env.get("TIMEZONE", settings.TIMEZONE),
        "job_search_interval_hours": int(file_env.get("JOB_SEARCH_INTERVAL_HOURS", settings.JOB_SEARCH_INTERVAL_HOURS)),
        
        # Automation Policies
        "auto_apply_enabled": policy.auto_apply_enabled,
        "approval_required": policy.approval_required,
        "min_match_score": policy.min_match_score,
        "max_daily_applications": policy.max_daily_applications,
        "allowed_sources": policy.allowed_sources,
        "cooling_off_days": policy.cooling_off_days
    }

@router.put("/")
def update_settings(
    telegram_bot_token: Optional[str] = Body(""),
    telegram_chat_id: Optional[str] = Body(""),
    gemini_api_key: Optional[str] = Body(""),
    resume_folder: Optional[str] = Body("/home/nx-pro"),
    timezone: Optional[str] = Body("Asia/Kolkata"),
    job_search_interval_hours: Optional[int] = Body(6),
    auto_apply_enabled: bool = Body(False),
    approval_required: bool = Body(True),
    min_match_score: int = Body(80),
    max_daily_applications: int = Body(10),
    allowed_sources: list = Body(["mock_ats", "greenhouse_sandbox"]),
    cooling_off_days: int = Body(30),
    db: Session = Depends(get_db)
):
    # 1. Update in-memory runtime settings and services
    if telegram_bot_token is not None:
        settings.TELEGRAM_BOT_TOKEN = telegram_bot_token.strip()
        telegram_service.bot_token = telegram_bot_token.strip()
    if telegram_chat_id is not None:
        settings.TELEGRAM_CHAT_ID = telegram_chat_id.strip()
        telegram_service.chat_id = telegram_chat_id.strip()
    if gemini_api_key is not None:
        settings.GEMINI_API_KEY = gemini_api_key.strip()
    if resume_folder is not None:
        settings.RESUME_FOLDER = resume_folder.strip()
    if timezone is not None:
        settings.TIMEZONE = timezone.strip()
    if job_search_interval_hours is not None:
        settings.JOB_SEARCH_INTERVAL_HOURS = job_search_interval_hours
        
    settings.AUTO_APPLY_ENABLED = auto_apply_enabled
    settings.APPLICATION_APPROVAL_REQUIRED = approval_required
    settings.MIN_MATCH_SCORE = min_match_score
    settings.MAX_DAILY_APPLICATIONS = max_daily_applications

    # 2. Persist to disk (.env files)
    env_updates = {
        "TELEGRAM_BOT_TOKEN": settings.TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": settings.TELEGRAM_CHAT_ID,
        "GEMINI_API_KEY": settings.GEMINI_API_KEY,
        "RESUME_FOLDER": settings.RESUME_FOLDER,
        "TIMEZONE": settings.TIMEZONE,
        "JOB_SEARCH_INTERVAL_HOURS": settings.JOB_SEARCH_INTERVAL_HOURS,
        "AUTO_APPLY_ENABLED": "true" if auto_apply_enabled else "false",
        "APPLICATION_APPROVAL_REQUIRED": "true" if approval_required else "false",
        "MIN_MATCH_SCORE": min_match_score,
        "MAX_DAILY_APPLICATIONS": max_daily_applications,
        "AUTHORIZED_APPLICATION_SOURCES": ",".join(allowed_sources)
    }
    persist_to_env_files(env_updates)

    # 3. Persist database policy
    policy = db.query(AutomationPolicy).first()
    if not policy:
        user = db.query(User).first()
        policy = AutomationPolicy(user_id=user.id if user else 1)
        db.add(policy)
        
    policy.auto_apply_enabled = auto_apply_enabled
    policy.approval_required = approval_required
    policy.min_match_score = min_match_score
    policy.max_daily_applications = max_daily_applications
    policy.allowed_sources = allowed_sources
    policy.cooling_off_days = cooling_off_days
    
    db.commit()

    return {
        "status": "success", 
        "message": "Environment variables (.env) and automation policies saved successfully!"
    }
