from fastapi import APIRouter, Body
from app.services.telegram_service import telegram_service
from app.core.config import settings

router = APIRouter(prefix="/telegram", tags=["Telegram Notifications"])

@router.get("/status")
def get_telegram_status():
    has_token = bool(settings.TELEGRAM_BOT_TOKEN)
    has_chat_id = bool(settings.TELEGRAM_CHAT_ID)
    return {
        "enabled": settings.TELEGRAM_ENABLED,
        "is_configured": has_token and has_chat_id,
        "chat_id": settings.TELEGRAM_CHAT_ID if has_chat_id else None,
        "bot_token_set": has_token
    }

@router.post("/test")
def send_test_notification(message: str = Body("🚀 Test notification from Global Job Hunter AI dashboard!", embed=True)):
    result = telegram_service.send_message(f"<b>GLOBAL JOB HUNTER AI — SYSTEM TEST</b>\n\n{message}")
    return result
