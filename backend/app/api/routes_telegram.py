from fastapi import APIRouter, Body, Request
from app.services.telegram_service import telegram_service
from app.core.config import settings
from typing import Dict, Any

router = APIRouter(prefix="/telegram", tags=["Telegram Notifications"])

@router.get("/status")
def get_telegram_status():
    has_token = bool(settings.TELEGRAM_BOT_TOKEN)
    has_chat_id = bool(settings.TELEGRAM_CHAT_ID)
    return {
        "enabled": settings.TELEGRAM_ENABLED,
        "is_configured": has_token and has_chat_id,
        "chat_id": settings.TELEGRAM_CHAT_ID if has_chat_id else None,
        "bot_token_set": has_token,
        "polling_active": telegram_service.polling_active
    }

@router.get("/start-message")
def get_start_message_preview():
    """Returns the deep, elite /start message formatted for Telegram."""
    return {
        "message": telegram_service.build_start_message()
    }

@router.post("/test")
def send_test_notification(message: str = Body("🚀 Test notification from Global Job Hunter AI dashboard!", embed=True)):
    result = telegram_service.send_message(f"<b>GLOBAL JOB HUNTER AI — SYSTEM TEST</b>\n\n{message}")
    return result

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Webhook endpoint for receiving incoming Telegram messages and /start commands."""
    try:
        update = await request.json()
        telegram_service.handle_incoming_update(update)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.post("/start-polling")
def trigger_polling():
    """Start background command listener for Telegram."""
    telegram_service.start_polling()
    return {"status": "polling_started", "active": telegram_service.polling_active}
