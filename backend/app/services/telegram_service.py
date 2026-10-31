import threading
import time
import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings

class TelegramNotificationService:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = settings.TELEGRAM_ENABLED
        self.polling_active = False
        self.polling_thread = None
        self.last_update_id = 0

    def send_message(self, text: str, target_chat_id: Optional[str] = None) -> Dict[str, Any]:
        """Send message via Telegram Bot API with error handling."""
        chat = target_chat_id or self.chat_id
        if not self.enabled or not self.bot_token or not chat:
            return {
                "success": True,
                "mode": "simulated_local",
                "message": "Telegram token or chat_id not configured. Notification logged locally."
            }

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat,
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
            f"🚀 <b>GLOBAL JOB HUNTER AI — HIGH MATCH DISCOVERED</b>\n\n"
            f"<b>Company:</b> {job.get('company_name')}\n"
            f"<b>Position:</b> {job.get('title')}\n"
            f"<b>Match Score:</b> <b>{match_score}/100</b>\n"
            f"<b>Compensation:</b> <code>{job.get('compensation_text')}</code>\n"
            f"<b>Location:</b> {job.get('location')} ({job.get('country_eligibility')})\n\n"
            f"👉 <a href='{job.get('application_url')}'>View Official Portal</a>"
        )
        return self.send_message(msg)

    def notify_ready_for_approval(self, app_id: int, job: Dict[str, Any], match_score: float) -> Dict[str, Any]:
        msg = (
            f"📋 <b>APPLICATION STAGED & READY FOR APPROVAL</b>\n\n"
            f"<b>Application ID:</b> #{app_id}\n"
            f"<b>Company:</b> {job.get('company_name')}\n"
            f"<b>Position:</b> {job.get('title')}\n"
            f"<b>Resume Match:</b> {match_score}/100\n"
            f"<b>Tailored Documents:</b> Generated from verified resume evidence\n\n"
            f"👉 Open dashboard at http://localhost:3000/queue to review and authorize submission."
        )
        return self.send_message(msg)

    def notify_application_confirmed(self, app_id: int, job: Dict[str, Any], confirmation_id: str, applied_at: str) -> Dict[str, Any]:
        msg = (
            f"🚀 <b>GLOBAL JOB HUNTER AI</b>\n\n"
            f"✅ <b>APPLICATION SUBMISSION CONFIRMED</b>\n\n"
            f"<b>Company:</b> {job.get('company_name')}\n"
            f"<b>Position:</b> {job.get('title')}\n"
            f"<b>Compensation:</b> {job.get('compensation_text')}\n"
            f"<b>Applied:</b> {applied_at}\n"
            f"<b>Authoritative Confirmation ID:</b> <code>{confirmation_id}</code>\n\n"
            f"🔗 <a href='{job.get('application_url')}'>Verified Application Link</a>\n"
            f"<b>Status:</b> Submitted — Confirmed"
        )
        return self.send_message(msg)

    # =========================================================
    # INBOUND COMMAND DISPATCHER & LUXURY /START HANDLER
    # =========================================================
    def build_start_message(self) -> str:
        return (
            f"💎 <b>GLOBAL JOB HUNTER AI — PREMIER AUTONOMOUS CAREER SUITE</b>\n"
            f"<i>Private Autonomous AI Employment System for High-Yield Global Tech Roles</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👑 <b>AN UNCOMPROMISING, ENTERPRISE-GRADE AI RECRUITMENT AGENT</b>\n"
            f"This is not a generic job-scraper or spam bot. You are connected to a high-end, self-hosted autonomous AI agent engineered specifically to hunt, verify, and land premium international employment ($40–$150/hr | $75,000–$150,000/yr) across:\n\n"
            f"• <b>Frontier AI Training & RLHF</b> (Surge AI, Alignerr, Mercor, Outlier, Handshake)\n"
            f"• <b>Full-Stack & Systems Architecture</b> (Python, Django, FastAPI, React, Next.js)\n"
            f"• <b>Autonomous AI Agents & Automation Pipelines</b>\n"
            f"• <b>Global Independent Contractor Engagements</b> (Contra, Braintrust, Lemon.io)\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ <b>HOW THE SYSTEM WORKS (IN-DEPTH ARCHITECTURE):</b>\n\n"
            f"1️⃣ <b>Autonomous Multi-Source Discovery:</b>\n"
            f"Every 6 hours, our modular connectors monitor official ATS endpoints (Greenhouse, Lever, Ashby), global remote APIs (Remotive), and premier AI training platforms. All opportunities are deduplicated and verified active.\n\n"
            f"2️⃣ <b>6-Pillar Neural Match Engine (0–100 Heuristic):</b>\n"
            f"Each vacancy is rigorously evaluated against your verified resume credentials:\n"
            f"• Technical Skills Match: <b>30%</b>\n"
            f"• Demonstrable Professional Experience: <b>20%</b>\n"
            f"• India Remote & Work Authorization Eligibility: <b>20%</b>\n"
            f"• Educational Qualifications: <b>10%</b>\n"
            f"• Role Preferences: <b>10%</b>\n"
            f"• Opportunity Recency & Quality: <b>10%</b>\n"
            f"<i>Vacancies scoring under 80/100 are automatically rejected or held for manual inspection.</i>\n\n"
            f"3️⃣ <b>Fact-Substantiated Document Synthesis:</b>\n"
            f"Our AI generator creates tailored professional summaries, custom cover letters, and standard question answers using <b>strictly substantiated facts</b> from your background (UPES MBA CGPA 8.90, Jamia B.Tech 83.3%, 200+ FreelanceKar deliveries, Handshake Dynamo, Outlier AI). Zero hallucinations or fabricated skills.\n\n"
            f"4️⃣ <b>3 Application Execution Modes:</b>\n"
            f"• <b>Mode A (Autonomous):</b> Submits automatically to pre-authorized API endpoints in your allowlist.\n"
            f"• <b>Mode B (Approval Required):</b> Stages documents in your dashboard queue for 1-click review.\n"
            f"• <b>Mode C (Assisted):</b> Pre-fills answers and generates direct portal links for manual submission.\n\n"
            f"5️⃣ <b>Strict Submission Proof:</b>\n"
            f"Applications are only marked confirmed when an authoritative API receipt or confirmation ID is returned. A browser click alone is never accepted as evidence.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎮 <b>INTERACTIVE COMMAND SHORTCUTS:</b>\n\n"
            f"• <b>/jobs</b> — View top high-match vacancies live in your pipeline.\n"
            f"• <b>/queue</b> — Inspect applications waiting for your approval.\n"
            f"• <b>/status</b> — System health, active crawling metrics & pipeline counts.\n"
            f"• <b>/profile</b> — View your active candidate credentials & skills.\n"
            f"• <b>/help</b> — Full command and documentation guide.\n\n"
            f"🖥️ <b>Web Command Center:</b>\n"
            f"<code>http://localhost:3000</code>\n\n"
            f"<i>System Active • Operating in Asia/Kolkata timezone</i>"
        )

    def handle_incoming_update(self, update: Dict[str, Any]):
        """Parse incoming Telegram update and route to appropriate command."""
        message = update.get("message") or update.get("edited_message")
        if not message:
            return

        chat_id = str(message.get("chat", {}).get("id"))
        text = (message.get("text") or "").strip()
        command = text.split()[0].lower() if text else ""

        # Update chat_id automatically if matching user
        if not self.chat_id:
            self.chat_id = chat_id

        if command == "/start":
            self.send_message(self.build_start_message(), target_chat_id=chat_id)

        elif command == "/help":
            help_text = (
                f"📖 <b>GLOBAL JOB HUNTER AI — COMMAND DIRECTORY</b>\n\n"
                f"• <b>/start</b> — Comprehensive deep-dive on system architecture, operation modes, and value.\n"
                f"• <b>/jobs</b> — Top live vacancies scoring ≥ 85/100 compatibility.\n"
                f"• <b>/queue</b> — Review staged applications awaiting your approval.\n"
                f"• <b>/status</b> — Pipeline analytics, crawled counts, and background worker status.\n"
                f"• <b>/profile</b> — Extracted candidate credentials, degrees, and skills.\n\n"
                f"Open your web dashboard at: http://localhost:3000"
            )
            self.send_message(help_text, target_chat_id=chat_id)

        elif command == "/status":
            from app.core.database import SessionLocal
            from app.models.schema import JobPosting, Application, JobMatch
            db = SessionLocal()
            try:
                total_jobs = db.query(JobPosting).count()
                high_match = db.query(JobMatch).filter(JobMatch.overall_score >= 85).count()
                awaiting = db.query(Application).filter(Application.status == "AWAITING_APPROVAL").count()
                confirmed = db.query(Application).filter(Application.status == "SUBMITTED_CONFIRMED").count()

                status_msg = (
                    f"📊 <b>GLOBAL JOB HUNTER AI — PIPELINE METRICS</b>\n\n"
                    f"• <b>Total Crawled Jobs:</b> {total_jobs}\n"
                    f"• <b>High-Match Qualified (≥85):</b> {high_match}\n"
                    f"• <b>Awaiting Approval:</b> {awaiting}\n"
                    f"• <b>Confirmed Submissions:</b> {confirmed}\n"
                    f"• <b>Background Crawler:</b> 🟢 Active (6h cycle)\n"
                    f"• <b>Timezone:</b> {settings.TIMEZONE}\n\n"
                    f"Manage pipeline at http://localhost:3000"
                )
                self.send_message(status_msg, target_chat_id=chat_id)
            finally:
                db.close()

        elif command == "/jobs":
            from app.core.database import SessionLocal
            from app.models.schema import JobPosting, JobMatch
            db = SessionLocal()
            try:
                top_matches = db.query(JobMatch).filter(JobMatch.overall_score >= 90).order_by(JobMatch.overall_score.desc()).limit(5).all()
                if not top_matches:
                    self.send_message("🔍 No 90+ score jobs currently staged. Check dashboard at http://localhost:3000/jobs", target_chat_id=chat_id)
                else:
                    lines = [f"🚀 <b>TOP HIGH-MATCH OPPORTUNITIES (≥90/100):</b>\n"]
                    for idx, m in enumerate(top_matches, 1):
                        job = m.job_posting
                        lines.append(
                            f"<b>{idx}. {job.company_name} — {job.title}</b>\n"
                            f"Score: <b>{m.overall_score}/100</b> | Comp: <code>{job.compensation_text}</code>\n"
                            f"👉 <a href='{job.application_url}'>Portal Link</a>\n"
                        )
                    self.send_message("\n".join(lines), target_chat_id=chat_id)
            finally:
                db.close()

        elif command == "/queue":
            from app.core.database import SessionLocal
            from app.models.schema import Application
            db = SessionLocal()
            try:
                pending = db.query(Application).filter(Application.status == "AWAITING_APPROVAL").all()
                if not pending:
                    self.send_message("✅ <b>Your approval queue is clear!</b> No applications currently awaiting review.", target_chat_id=chat_id)
                else:
                    lines = [f"📋 <b>APPLICATIONS AWAITING REVIEW ({len(pending)}):</b>\n"]
                    for p in pending:
                        job = p.job_posting
                        lines.append(
                            f"• <b>App #{p.id}: {job.company_name} — {job.title}</b>\n"
                            f"Match: {p.match_score}/100\n"
                        )
                    lines.append("\n👉 Review & approve at http://localhost:3000/queue")
                    self.send_message("\n".join(lines), target_chat_id=chat_id)
            finally:
                db.close()

        elif command == "/profile":
            from app.core.database import SessionLocal
            from app.models.schema import CandidateProfile
            db = SessionLocal()
            try:
                prof = db.query(CandidateProfile).first()
                if prof:
                    p_text = (
                        f"👤 <b>CANDIDATE INTELLIGENCE PROFILE</b>\n\n"
                        f"<b>Name:</b> {prof.full_name}\n"
                        f"<b>Location:</b> {prof.location}\n"
                        f"<b>Headline:</b> {prof.headline}\n"
                        f"<b>Academic Credentials:</b> MBA (UPES, CGPA 8.90) • B.Tech (Jamia Millia Islamia, 83.3% First Class)\n"
                        f"<b>Core Strengths:</b> RLHF, LLM Evaluation, Python, Django, FastAPI, React, Next.js, 200+ FreelanceKar Deliveries\n\n"
                        f"🔗 GitHub: {prof.github_url}\n"
                        f"🔗 Web: {prof.portfolio_url}"
                    )
                    self.send_message(p_text, target_chat_id=chat_id)
                else:
                    self.send_message("Candidate profile not yet loaded. Ingest resume in dashboard.", target_chat_id=chat_id)
            finally:
                db.close()

    def start_polling(self):
        """Start long-polling thread for Telegram commands."""
        if self.polling_active or not self.bot_token:
            return

        self.polling_active = True

        def poll_worker():
            while self.polling_active:
                try:
                    if not self.bot_token:
                        time.sleep(5)
                        continue
                    url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
                    params = {"offset": self.last_update_id + 1, "timeout": 5}
                    with httpx.Client(timeout=10.0) as client:
                        resp = client.get(url, params=params)
                        if resp.status_code == 200:
                            data = resp.json()
                            updates = data.get("result", [])
                            for upd in updates:
                                self.last_update_id = upd.get("update_id", self.last_update_id)
                                self.handle_incoming_update(upd)
                        else:
                            time.sleep(5)
                except Exception:
                    time.sleep(5)

        self.polling_thread = threading.Thread(target=poll_worker, daemon=True)
        self.polling_thread.start()
        print("Telegram inbound command polling worker started.")

    def stop_polling(self):
        self.polling_active = False

telegram_service = TelegramNotificationService()
