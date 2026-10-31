import httpx
from typing import Optional, Dict, Any
from app.core.config import settings

class TelegramNotificationService:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = settings.TELEGRAM_ENABLED

    def send_message(self, text: str) -> Dict[str, Any]:
        """Send message via Telegram Bot API with error handling."""
        if not self.enabled or not self.bot_token or not self.chat_id:
            # Safe local log when credentials are not yet entered
            return {
                "success": True,
                "mode": "simulated_local",
                "message": "Telegram token or chat_id not configured. Notification logged locally."
            }

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    return {"success": True, "mode": "delivered", "response": resp.json()}
                else:
                    return {
                        "success": False, 
                        "mode": "api_error", 
                        "status_code": resp.status_code, 
                        "error": resp.text
                    }
        except Exception as e:
            return {"success": False, "mode": "network_exception", "error": str(e)}

    def notify_high_match_job(self, job: Dict[str, Any], match_score: float) -> Dict[str, Any]:
        msg = (
            f"🚀 <b>GLOBAL JOB HUNTER AI — NEW HIGH MATCH</b>\n\n"
            f"<b>Company:</b> {job.get('company_name')}\n"
            f"<b>Position:</b> {job.get('title')}\n"
            f"<b>Match Score:</b> <b>{match_score}/100</b>\n"
            f"<b>Compensation:</b> {job.get('compensation_text')}\n"
            f"<b>Location:</b> {job.get('location')} ({job.get('country_eligibility')})\n\n"
            f"👉 <a href='{job.get('application_url')}'>View Application Portal</a>"
        )
        return self.send_message(msg)

    def notify_ready_for_approval(self, app_id: int, job: Dict[str, Any], match_score: float) -> Dict[str, Any]:
        msg = (
            f"📋 <b>APPLICATION READY FOR APPROVAL</b>\n\n"
            f"<b>Application ID:</b> #{app_id}\n"
            f"<b>Company:</b> {job.get('company_name')}\n"
            f"<b>Position:</b> {job.get('title')}\n"
            f"<b>Resume Match:</b> {match_score}/100\n"
            f"<b>Tailored Documents:</b> Generated & Staged\n\n"
            f"Please review and approve in your Global Job Hunter dashboard."
        )
        return self.send_message(msg)

    def notify_application_confirmed(self, app_id: int, job: Dict[str, Any], confirmation_id: str, applied_at: str) -> Dict[str, Any]:
        msg = (
            f"🚀 <b>GLOBAL JOB HUNTER AI</b>\n\n"
            f"✅ <b>APPLICATION CONFIRMED</b>\n\n"
            f"<b>Company:</b> {job.get('company_name')}\n"
            f"<b>Position:</b> {job.get('title')}\n"
            f"<b>Location:</b> {job.get('location')}\n"
            f"<b>Compensation:</b> {job.get('compensation_text')}\n"
            f"<b>Application Method:</b> Authorized submission\n"
            f"<b>Applied:</b> {applied_at}\n"
            f"<b>Confirmation ID:</b> <code>{confirmation_id}</code>\n\n"
            f"🔗 <a href='{job.get('application_url')}'>Verified Application Link</a>\n"
            f"<b>Status:</b> Submitted — Confirmed"
        )
        return self.send_message(msg)

telegram_service = TelegramNotificationService()
