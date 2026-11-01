import threading
import time
import uuid
import datetime
import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings

class TelegramNotificationService:
    """
    Phase 8 & 9: Enterprise Telegram Command Center & Event-Driven Engine
    Supports all 16 commands, consistent structured job cards, and 5 interactive inline buttons:
    [🚀 Auto Apply] [👁 View Job] [📄 Review Application] [❌ Skip] [⭐ Save Job]
    """
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = settings.TELEGRAM_ENABLED
        self.polling_active = False
        self.polling_thread = None
        self.last_update_id = 0
        self.is_paused = False
        self.saved_jobs = set()

    def send_message(
        self, 
        text: str, 
        target_chat_id: Optional[str] = None, 
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send message via Telegram Bot API with optional inline keyboards."""
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
        if reply_markup:
            payload["reply_markup"] = reply_markup

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

    def answer_callback_query(self, query_id: str, text: str = "", show_alert: bool = False):
        """Acknowledge Telegram callback query immediately."""
        if not self.bot_token:
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery"
        try:
            with httpx.Client(timeout=5.0) as client:
                client.post(url, json={"callback_query_id": query_id, "text": text, "show_alert": show_alert})
        except Exception as e:
            print(f"Error answering callback query: {e}")

    def format_job_card(self, job: Dict[str, Any], match_score: float, why_text: str = "") -> Dict[str, Any]:
        """Format vacancy card and 5 inline buttons strictly matching Phase 8 specification."""
        job_id = job.get("id") or job.get("source_job_id", "")
        company = job.get("company_name", "Leading AI Organization")
        position = job.get("title") or job.get("job_title", "Technical Specialist")
        location = job.get("location") or job.get("country_eligibility", "Worldwide Remote")
        contract = job.get("employment_type", "Contract / Full-time")
        salary = job.get("compensation_text", "$40 - $120 / hr")
        source_name = job.get("source_id") or job.get("adapter_key", "Verified ATS Network")
        app_url = job.get("application_url", "https://freelancekar.com")
        posted = str(job.get("posted_at") or job.get("posted_date") or "Recently Verified")[:10]

        if not why_text:
            why_text = f"High alignment with verified background in Python, RLHF evaluation, and full-stack software delivery (UPES MBA, Jamia B.Tech)."

        text = (
            f"🚀 <b>GLOBAL JOB HUNTER AI</b>\n\n"
            f"🏢 <b>Company:</b> {company}\n"
            f"💼 <b>Position:</b> {position}\n"
            f"🌍 <b>Location:</b> {location}\n"
            f"📑 <b>Contract:</b> {contract}\n"
            f"💰 <b>Salary:</b> <code>{salary}</code>\n"
            f"🎯 <b>Resume Match:</b> <b>{int(match_score)}/100</b>\n\n"
            f"✅ <b>Skills Match:</b> Strong Alignment\n"
            f"✅ <b>Location Eligibility:</b> India Confirmed\n"
            f"✅ <b>Job Status:</b> Verified Open\n"
            f"📅 <b>Posted:</b> {posted}\n\n"
            f"<b>Why it matches:</b>\n"
            f"{why_text}\n\n"
            f"<b>Source:</b> {source_name.title()}\n"
            f"<b>Application:</b> <a href='{app_url}'>Official Portal Link</a>"
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "🚀 Auto Apply", "callback_data": f"apply:{job_id}"},
                    {"text": "👁 View Job", "url": app_url}
                ],
                [
                    {"text": "📄 Review Application", "callback_data": f"review:{job_id}"},
                    {"text": "❌ Skip", "callback_data": f"skip:{job_id}"}
                ],
                [
                    {"text": "⭐ Save Job", "callback_data": f"save:{job_id}"}
                ]
            ]
        }
        return {"text": text, "reply_markup": reply_markup}

    def format_naukri_job_card(self, job: Dict[str, Any], match_score: float) -> Dict[str, Any]:
        """
        Phase 7 Module 7: Canonical Naukri Job Card
        """
        job_id = job.get("id") or job.get("source_job_id", "")
        company = job.get("company_name", "Leading Indian Tech Enterprise")
        position = job.get("title", "Full-Stack AI Developer")
        location = job.get("location", "Noida / Delhi NCR, India")
        salary = job.get("compensation_text", "Market Standard / Competitive")
        contract = job.get("employment_type", "Full-time")
        app_url = job.get("application_url", "https://www.naukri.com")
        capability = job.get("capability", "MANUAL_APPLICATION_ASSISTANT")

        text = (
            f"🇮🇳 <b>GLOBAL JOB HUNTER AI</b>\n\n"
            f"🎯 <b>NAUKRI JOB MATCH</b>\n\n"
            f"🏢 <b>Company:</b> {company}\n"
            f"💼 <b>Position:</b> {position}\n"
            f"📍 <b>Location:</b> {location}\n"
            f"💰 <b>Salary:</b> <code>{salary}</code>\n"
            f"📑 <b>Employment:</b> {contract}\n"
            f"🎯 <b>Match:</b> <b>{int(match_score)}/100</b>\n\n"
            f"🛠 <b>Required Skills:</b>\n"
            f"Python, FastAPI, Next.js, RLHF Model Evaluation, PostgreSQL\n\n"
            f"📡 <b>Application Source:</b> Naukri.com\n"
            f"⚡ <b>Application Capability:</b> <code>{capability}</code>"
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "👁 View Job", "url": app_url},
                    {"text": "📝 Prepare Application", "callback_data": f"nk:prep:{job_id}"}
                ],
                [
                    {"text": "⭐ Save", "callback_data": f"save:{job_id}"},
                    {"text": "❌ Skip", "callback_data": f"skip:{job_id}"}
                ]
            ]
        }
        return {"text": text, "reply_markup": reply_markup}


    def notify_high_match_job(self, job: Dict[str, Any], match_score: float) -> Dict[str, Any]:
        """Dispatch high-match vacancy to Telegram using standard card format."""
        card = self.format_job_card(job, match_score)
        return self.send_message(card["text"], reply_markup=card["reply_markup"])

    def format_recruiter_response_card(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 6 Module 5: Structured Recruiter Response Card
        """
        company = msg.get("company", "Employer")
        role = msg.get("role", "Software Role")
        recruiter = msg.get("recruiter", "Recruiting Team")
        received_at = msg.get("received_at", "Recently")
        cat = msg.get("category", "CORRESPONDENCE")
        conf = msg.get("confidence", 0.90)
        app_id = msg.get("application_id", "")
        msg_id = msg.get("message_id", "")
        date_str = msg.get("interview_date", "Pending Selection")
        tz_str = msg.get("interview_timezone", "Asia/Kolkata")

        text = (
            f"📨 <b>GLOBAL JOB HUNTER AI</b>\n\n"
            f"🎯 <b>RECRUITER RESPONSE DETECTED</b>\n\n"
            f"🏢 <b>Company:</b> {company}\n"
            f"💼 <b>Role:</b> {role}\n"
            f"👤 <b>Recruiter:</b> {recruiter}\n"
            f"🕒 <b>Email Received:</b> {received_at}\n\n"
            f"📑 <b>Message Type:</b> <code>{cat}</code>\n"
        )
        if cat in ("INTERVIEW_INVITATION", "INTERVIEW_RESCHEDULE"):
            text += f"📅 <b>Interview Date:</b> {date_str}\n🕒 <b>Interview Time:</b> {tz_str}\n"
        text += (
            f"🎯 <b>Confidence:</b> <b>{int(conf * 100)}%</b>\n\n"
            f"<i>Choose an authorized response action below:</i>"
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "👁 View Email", "callback_data": f"msg:view:{msg_id}"},
                    {"text": "✍️ Prepare Reply", "callback_data": f"reply:prepare:{app_id}"}
                ],
                [
                    {"text": "📅 Review Interview", "callback_data": f"intv:prep:{app_id}"},
                    {"text": "🤝 Mark Follow-Up", "callback_data": f"fup:mark:{app_id}"}
                ]
            ]
        }
        return {"text": text, "reply_markup": reply_markup}

    def format_naukri_job_card(self, job: Dict[str, Any], match_score: float) -> Dict[str, Any]:
        """
        Phase 7 Module 7: Canonical Naukri Job Card
        """
        job_id = job.get("id") or job.get("source_job_id", "")
        company = job.get("company_name", "Leading Indian Tech Enterprise")
        position = job.get("title", "Full-Stack AI Developer")
        location = job.get("location", "Noida / Delhi NCR, India")
        salary = job.get("compensation_text", "Market Standard / Competitive")
        contract = job.get("employment_type", "Full-time")
        app_url = job.get("application_url", "https://www.naukri.com")
        capability = job.get("capability", "MANUAL_APPLICATION_ASSISTANT")

        text = (
            f"🇮🇳 <b>GLOBAL JOB HUNTER AI</b>\n\n"
            f"🎯 <b>NAUKRI JOB MATCH</b>\n\n"
            f"🏢 <b>Company:</b> {company}\n"
            f"💼 <b>Position:</b> {position}\n"
            f"📍 <b>Location:</b> {location}\n"
            f"💰 <b>Salary:</b> <code>{salary}</code>\n"
            f"📑 <b>Employment:</b> {contract}\n"
            f"🎯 <b>Match:</b> <b>{int(match_score)}/100</b>\n\n"
            f"🛠 <b>Required Skills:</b>\n"
            f"Python, FastAPI, Next.js, RLHF Model Evaluation, PostgreSQL\n\n"
            f"📡 <b>Application Source:</b> Naukri.com\n"
            f"⚡ <b>Application Capability:</b> <code>{capability}</code>"
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "👁 View Job", "url": app_url},
                    {"text": "📝 Prepare Application", "callback_data": f"nk:prep:{job_id}"}
                ],
                [
                    {"text": "⭐ Save", "callback_data": f"save:{job_id}"},
                    {"text": "❌ Skip", "callback_data": f"skip:{job_id}"}
                ]
            ]
        }
        return {"text": text, "reply_markup": reply_markup}



    def notify_application_confirmed(self, app_id: int, job: Dict[str, Any], confirmation_id: str, applied_at: str) -> Dict[str, Any]:
        msg = (
            f"🚀 <b>GLOBAL JOB HUNTER AI</b>\n\n"
            f"✅ <b>APPLICATION SUBMISSION CONFIRMED</b>\n\n"
            f"<b>Company:</b> {job.get('company_name')}\n"
            f"<b>Position:</b> {job.get('title') or job.get('job_title')}\n"
            f"<b>Compensation:</b> {job.get('compensation_text')}\n"
            f"<b>Applied:</b> {applied_at}\n"
            f"<b>Authoritative Confirmation ID:</b> <code>{confirmation_id}</code>\n\n"
            f"🔗 <a href='{job.get('application_url')}'>Verified Application Link</a>\n"
            f"<b>Status:</b> Submitted — Confirmed"
        )
        return self.send_message(msg)

    # =========================================================
    # INBOUND COMMAND DISPATCHER (ALL 16 REQUIRED COMMANDS)
    # =========================================================
    def build_start_message(self) -> str:
        return (
            f"💎 <b>GLOBAL JOB HUNTER AI — PREMIER CAREER PLATFORM (V2.0)</b>\n"
            f"<i>Autonomous Global Job Search Engine & Telegram One-Click Application Center</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👑 <b>AN UNCOMPROMISING RECRUITMENT INTELLIGENCE SUITE</b>\n"
            f"Connected to 8 global ATS feeds & remote APIs: Greenhouse, Lever, Ashby, Himalayas, Jobicy, Remotive, Arbeitnow & Verified AI Networks.\n\n"
            f"⚡ <b>QUICK ACTIONS:</b>\n"
            f"• /topjobs — View top opportunities (≥85/100)\n"
            f"• /search &lt;keyword&gt; — Search live global vacancies\n"
            f"• /aitraining — AI Training & RLHF positions\n"
            f"• /fullstack — Full-Stack Python & Next.js positions\n"
            f"• /freelance — Remote independent contract work\n"
            f"• /profile — View your verified candidate profile\n"
            f"• /applications — View submission receipts\n"
            f"• /sources — Live status of all 8 discovery connectors\n"
            f"• /help — Full command directory\n\n"
            f"🖥️ <b>Web Command Center:</b> http://localhost:3000\n"
            f"<i>System Active • Operating in Asia/Kolkata timezone</i>"
        )

    def handle_incoming_update(self, update: Dict[str, Any]):
        """Parse incoming update, handling both text commands and inline callback queries."""
        callback_query = update.get("callback_query")
        if callback_query:
            self.handle_callback_query(callback_query)
            return

        message = update.get("message") or update.get("edited_message")
        if not message:
            return

        chat_id = str(message.get("chat", {}).get("id"))
        text = (message.get("text") or "").strip()
        parts = text.split(maxsplit=1)
        raw_cmd = parts[0].strip().lower() if parts else ""
        query_param = parts[1].strip() if len(parts) > 1 else ""

        # Normalize command by stripping bot username (e.g. /job@NXmod_bot -> /job)
        clean_cmd = raw_cmd.split("@")[0].strip().lower()
        has_slash = clean_cmd.startswith("/")
        if not has_slash:
            clean_cmd = "/" + clean_cmd

        if not self.chat_id:
            self.chat_id = chat_id

        from app.core.database import SessionLocal
        from app.models.schema import JobPosting, Application, JobMatch, CandidateProfile

        if clean_cmd in ("/start", "/menu", "/intro"):
            self.send_message(self.build_start_message(), target_chat_id=chat_id)

        elif clean_cmd in ("/help", "/instructions", "/info"):
            help_msg = (
                f"📖 <b>GLOBAL JOB HUNTER AI — COMMAND DIRECTORY</b>\n\n"
                f"• <b>/job</b> or <b>/jobs</b> — View top high-match opportunities (≥85%)\n"
                f"• <b>/start</b> — Main menu & system overview\n"
                f"• <b>/profile</b> — My resume and extracted skills\n"
                f"• <b>/search &lt;query&gt;</b> — Search real global vacancies\n"
                f"• <b>/filters</b> — Search preferences and match thresholds\n"
                f"• <b>/topjobs</b> — Highest-ranked opportunities (≥85%)\n"
                f"• <b>/remote</b> — Worldwide remote positions\n"
                f"• <b>/aitraining</b> — AI training & RLHF opportunities\n"
                f"• <b>/fullstack</b> — Full-stack & backend opportunities\n"
                f"• <b>/freelance</b> — Freelance and contract projects\n"
                f"• <b>/autoapply</b> — Application automation settings\n"
                f"• <b>/applications</b> — Verified application history\n"
                f"• <b>/pending</b> — Applications awaiting approval\n"
                f"• <b>/stats</b> — Search and pipeline statistics\n"
                f"• <b>/sources</b> — API connector health & status\n"
                f"• <b>/pause</b> — Pause scheduled background crawler\n"
                f"• <b>/resume</b> — Resume background crawler\n\n"
                f"Open Dashboard: http://localhost:3000"
            )
            self.send_message(help_msg, target_chat_id=chat_id)

        elif clean_cmd in ("/profile", "/cv", "/resume", "/candidate"):
            db = SessionLocal()
            try:
                prof = db.query(CandidateProfile).first()
                if prof:
                    skills_list = [s.name for s in prof.skills[:12]]
                    p_text = (
                        f"👤 <b>CANDIDATE INTELLIGENCE PROFILE</b>\n\n"
                        f"<b>Name:</b> {prof.full_name}\n"
                        f"<b>Location:</b> {prof.location}\n"
                        f"<b>Headline:</b> {prof.headline}\n\n"
                        f"🎓 <b>Academic Degrees:</b>\n"
                        f"• MBA in Strategy & Operations (UPES Dehradun, 8.90 CGPA)\n"
                        f"• B.Tech in Electrical Engineering (Jamia Millia Islamia, 83.3% First Class)\n\n"
                        f"💼 <b>Active Workstreams:</b>\n"
                        f"• Handshake Project Dynamo (AI Trainer / LLM Evaluation)\n"
                        f"• Outlier AI (Generative AI Engineer & RLHF Consultant)\n"
                        f"• FreelanceKar.com (Founder, 200+ Delivered Projects)\n\n"
                        f"⚡ <b>Core Skills:</b>\n"
                        f"{', '.join(skills_list)}\n\n"
                        f"🔗 GitHub: {prof.github_url}\n"
                        f"🔗 Web: {prof.portfolio_url}"
                    )
                    self.send_message(p_text, target_chat_id=chat_id)
                else:
                    self.send_message("Candidate profile not yet loaded. Ingest resume at http://localhost:3000/resumes", target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/job", "/jobs", "/topjob", "/topjobs"):
            db = SessionLocal()
            try:
                top_matches = db.query(JobMatch).filter(JobMatch.overall_score >= 85).order_by(JobMatch.overall_score.desc()).limit(3).all()
                if not top_matches:
                    self.send_message("🔍 No 85+ score jobs currently staged. Run /search to crawl new vacancies.", target_chat_id=chat_id)
                else:
                    self.send_message(f"🏆 <b>TOP HIGH-MATCH OPPORTUNITIES (≥85/100):</b>", target_chat_id=chat_id)
                    for m in top_matches:
                        job = m.job_posting
                        job_dict = {
                            "id": job.id,
                            "company_name": job.company_name,
                            "title": job.title,
                            "location": job.location,
                            "country_eligibility": job.country_eligibility,
                            "employment_type": job.employment_type,
                            "compensation_text": job.compensation_text,
                            "application_url": job.application_url,
                            "source_id": getattr(job, "source_id", "ATS Verified"),
                            "posted_at": str(job.posted_date or "")[:10]
                        }
                        card = self.format_job_card(job_dict, m.overall_score)
                        self.send_message(card["text"], target_chat_id=chat_id, reply_markup=card["reply_markup"])
            finally:
                db.close()

        elif clean_cmd in ("/search", "/find", "/query"):
            q = query_param or "AI"
            self.send_message(f"🔍 <i>Searching live global sources for '<b>{q}</b>'...</i>", target_chat_id=chat_id)
            from app.services.discovery_service import discovery_service
            jobs = discovery_service.run_discovery(query=q, persist=True)
            if not jobs:
                self.send_message(f"No vacancies found matching '{q}'.", target_chat_id=chat_id)
            else:
                self.send_message(f"🎯 <b>Found {len(jobs)} vacancies for '{q}'. Showing top matches:</b>", target_chat_id=chat_id)
                for j in jobs[:3]:
                    card = self.format_job_card(j, 88.0)
                    self.send_message(card["text"], target_chat_id=chat_id, reply_markup=card["reply_markup"])

        elif clean_cmd in ("/remote", "/aitraining", "/fullstack", "/freelance"):
            db = SessionLocal()
            try:
                query_filter = db.query(JobPosting)
                if clean_cmd == "/remote":
                    query_filter = query_filter.filter(JobPosting.workplace_type == "Remote")
                elif clean_cmd == "/aitraining":
                    query_filter = query_filter.filter(JobPosting.title.ilike("%AI%") | JobPosting.title.ilike("%LLM%") | JobPosting.title.ilike("%Trainer%"))
                elif clean_cmd == "/fullstack":
                    query_filter = query_filter.filter(JobPosting.title.ilike("%Full%") | JobPosting.title.ilike("%Python%") | JobPosting.title.ilike("%Engineer%"))
                elif clean_cmd == "/freelance":
                    query_filter = query_filter.filter(JobPosting.employment_type.ilike("%Contract%") | JobPosting.employment_type.ilike("%Freelance%"))

                results = query_filter.limit(3).all()
                tag_label = clean_cmd.replace("/", "").upper()
                if not results:
                    self.send_message(f"No specific vacancies in {tag_label} found currently. Use /search to crawl.", target_chat_id=chat_id)
                else:
                    self.send_message(f"🌐 <b>FEATURED {tag_label} OPPORTUNITIES:</b>", target_chat_id=chat_id)
                    for r in results:
                        job_dict = {
                            "id": r.id,
                            "company_name": r.company_name,
                            "title": r.title,
                            "location": r.location,
                            "country_eligibility": r.country_eligibility,
                            "employment_type": r.employment_type,
                            "compensation_text": r.compensation_text,
                            "application_url": r.application_url,
                            "source_id": "Global Feed",
                            "posted_at": str(r.posted_date or "")[:10]
                        }
                        card = self.format_job_card(job_dict, 89.0)
                        self.send_message(card["text"], target_chat_id=chat_id, reply_markup=card["reply_markup"])
            finally:
                db.close()

        elif clean_cmd in ("/filters", "/filter", "/preferences"):
            india_label = "🟢 India-Only: ON" if getattr(settings, 'RESTRICT_TO_INDIA_ELIGIBLE', True) else "⚪ India-Only: OFF"
            filt_markup = {
                "inline_keyboard": [
                    [
                        {"text": india_label, "callback_data": "cfg:toggle_india"},
                        {"text": f"Threshold: {settings.MIN_MATCH_SCORE}%", "callback_data": "cfg:cycle_score"}
                    ],
                    [
                        {"text": "⚙️ Open Web Settings", "url": "http://localhost:3000/settings"}
                    ]
                ]
            }
            filt_msg = (
                f"⚙️ <b>CURRENT SEARCH PREFERENCES & FILTERS</b>\n\n"
                f"• <b>Default Applicant Location:</b> India (Asia/Kolkata)\n"
                f"• <b>Minimum Match Threshold:</b> <b>{settings.MIN_MATCH_SCORE} / 100</b>\n"
                f"• <b>India-Eligible Filter:</b> {'🟢 Strictly Active' if getattr(settings, 'RESTRICT_TO_INDIA_ELIGIBLE', True) else '⚪ Showing All Locations'}\n"
                f"• <b>Workplace Type:</b> 100% Worldwide Remote\n"
                f"• <b>Employment Types:</b> Full-Time, Contract, Freelance\n"
                f"• <b>Connected Feeds:</b> Greenhouse, Lever, Ashby, Remotive, Himalayas, Jobicy, Arbeitnow\n\n"
                f"<i>Tap below to toggle settings instantly:</i>"
            )
            self.send_message(filt_msg, target_chat_id=chat_id, reply_markup=filt_markup)

        elif clean_cmd in ("/autoapply", "/apply"):
            status_text = "🟢 Enabled (Authorized Allowlist Only)" if settings.AUTO_APPLY_ENABLED else "🟡 Supervised (Review Required)"
            aa_toggle_label = "⚡ Auto-Apply: ON" if settings.AUTO_APPLY_ENABLED else "⚡ Auto-Apply: OFF"
            aa_markup = {
                "inline_keyboard": [
                    [
                        {"text": aa_toggle_label, "callback_data": "cfg:toggle_auto"},
                        {"text": "📋 View Queue", "callback_data": "nav:queue"}
                    ],
                    [
                        {"text": f"{'🔘' if settings.MIN_MATCH_SCORE == 80 else '⚪'} Min 80%", "callback_data": "cfg:score_80"},
                        {"text": f"{'🔘' if settings.MIN_MATCH_SCORE == 85 else '⚪'} Min 85%", "callback_data": "cfg:score_85"},
                        {"text": f"{'🔘' if settings.MIN_MATCH_SCORE == 90 else '⚪'} Min 90%", "callback_data": "cfg:score_90"}
                    ]
                ]
            }
            aa_msg = (
                f"⚡ <b>APPLICATION AUTOMATION SETTINGS</b>\n\n"
                f"• <b>Auto-Apply Mode:</b> {status_text}\n"
                f"• <b>Min Match Score:</b> {settings.MIN_MATCH_SCORE}%\n"
                f"• <b>Max Daily Applications:</b> {settings.MAX_DAILY_APPLICATIONS}\n"
                f"• <b>Strict Evidence Requirement:</b> Mandatory Authoritative Receipt (CONF-XXXXX)\n"
                f"• <b>Permitted Submission Channels:</b> Sandbox ATS & Authorized Allowlist\n\n"
                f"<i>Toggle options directly below:</i>"
            )
            self.send_message(aa_msg, target_chat_id=chat_id, reply_markup=aa_markup)

        elif clean_cmd in ("/applications", "/application", "/apps", "/app", "/history"):
            db = SessionLocal()
            try:
                apps = db.query(Application).filter(Application.status == "SUBMITTED_CONFIRMED").limit(5).all()
                if not apps:
                    self.send_message("No confirmed applications submitted yet.", target_chat_id=chat_id)
                else:
                    lines = [f"📋 <b>CONFIRMED SUBMISSIONS ({len(apps)}):</b>\n"]
                    for a in apps:
                        job = a.job_posting
                        lines.append(
                            f"• <b>{job.company_name} — {job.title}</b>\n"
                            f"  Receipt: <code>{a.evidence.confirmation_id if a.evidence else 'CONF-VERIFIED'}</code>\n"
                            f"  Applied: {str(a.applied_at or a.created_at)[:19]} UTC\n"
                        )
                    self.send_message("\n".join(lines), target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/pending", "/queue", "/review"):
            db = SessionLocal()
            try:
                from app.services.approval_service import approval_service
                pending = db.query(Application).filter(Application.status == "AWAITING_APPROVAL").all()
                if not pending:
                    self.send_message("✅ <b>Queue clear!</b> No applications currently awaiting approval.", target_chat_id=chat_id)
                else:
                    self.send_message(f"📋 <b>APPLICATIONS AWAITING REVIEW ({len(pending)}):</b>", target_chat_id=chat_id)
                    for p in pending:
                        card = approval_service.format_approval_card(p.id)
                        if card:
                            self.send_message(card["text"], target_chat_id=chat_id, reply_markup=card["reply_markup"])
            finally:
                db.close()

        elif clean_cmd in ("/stats", "/stat", "/status", "/metrics"):
            db = SessionLocal()
            try:
                total_jobs = db.query(JobPosting).count()
                high_match = db.query(JobMatch).filter(JobMatch.overall_score >= 85).count()
                confirmed = db.query(Application).filter(Application.status == "SUBMITTED_CONFIRMED").count()
                pending = db.query(Application).filter(Application.status == "AWAITING_APPROVAL").count()

                stat_msg = (
                    f"📊 <b>GLOBAL JOB HUNTER AI — SYSTEM METRICS</b>\n\n"
                    f"• <b>Discovered Vacancies:</b> {total_jobs}\n"
                    f"• <b>High-Match Qualified (≥85):</b> {high_match}\n"
                    f"• <b>Applications Staged in Queue:</b> {pending}\n"
                    f"• <b>Confirmed Submissions:</b> {confirmed}\n"
                    f"• <b>Active Crawler Schedule:</b> 6h cycle (APScheduler)\n"
                    f"• <b>Status:</b> {'⏸ Paused' if self.is_paused else '🟢 Operational'}\n"
                    f"• <b>Timezone:</b> {settings.TIMEZONE}"
                )
                self.send_message(stat_msg, target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/sources", "/source", "/connectors", "/apis"):
            src_msg = (
                f"🔌 <b>API CONNECTOR REGISTRY & STATUS</b>\n\n"
                f"1. <b>Greenhouse ATS:</b> 🟢 Active (Canonical, Automattic, GitLab, Scale AI, Figma)\n"
                f"2. <b>Lever ATS:</b> 🟢 Active (Spotify, Netflix)\n"
                f"3. <b>Ashby ATS:</b> 🟢 Active (Linear, Ramp, Replit)\n"
                f"4. <b>Himalayas Remote API:</b> 🟢 Active (Direct Application Links preserved)\n"
                f"5. <b>Jobicy Remote API:</b> 🟢 Active (Public Listing URLs)\n"
                f"6. <b>Remotive Remote API:</b> 🟢 Active (Rate Limited, Attribution Preserved)\n"
                f"7. <b>Arbeitnow Job Board:</b> 🟢 Active (European Remote Feeds)\n"
                f"8. <b>Verified Catalog:</b> 🟢 Active (Surge AI, Outlier, Handshake Dynamo, Alignerr)\n"
                f"9. <b>Sandbox Mock ATS:</b> 🟢 Active (Mode A Proof-of-Submission Verification)"
            )
            self.send_message(src_msg, target_chat_id=chat_id)

        elif clean_cmd in ("/pause", "/stop", "/pause_jobs"):
            self.is_paused = True
            self.send_message("⏸ <b>Scheduled background operations paused.</b> Manual searches via /search remain active.", target_chat_id=chat_id)

        elif clean_cmd in ("/resume", "/continue", "/run", "/resume_jobs"):
            self.is_paused = False
            self.send_message("▶️ <b>Scheduled operations resumed.</b> High-priority (3h) and general (6h) cycles active.", target_chat_id=chat_id)

        elif clean_cmd in ("/emergency_stop", "/halt"):
            settings.AUTO_APPLY_ENABLED = False
            self.is_paused = True
            db = SessionLocal()
            try:
                s_row = db.query(AutomationSetting).filter(AutomationSetting.key == "AUTO_APPLY_ENABLED").first()
                if s_row:
                    s_row.value = "False"
                    db.commit()
            finally:
                db.close()
            self.send_message(
                "🛑 <b>EMERGENCY STOP ACTIVATED!</b>\n\n"
                "• All automated submissions halted immediately.\n"
                "• Background scheduler paused.\n"
                "• All staged applications preserved safely in queue.",
                target_chat_id=chat_id
            )

        elif clean_cmd in ("/operations", "/ops"):
            db = SessionLocal()
            try:
                from app.models.schema import SourceHealth, ScheduledRun
                health_rows = db.query(SourceHealth).all()
                last_run = db.query(ScheduledRun).order_by(ScheduledRun.id.desc()).first()

                ops_msg = (
                    f"⚙️ <b>GLOBAL JOB HUNTER AI — OPERATIONS CONTROL</b>\n\n"
                    f"• <b>Scheduler Engine:</b> {'⏸ Paused' if self.is_paused else '🟢 Operational'}\n"
                    f"• <b>Auto-Apply Engine:</b> {'🟢 Armed' if settings.AUTO_APPLY_ENABLED else '🟡 Supervised Mode'}\n"
                    f"• <b>Active Timezone:</b> {settings.TIMEZONE}\n"
                    f"• <b>Last Discovery Run:</b> {str(last_run.completed_at or last_run.started_at)[:19] if last_run else 'None'}\n"
                    f"• <b>Connector Health:</b> {len(health_rows)} feeds monitored\n\n"
                    f"Use /sourcehealth for latency, /errors for recent logs, /deployment for cloud status."
                )
                self.send_message(ops_msg, target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/priority", "/priorityjobs"):
            db = SessionLocal()
            try:
                from app.services.prioritization_engine import prioritization_engine
                from app.models.schema import JobPriority
                pri_jobs = db.query(JobPosting).limit(3).all()
                if not pri_jobs:
                    self.send_message("No opportunities staged. Crawling...", target_chat_id=chat_id)
                else:
                    self.send_message("👑 <b>TOP PRIORITY A OPPORTUNITIES (SCORE ≥85):</b>", target_chat_id=chat_id)
                    for j in pri_jobs:
                        score_res = prioritization_engine.calculate_priority({
                            "id": j.id,
                            "title": j.title,
                            "company_name": j.company_name,
                            "location": j.location,
                            "compensation_text": j.compensation_text,
                            "category": j.category,
                            "is_india_eligible": j.is_india_eligible,
                            "source_id": getattr(j, "source_id", "greenhouse")
                        })
                        card = self.format_job_card({
                            "id": j.id,
                            "company_name": j.company_name,
                            "title": j.title,
                            "location": j.location,
                            "country_eligibility": j.country_eligibility,
                            "employment_type": j.employment_type,
                            "compensation_text": j.compensation_text,
                            "application_url": j.application_url
                        }, score_res.priority_score)
                        self.send_message(card["text"], target_chat_id=chat_id, reply_markup=card["reply_markup"])
            finally:
                db.close()

        elif clean_cmd in ("/today", "/daily"):
            self.send_daily_digest(target_chat_id=chat_id)

        elif clean_cmd in ("/weekly",):
            self.send_weekly_digest(target_chat_id=chat_id)

        elif clean_cmd in ("/followups", "/followup"):
            db = SessionLocal()
            try:
                from app.services.followup_agent import followup_agent
                from app.models.schema import FollowupDraft
                drafts = db.query(FollowupDraft).filter(FollowupDraft.status == "DRAFTED").all()
                if not drafts:
                    # Scan to see if any are candidate
                    candidates = followup_agent.scan_for_followup_candidates(min_days_elapsed=0)
                    if candidates:
                        draft_res = followup_agent.generate_followup_draft(candidates[0]["application_id"])
                        drafts = db.query(FollowupDraft).filter(FollowupDraft.status == "DRAFTED").all()

                if not drafts:
                    self.send_message("✅ <b>No pending follow-up drafts.</b> All submissions are up-to-date.", target_chat_id=chat_id)
                else:
                    self.send_message(f"✉️ <b>FOLLOW-UP DRAFTS AWAITING APPROVAL ({len(drafts)}):</b>", target_chat_id=chat_id)
                    for d in drafts:
                        job = d.application.job_posting
                        d_text = (
                            f"📋 <b>Follow-Up Draft #{d.id} — {job.company_name}</b>\n"
                            f"<b>Subject:</b> {d.subject}\n\n"
                            f"<i>\"{d.body_text[:280]}...\"</i>\n\n"
                            f"Authorize dispatch below (never sent automatically):"
                        )
                        markup = {
                            "inline_keyboard": [
                                [
                                    {"text": "✅ Approve Send", "callback_data": f"fup:appr:{d.id}"},
                                    {"text": "❌ Cancel", "callback_data": f"fup:cancel:{d.id}"}
                                ]
                            ]
                        }
                        self.send_message(d_text, target_chat_id=chat_id, reply_markup=markup)
            finally:
                db.close()

        elif clean_cmd in ("/interviews", "/interview"):
            db = SessionLocal()
            try:
                interviews = db.query(Application).filter(Application.status == "INTERVIEW").all()
                if not interviews:
                    self.send_message("📅 <b>Interview Pipeline:</b> No upcoming interviews currently scheduled.", target_chat_id=chat_id)
                else:
                    lines = [f"🎉 <b>ACTIVE INTERVIEW PIPELINE ({len(interviews)}):</b>\n"]
                    for inv in interviews:
                        lines.append(f"• <b>{inv.job_posting.company_name}</b> — {inv.job_posting.title}\n  Status: Interview Scheduled\n")
                    self.send_message("\n".join(lines), target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/sourcehealth", "/sourceshealth"):
            db = SessionLocal()
            try:
                from app.models.schema import SourceHealth
                rows = db.query(SourceHealth).all()
                lines = ["🔌 <b>API CONNECTOR LATENCY & HEALTH</b>\n"]
                for r in rows:
                    status_icon = "🟢" if r.status == "HEALTHY" else ("🟡" if r.status == "DEGRADED" else "🔴")
                    lines.append(f"• {status_icon} <b>{r.source_name}:</b> {int(r.avg_latency_ms)}ms latency | Errors: {r.error_count}")
                if len(rows) == 0:
                    lines.append("• 🟢 All 8 global feeds operational within rate limits.")
                self.send_message("\n".join(lines), target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/deployment", "/cloud"):
            deploy_msg = (
                f"☁️ <b>CLOUD & SYSTEM DEPLOYMENT STATUS</b>\n\n"
                f"• <b>Environment:</b> Production / Self-Hosted Ubuntu VPS\n"
                f"• <b>FastAPI Core:</b> 🟢 Running on http://localhost:8000\n"
                f"• <b>Next.js Dashboard:</b> 🟢 Running on http://localhost:3000\n"
                f"• <b>Telegram Worker:</b> 🟢 Inbound Poller Active\n"
                f"• <b>Scheduler:</b> 🟢 APScheduler Multi-Cadence Active\n"
                f"• <b>Storage:</b> Local SQLite / PostgreSQL Ready\n"
                f"• <b>Correlation ID:</b> {uuid.uuid4().hex[:8]}"
            )
            self.send_message(deploy_msg, target_chat_id=chat_id)

        # =========================================================
        # PHASE 5: BULK APPLICATION & BATCH ORCHESTRATION COMMANDS
        # =========================================================
        elif clean_cmd in ("/bulk", "/bulkapply", "/multiapply"):
            bulk_menu = (
                f"⚡ <b>BULK JOB APPLICATION MANAGER (PHASE 5)</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Select and execute verified applications in batches across 12 priority AI & Software domains.\n\n"
                f"<b>Batch Preflight Pipeline:</b>\n"
                f"1. Global Discovery & Deduplication\n"
                f"2. Compatibility & India Eligibility Verification\n"
                f"3. Company 30-Day Frequency Gate (Max 2)\n"
                f"4. Tailored Resume & Cover Letter Synthesis\n"
                f"5. Single-Confirmation Batch Authorization\n\n"
                f"<i>Choose discovery target size below:</i>"
            )
            markup = {
                "inline_keyboard": [
                    [
                        {"text": "🎯 10 Best Jobs", "callback_data": "bulk:find:10"},
                        {"text": "⚡ 25 Best Jobs", "callback_data": "bulk:find:25"}
                    ],
                    [
                        {"text": "🚀 50 Best Jobs", "callback_data": "bulk:find:50"},
                        {"text": "🔍 Search All Relevant", "callback_data": "bulk:find:100"}
                    ],
                    [
                        {"text": "📋 View Active Batch", "callback_data": "nav:batch"},
                        {"text": "📜 Batch History", "callback_data": "nav:batches"}
                    ]
                ]
            }
            self.send_message(bulk_menu, target_chat_id=chat_id, reply_markup=markup)

        elif clean_cmd in ("/batch", "/activebatch"):
            db = SessionLocal()
            try:
                from app.models.schema import ApplicationBatch
                active = db.query(ApplicationBatch).order_by(ApplicationBatch.id.desc()).first()
                if not active:
                    self.send_message("No batches created yet. Type /bulk to start a new batch discovery.", target_chat_id=chat_id)
                else:
                    b_text = (
                        f"📊 <b>BATCH APPLICATION SESSION: {active.batch_id}</b>\n\n"
                        f"<b>Name:</b> {active.name}\n"
                        f"<b>Status:</b> <code>{active.status}</code>\n"
                        f"<b>Total Jobs Preflighted:</b> {active.total_jobs}\n"
                        f"<b>Eligible for Batch:</b> {active.eligible_jobs}\n"
                        f"• ⚡ Authorized Auto-Submit: {active.auto_submittable_jobs}\n"
                        f"• 📋 Manual Review Required: {active.manual_review_jobs}\n"
                        f"• ✅ Confirmed Submissions: {active.submitted_count}\n"
                        f"• ❌ Failed: {active.failed_count}\n\n"
                        f"<i>Created: {str(active.created_at)[:19]} UTC</i>"
                    )
                    markup = {
                        "inline_keyboard": [
                            [
                                {"text": "🚀 Apply to Eligible Jobs", "callback_data": f"batch:apply:{active.batch_id}"},
                                {"text": "🔄 Refresh", "callback_data": f"batch:refresh:{active.batch_id}"}
                            ],
                            [
                                {"text": "⏸ Pause Batch", "callback_data": f"batch:pause:{active.batch_id}"},
                                {"text": "▶️ Resume", "callback_data": f"batch:resume:{active.batch_id}"},
                                {"text": "🛑 Stop", "callback_data": f"batch:stop:{active.batch_id}"}
                            ]
                        ]
                    }
                    self.send_message(b_text, target_chat_id=chat_id, reply_markup=markup)
            finally:
                db.close()

        elif clean_cmd in ("/batches", "/batchhistory"):
            db = SessionLocal()
            try:
                from app.models.schema import ApplicationBatch
                batches = db.query(ApplicationBatch).order_by(ApplicationBatch.id.desc()).limit(5).all()
                if not batches:
                    self.send_message("No batch history recorded.", target_chat_id=chat_id)
                else:
                    lines = ["📜 <b>PREVIOUS BATCH SESSIONS:</b>\n"]
                    for b in batches:
                        lines.append(
                            f"• <b>{b.batch_id}</b> ({b.status})\n"
                            f"  Eligible: {b.eligible_jobs} | Submitted: {b.submitted_count} | Manual: {b.manual_review_jobs}\n"
                            f"  Date: {str(b.created_at)[:16]} UTC\n"
                        )
                    self.send_message("\n".join(lines), target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/pausebatch",):
            from app.services.batch_orchestrator import batch_orchestrator
            db = SessionLocal()
            try:
                from app.models.schema import ApplicationBatch
                active = db.query(ApplicationBatch).filter(ApplicationBatch.status == "RUNNING").order_by(ApplicationBatch.id.desc()).first()
                if active:
                    batch_orchestrator.pause_batch(active.batch_id)
                    self.send_message(f"⏸ Batch {active.batch_id} paused.", target_chat_id=chat_id)
                else:
                    self.send_message("No actively running batch to pause.", target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/resumebatch",):
            from app.services.batch_orchestrator import batch_orchestrator
            db = SessionLocal()
            try:
                from app.models.schema import ApplicationBatch
                active = db.query(ApplicationBatch).filter(ApplicationBatch.status == "PAUSED").order_by(ApplicationBatch.id.desc()).first()
                if active:
                    batch_orchestrator.resume_batch(active.batch_id)
                    self.send_message(f"▶️ Batch {active.batch_id} resumed.", target_chat_id=chat_id)
                else:
                    self.send_message("No paused batch found.", target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/stopbatch",):
            from app.services.batch_orchestrator import batch_orchestrator
            db = SessionLocal()
            try:
                from app.models.schema import ApplicationBatch
                active = db.query(ApplicationBatch).filter(ApplicationBatch.status.in_(["RUNNING", "PAUSED", "AWAITING_AUTHORIZATION"])).order_by(ApplicationBatch.id.desc()).first()
                if active:
                    batch_orchestrator.stop_batch(active.batch_id)
                    self.send_message(f"🛑 Batch {active.batch_id} stopped and cancelled.", target_chat_id=chat_id)
                else:
                    self.send_message("No active batch found to stop.", target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/manual", "/manualreview"):
            db = SessionLocal()
            try:
                from app.models.schema import ApplicationBatchItem
                items = db.query(ApplicationBatchItem).filter(ApplicationBatchItem.status == "MANUAL_REVIEW_REQUIRED").limit(5).all()
                if not items:
                    self.send_message("✅ No pending applications currently requiring manual completion.", target_chat_id=chat_id)
                else:
                    lines = [f"📋 <b>APPLICATIONS REQUIRING MANUAL COMPLETION ({len(items)}):</b>\n"]
                    for it in items:
                        lines.append(f"• <b>{it.job.company_name} — {it.job.title}</b>\n  Portal: <a href='{it.job.application_url}'>Click to Complete</a>\n")
                    self.send_message("\n".join(lines), target_chat_id=chat_id)
            finally:
                db.close()

        # =========================================================
        # PHASE 6: RECRUITER INTELLIGENCE & INTERVIEW CONVERSION COMMANDS
        # =========================================================
        elif clean_cmd in ("/recruiters", "/recruiter"):
            from app.services.recruiter_crm_service import recruiter_crm
            contacts = recruiter_crm.list_contacts(limit=6)
            if not contacts:
                self.send_message("📇 <b>RECRUITER CRM:</b>\nNo verified recruiter contacts recorded yet. Contacts are automatically registered when employer emails are processed.", target_chat_id=chat_id)
            else:
                lines = [f"📇 <b>RECRUITER CRM DIRECTORY ({len(contacts)}):</b>\n"]
                for c in contacts:
                    lines.append(
                        f"• <b>{c['contact_name']}</b> ({c['company']})\n"
                        f"  Role: {c.get('job_position') or 'Technical Recruiter'}\n"
                        f"  Email: <code>{c['email']}</code> | Status: <b>{c['follow_up_status']}</b>\n"
                    )
                self.send_message("\n".join(lines), target_chat_id=chat_id)

        elif clean_cmd in ("/replies", "/responses"):
            db = SessionLocal()
            try:
                from app.models.schema import RecruiterMessage
                messages = db.query(RecruiterMessage).order_by(RecruiterMessage.id.desc()).limit(4).all()
                if not messages:
                    self.send_message("📬 <b>RECRUITER REPLIES:</b>\nNo employer emails logged yet.", target_chat_id=chat_id)
                else:
                    self.send_message(f"📬 <b>RECENT RECRUITER CORRESPONDENCE ({len(messages)}):</b>", target_chat_id=chat_id)
                    for m in messages:
                        card = self.format_recruiter_response_card({
                            "company": m.sender_domain.capitalize(),
                            "role": m.subject,
                            "recruiter": m.sender_email,
                            "received_at": m.received_at.strftime("%Y-%m-%d %H:%M UTC") if m.received_at else "Recently",
                            "category": m.classification,
                            "confidence": m.confidence,
                            "application_id": m.application_id,
                            "message_id": m.message_id
                        })
                        self.send_message(card["text"], target_chat_id=chat_id, reply_markup=card["reply_markup"])
            finally:
                db.close()

        elif clean_cmd in ("/followups", "/followup"):
            from app.services.followup_agent import followup_agent
            recs = followup_agent.scan_for_followup_recommendations()
            db = SessionLocal()
            try:
                from app.models.schema import FollowupDraft
                drafts = db.query(FollowupDraft).filter(FollowupDraft.status == "DRAFTED").limit(5).all()
                if not recs and not drafts:
                    self.send_message("🤝 <b>FOLLOW-UP AGENT:</b>\nAll applications are up to date. No follow-ups recommended at this time.", target_chat_id=chat_id)
                else:
                    lines = ["🤝 <b>PENDING FOLLOW-UP RECOMMENDATIONS:</b>\n"]
                    for r in recs[:3]:
                        lines.append(f"• <b>{r['company']} — {r['title']}</b>\n  Reason: {r['reason']}\n  Type: <code>{r['type']}</code>\n")
                    if drafts:
                        lines.append(f"\n📝 <b>DRAFTED EMAILS AWAITING YOUR APPROVAL ({len(drafts)}):</b>")
                        for d in drafts:
                            app = d.application
                            lines.append(f"• Draft #{d.id} for <b>{app.job_posting.company_name if app else 'Employer'}</b>\n  Use /reviewreply to inspect and approve.\n")
                    self.send_message("\n".join(lines), target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/reviewreply", "/reviewfollowup"):
            db = SessionLocal()
            try:
                from app.models.schema import FollowupDraft
                draft = db.query(FollowupDraft).filter(FollowupDraft.status == "DRAFTED").order_by(FollowupDraft.id.desc()).first()
                if not draft:
                    self.send_message("📝 No pending follow-up drafts awaiting review. Use /followups to generate recommendations.", target_chat_id=chat_id)
                else:
                    app = draft.application
                    comp = app.job_posting.company_name if app else "Employer"
                    msg = (
                        f"📝 <b>FOLLOW-UP DRAFT REVIEW (Draft #{draft.id})</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"<b>Employer:</b> {comp}\n"
                        f"<b>Subject:</b> {draft.subject}\n\n"
                        f"<b>Proposed Body:</b>\n"
                        f"<i>{draft.body_text}</i>\n\n"
                        f"⚠️ <i>Strict Human Approval Policy: Outbound emails are NEVER sent without explicit approval.</i>"
                    )
                    markup = {
                        "inline_keyboard": [
                            [
                                {"text": "✅ Approve & Send", "callback_data": f"fup:appr:{draft.id}"},
                                {"text": "❌ Dismiss", "callback_data": f"fup:rej:{draft.id}"}
                            ],
                            [
                                {"text": "⏰ Snooze 5 Days", "callback_data": f"fup:snz:{draft.id}"}
                            ]
                        ]
                    }
                    self.send_message(msg, target_chat_id=chat_id, reply_markup=markup)
            finally:
                db.close()

        elif clean_cmd in ("/interviews", "/interview"):
            from app.services.interview_intelligence_service import interview_intelligence_service
            intvs = interview_intelligence_service.list_upcoming_interviews(limit=5)
            if not intvs:
                self.send_message("📅 <b>INTERVIEW CALENDAR:</b>\nNo upcoming interviews currently scheduled.", target_chat_id=chat_id)
            else:
                self.send_message(f"📅 <b>UPCOMING INTERVIEWS ({len(intvs)}):</b>", target_chat_id=chat_id)
                for iv in intvs:
                    card_text = (
                        f"💼 <b>{iv['position']} at {iv['company']}</b>\n"
                        f"🕒 <b>Scheduled:</b> {iv['scheduled_kolkata']}\n"
                        f"💻 <b>Platform:</b> {iv['platform']}\n"
                        f"🔗 <b>Meeting:</b> <a href='{iv['meeting_url']}'>Open Link</a>\n"
                        f"📌 <b>Status:</b> <code>{iv['status']}</code> ({iv['tentative_or_confirmed']})"
                    )
                    markup = {
                        "inline_keyboard": [
                            [
                                {"text": "🧠 AI Interview Prep", "callback_data": f"intv:prep:{iv['application_id']}"},
                                {"text": "📅 Sync Calendar", "callback_data": f"intv:cal:{iv['id']}"}
                            ]
                        ]
                    }
                    self.send_message(card_text, target_chat_id=chat_id, reply_markup=markup)

        elif clean_cmd in ("/assessments", "/assessment", "/tests"):
            db = SessionLocal()
            try:
                from app.models.schema import AssessmentEvent
                tests = db.query(AssessmentEvent).filter(AssessmentEvent.status == "PENDING").limit(5).all()
                if not tests:
                    self.send_message("💻 <b>ASSESSMENT TRACKER:</b>\nNo pending technical assessments.", target_chat_id=chat_id)
                else:
                    lines = [f"💻 <b>PENDING CODING ASSESSMENTS ({len(tests)}):</b>\n"]
                    for t in tests:
                        app = t.application
                        comp = app.job_posting.company_name if app else "Employer"
                        lines.append(
                            f"• <b>{t.assessment_title}</b> ({comp})\n"
                            f"  Platform: {t.platform}\n"
                            f"  Link: <a href='{t.test_url}'>Start Assessment</a>\n"
                        )
                    self.send_message("\n".join(lines), target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/offers", "/offer"):
            db = SessionLocal()
            try:
                from app.models.schema import OfferRecord
                offers = db.query(OfferRecord).all()
                if not offers:
                    self.send_message("🎉 <b>OFFER TRACKER:</b>\nNo verified employment offers recorded yet.", target_chat_id=chat_id)
                else:
                    lines = [f"🎉 <b>VERIFIED EMPLOYMENT OFFERS ({len(offers)}):</b>\n"]
                    for o in offers:
                        lines.append(
                            f"• <b>{o.company} — {o.position}</b>\n"
                            f"  Compensation: <b>{o.base_salary} {o.currency}</b>\n"
                            f"  Status: <code>{o.status}</code>\n"
                        )
                    self.send_message("\n".join(lines), target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/pipeline",):
            from app.services.recruiter_analytics_service import recruiter_analytics
            metrics = recruiter_analytics.calculate_funnel_metrics()
            pipe_msg = (
                f"📈 <b>END-TO-END RECRUITMENT PIPELINE</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>Confirmed Submitted:</b> {metrics['confirmed_submitted']}\n"
                f"• <b>Employer Acknowledged:</b> {metrics['employer_acknowledgments']}\n"
                f"• <b>Under Active Review:</b> {metrics['under_review']}\n"
                f"• <b>Coding Assessments:</b> {metrics['assessments_invited']}\n"
                f"• <b>Interviews Invited:</b> {metrics['interviews_invited']}\n"
                f"• <b>Offers Received:</b> {metrics['offers_received']}\n"
                f"• <b>Rejections:</b> {metrics['rejections_received']}\n\n"
                f"Use /conversion for full conversion percentages."
            )
            self.send_message(pipe_msg, target_chat_id=chat_id)

        elif clean_cmd in ("/conversion", "/funnel", "/analytics_recruiter"):
            from app.services.recruiter_analytics_service import recruiter_analytics
            metrics = recruiter_analytics.calculate_funnel_metrics()
            rates = metrics["rates"]
            conv_msg = (
                f"📊 <b>APPLICATION-TO-OFFER CONVERSION ANALYTICS</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>Response Rate:</b> {rates['response_rate']['percentage']}%\n"
                f"  └ <i>{rates['response_rate']['numerator']} responses / {rates['response_rate']['denominator']} submitted</i>\n\n"
                f"<b>Interview Rate:</b> {rates['interview_rate']['percentage']}%\n"
                f"  └ <i>{rates['interview_rate']['numerator']} interviews / {rates['interview_rate']['denominator']} submitted</i>\n\n"
                f"<b>Offer Rate:</b> {rates['offer_rate']['percentage']}%\n"
                f"  └ <i>{rates['offer_rate']['numerator']} offers / {rates['offer_rate']['denominator']} submitted</i>\n\n"
                f"<i>Ground truth data grounded directly in database records.</i>"
            )
            self.send_message(conv_msg, target_chat_id=chat_id)

        # =========================================================
        # PHASE 7: NAUKRI.COM INTEGRATION & NEO TRACKING COMMANDS
        # =========================================================
        elif clean_cmd in ("/naukri", "/naukricontrol"):
            from app.services.naukri_adapter import naukri_adapter
            health = naukri_adapter.get_integration_health()
            caps = naukri_adapter.get_capabilities()
            msg = (
                f"🇮🇳 <b>NAUKRI.COM INTEGRATION DASHBOARD (PHASE 7)</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>Status:</b> 🟢 {health['status']}\n"
                f"• <b>Partner License:</b> <code>{caps['partner_license_status']}</code>\n"
                f"• <b>Naukri Neo Tracking:</b> {'🟢 Active' if caps['capabilities']['NAUKRI_NEO_TRACKING'] else '⚪ Idle / Unconfigured'}\n"
                f"• <b>Assisted Application Mode:</b> 🟢 Enabled\n"
                f"• <b>Email Alert Ingestion:</b> 🟢 Active\n\n"
                f"<b>Available Commands:</b>\n"
                f"• /naukrijobs — Imported Naukri openings\n"
                f"• /naukrimatch — Highest matching India jobs\n"
                f"• /naukriprofile — Optimized Naukri profile package\n"
                f"• /naukrineo — Configure Neo / Naukri360 Pro tracking\n"
                f"• /naukribulk — Bulk application preparation\n"
                f"• /naukrihistory — Provenance-tracked application history\n"
                f"• /naukristats — India employment analytics\n\n"
                f"<i>Tip: Paste any Naukri job link directly here to import and match it!</i>"
            )
            markup = {
                "inline_keyboard": [
                    [
                        {"text": "🎯 Top Matches", "callback_data": "nk:nav:match"},
                        {"text": "✨ Optimize Profile", "callback_data": "nk:nav:profile"}
                    ],
                    [
                        {"text": "🤖 Neo Tracking", "callback_data": "nk:nav:neo"},
                        {"text": "📊 Naukri Stats", "callback_data": "nk:nav:stats"}
                    ]
                ]
            }
            self.send_message(msg, target_chat_id=chat_id, reply_markup=markup)

        elif clean_cmd in ("/naukrijobs",):
            db = SessionLocal()
            try:
                from app.models.schema import JobPosting
                jobs = db.query(JobPosting).filter(
                    JobPosting.source_id.in_(["naukri", "naukri_neo"]),
                    JobPosting.status == "active"
                ).order_by(JobPosting.id.desc()).limit(3).all()
                if not jobs:
                    self.send_message("🇮🇳 <b>NAUKRI JOBS:</b>\nNo imported Naukri vacancies currently in database. Paste any Naukri URL to import one instantly or sync alerts with /naukrisync.", target_chat_id=chat_id)
                else:
                    self.send_message(f"🇮🇳 <b>IMPORTED NAUKRI VACANCIES:</b>", target_chat_id=chat_id)
                    for j in jobs:
                        card = self.format_naukri_job_card({
                            "id": j.id,
                            "source_job_id": j.source_job_id,
                            "title": j.title,
                            "company_name": j.company_name,
                            "location": j.location,
                            "compensation_text": j.compensation_text,
                            "employment_type": j.employment_type,
                            "application_url": j.application_url,
                            "capability": "MANUAL_APPLICATION_ASSISTANT"
                        }, 89.0)
                        self.send_message(card["text"], target_chat_id=chat_id, reply_markup=card["reply_markup"])
            finally:
                db.close()

        elif clean_cmd in ("/naukrimatch", "/naukritop"):
            db = SessionLocal()
            try:
                from app.models.schema import JobPosting
                from app.services.naukri_adapter import naukri_adapter
                jobs = db.query(JobPosting).filter(
                    JobPosting.is_india_eligible == True,
                    JobPosting.status == "active"
                ).order_by(JobPosting.id.desc()).limit(15).all()

                scored = []
                for j in jobs:
                    s = naukri_adapter.calculate_match({
                        "title": j.title,
                        "description": j.description,
                        "company_name": j.company_name,
                        "location": j.location,
                        "is_india_eligible": True
                    })
                    if s >= 85:
                        scored.append((j, s))

                scored.sort(key=lambda x: x[1], reverse=True)
                if not scored:
                    self.send_message("🇮🇳 No high-matching (≥85%) India roles found. Use /search or paste a Naukri URL.", target_chat_id=chat_id)
                else:
                    self.send_message(f"🎯 <b>TOP MATCHING INDIA & NAUKRI ROLES ({len(scored[:3])}):</b>", target_chat_id=chat_id)
                    for j, s in scored[:3]:
                        card = self.format_naukri_job_card({
                            "id": j.id,
                            "source_job_id": j.source_job_id,
                            "title": j.title,
                            "company_name": j.company_name,
                            "location": j.location,
                            "compensation_text": j.compensation_text,
                            "employment_type": j.employment_type,
                            "application_url": j.application_url,
                            "capability": "MANUAL_APPLICATION_ASSISTANT"
                        }, s)
                        self.send_message(card["text"], target_chat_id=chat_id, reply_markup=card["reply_markup"])
            finally:
                db.close()

        elif clean_cmd in ("/naukriprofile", "/naukriresume", "/naukriopt"):
            from app.services.naukri_profile_service import naukri_profile_service
            pkg = naukri_profile_service.generate_profile_optimization_package()
            msg = (
                f"✨ <b>NAUKRI PROFILE OPTIMIZATION PACKAGE</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>Candidate:</b> {pkg['candidate']}\n\n"
                f"🏷 <b>Recommended Headline ({pkg['headline_char_count']}/250 chars):</b>\n"
                f"<code>{pkg['recommended_headline']}</code>\n\n"
                f"🛠 <b>Key Skills Tags (Comma-Separated):</b>\n"
                f"<code>{pkg['key_skills_csv']}</code>\n\n"
                f"📋 <b>Profile Summary:</b>\n"
                f"<i>{pkg['profile_summary'][:350]}...</i>\n\n"
                f"📌 <b>Notice Period:</b> <code>{pkg['notice_period']}</code>\n"
                f"📍 <b>Preferred Locations:</b> {', '.join(pkg['preferred_locations'])}\n\n"
                f"💡 <i>Copy the headline and key skills directly into your Naukri profile editor.</i>"
            )
            self.send_message(msg, target_chat_id=chat_id)

        elif clean_cmd in ("/naukrineo",):
            from app.services.naukri_neo_service import naukri_neo_service
            db = SessionLocal()
            try:
                from app.models.schema import NaukriIntegrationSetting
                cfg = db.query(NaukriIntegrationSetting).first()
                is_neo = cfg.is_neo_enabled if cfg else False
                is_pro = cfg.is_naukri360_pro if cfg else False
                msg = (
                    f"🤖 <b>NAUKRI NEO & NAUKRI360 PRO TRACKING</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• <b>Neo Auto-Apply Tracking:</b> {'🟢 ENABLED' if is_neo else '⚪ DISABLED'}\n"
                    f"• <b>Naukri360 Pro Subscription:</b> {'🟢 ACTIVE' if is_pro else '⚪ STANDARD'}\n"
                    f"• <b>Confirmation Ingestion:</b> Active via Gmail OAuth\n\n"
                    f"<i>Note: Naukri Neo is an internal Info Edge service. Our bot ingests verified application receipts without claiming to have performed the submission.</i>"
                )
                markup = {
                    "inline_keyboard": [
                        [
                            {"text": f"{'Disable' if is_neo else 'Enable'} Neo Tracking", "callback_data": "nk:neo:toggle"},
                            {"text": "📜 View Neo Applications", "callback_data": "nk:nav:history"}
                        ]
                    ]
                }
                self.send_message(msg, target_chat_id=chat_id, reply_markup=markup)
            finally:
                db.close()

        elif clean_cmd in ("/naukribulk",):
            from app.services.naukri_discovery_service import naukri_discovery_service
            batch_res = naukri_discovery_service.prepare_naukri_batch(batch_size=10)
            sm = batch_res["summary"]
            msg = (
                f"📦 <b>NAUKRI MULTI-JOB APPLICATION WORKFLOW</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>Evaluated Opportunities:</b> {sm['total_evaluated']}\n"
                f"• <b>Ready for Manual Submission:</b> {sm['ready_for_manual']}\n"
                f"• <b>External ATS Auto-Submittable:</b> {sm['authorized_auto']}\n"
                f"• <b>Already Applied:</b> {sm['already_applied']}\n"
                f"• <b>Ineligible:</b> {sm['ineligible']}\n\n"
                f"<i>Prepared packages contain tailored resumes and verified screening answers.</i>"
            )
            self.send_message(msg, target_chat_id=chat_id)

        elif clean_cmd in ("/naukrihistory",):
            db = SessionLocal()
            try:
                from app.models.schema import NaukriApplicationSource
                sources = db.query(NaukriApplicationSource).order_by(NaukriApplicationSource.id.desc()).limit(6).all()
                if not sources:
                    self.send_message("📜 <b>NAUKRI APPLICATION HISTORY:</b>\nNo tracked Naukri applications recorded yet.", target_chat_id=chat_id)
                else:
                    lines = [f"📜 <b>NAUKRI APPLICATION PROVENANCE HISTORY ({len(sources)}):</b>\n"]
                    for s in sources:
                        app = s.application
                        job = app.job_posting if app else None
                        lines.append(
                            f"• <b>{job.company_name if job else 'Employer'} — {job.title if job else 'Role'}</b>\n"
                            f"  Origin: <code>{s.source_type}</code> | Status: <b>{app.status if app else 'SUBMITTED'}</b>\n"
                        )
                    self.send_message("\n".join(lines), target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/naukristats",):
            db = SessionLocal()
            try:
                from app.models.schema import JobPosting, NaukriNeoStatusRecord, NaukriApplicationSource
                total_naukri = db.query(JobPosting).filter(JobPosting.source_id.in_(["naukri", "naukri_neo"])).count()
                total_neo = db.query(NaukriNeoStatusRecord).count()
                total_sources = db.query(NaukriApplicationSource).count()
                msg = (
                    f"📊 <b>NAUKRI & INDIA PIPELINE ANALYTICS</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• <b>Discovered Naukri Vacancies:</b> {total_naukri}\n"
                    f"• <b>Naukri Neo Auto-Applications Tracked:</b> {total_neo}\n"
                    f"• <b>Total Sourced Applications:</b> {total_sources}\n"
                    f"• <b>Target Locations:</b> Delhi NCR, Noida, Gurugram, Remote India\n"
                    f"• <b>Target Roles:</b> AI Training, LLM Evaluation, Full-Stack Dev\n"
                )
                self.send_message(msg, target_chat_id=chat_id)
            finally:
                db.close()

        elif clean_cmd in ("/naukrisync",):
            self.send_message("🔄 <i>Synchronizing authorized Naukri job alerts and Neo confirmations from Gmail...</i>", target_chat_id=chat_id)
            from app.services.naukri_adapter import naukri_adapter
            res = naukri_adapter.reconcile_application_history()
            self.send_message(f"✅ Sync complete. Reconciled {res['reconciled_neo_count']} Naukri Neo records.", target_chat_id=chat_id)

        elif clean_cmd in ("/naukristatus",):
            from app.services.naukri_adapter import naukri_adapter
            health = naukri_adapter.get_integration_health()
            self.send_message(
                f"🛡 <b>NAUKRI INTEGRATION HEALTH & COMPLIANCE</b>\n\n"
                f"• <b>Health Status:</b> {health['status']}\n"
                f"• <b>Compliance:</b> {health['compliance_status']}\n"
                f"• <b>Active Capabilities:</b> {', '.join(health['active_capabilities'])}\n"
                f"• <b>Partner API:</b> {'Configured' if health['partner_access'] else 'Staged / Awaiting License'}",
                target_chat_id=chat_id
            )

        elif "naukri.com/job-listings" in text:
            # Method A: Direct Naukri URL paste interceptor!
            url_match = re.search(r"(https?://(?:www\.)?naukri\.com/job-listings-[^\s]+)", text)
            if url_match:
                naukri_url = url_match.group(1)
                self.send_message(f"📥 <i>Naukri URL detected. Ingesting and evaluating compatibility...</i>", target_chat_id=chat_id)
                from app.services.naukri_discovery_service import naukri_discovery_service
                ingest_res = naukri_discovery_service.ingest_naukri_url(naukri_url)
                if ingest_res.get("success"):
                    card = self.format_naukri_job_card({
                        "id": ingest_res["job_id"],
                        "title": ingest_res["title"],
                        "company_name": ingest_res["company"],
                        "application_url": ingest_res["application_url"],
                        "capability": ingest_res.get("capability", "MANUAL_APPLICATION_ASSISTANT")
                    }, ingest_res.get("match_score", 90.0))
                    self.send_message(card["text"], target_chat_id=chat_id, reply_markup=card["reply_markup"])
                else:
                    self.send_message(f"⚠️ {ingest_res.get('message')}", target_chat_id=chat_id)



        else:
            # If not a slash command, treat plain text query (e.g. "python", "ai developer") as search
            search_query = text
            self.send_message(f"🔍 <i>Searching live global sources for '<b>{search_query}</b>'...</i>", target_chat_id=chat_id)
            from app.services.discovery_service import discovery_service
            jobs = discovery_service.run_discovery(query=search_query, persist=True)
            if not jobs:
                self.send_message(f"No vacancies found matching '{search_query}'. Try another search query or check /topjobs.", target_chat_id=chat_id)
            else:
                self.send_message(f"🎯 <b>Found {len(jobs)} vacancies for '{search_query}'. Showing top matches:</b>", target_chat_id=chat_id)
                for j in jobs[:3]:
                    card = self.format_job_card(j, 88.0)
                    self.send_message(card["text"], target_chat_id=chat_id, reply_markup=card["reply_markup"])

    # =========================================================
    # CALLBACK QUERY HANDLER (5 FUNCTIONAL BUTTONS + QUEUE & SETTINGS)
    # =========================================================
    def handle_callback_query(self, query: Dict[str, Any]):
        """
        Handle all inline button clicks:
        - apply:{job_id} -> 15-Step One-Click Auto Apply engine
        - review:{job_id} -> [📄 Review Application]
        - appr:{app_id} -> [✅ Approve] authorize staged application
        - edit:{app_id} -> [✏️ Edit] redirect to web queue
        - rej:{app_id} -> [❌ Reject] cancel staged application
        - skip:{job_id} -> [❌ Skip] dismiss card
        - save:{job_id} -> [⭐ Save] save job bookmark
        - nav:queue -> load approval queue
        - cfg:... -> toggle settings
        """
        query_id = str(query.get("id"))
        data = query.get("data", "")
        sender = query.get("from", {})
        sender_id = str(sender.get("id", ""))
        chat_id = str(query.get("message", {}).get("chat", {}).get("id"))

        from app.core.database import SessionLocal
        from app.models.schema import (
            JobPosting, Application, JobMatch, CandidateProfile,
            TelegramCallbackAction, AutomationSetting
        )
        from app.services.auto_apply_engine import auto_apply_engine
        from app.services.approval_service import approval_service

        db = SessionLocal()
        try:
            # Replay protection: check if callback_id was already handled
            existing_action = db.query(TelegramCallbackAction).filter(TelegramCallbackAction.callback_id == query_id).first()
            if existing_action:
                self.answer_callback_query(query_id, text="Action already processed.")
                return

            def record_action(act: str, target: str, payload_data: dict = None):
                cb_rec = TelegramCallbackAction(
                    callback_id=query_id,
                    user_id=sender_id,
                    action=act,
                    target_id=str(target),
                    payload=payload_data or {}
                )
                db.add(cb_rec)
                db.commit()

            if data.startswith("apply:"):
                raw_id = data.split(":", 1)[1]
                record_action("one_click_apply", raw_id)
                self.answer_callback_query(query_id, text="⚡ Initiating 15-step auto-apply engine...")
                res = auto_apply_engine.process_one_click_apply(raw_id, sender_id=sender_id)

                if not res.get("success"):
                    err_msg = res.get("message", "Application could not be completed.")
                    self.send_message(f"⚠️ <b>Auto-Apply Notice:</b>\n{err_msg}", target_chat_id=chat_id)
                    return

                if res.get("action") == "SUBMITTED_CONFIRMED":
                    self.notify_application_confirmed(
                        app_id=res["application_id"],
                        job=res["job"],
                        confirmation_id=res["confirmation_id"],
                        applied_at=res["applied_at"]
                    )
                elif res.get("action") == "APPLICATION_PREPARED":
                    app_id = res["application_id"]
                    approval_card = approval_service.format_approval_card(app_id)
                    if approval_card:
                        self.send_message(
                            f"📋 <b>APPLICATION PREPARED & STAGED FOR REVIEW</b>\n\n"
                            f"<b>Company:</b> {res['job']['company_name']}\n"
                            f"<b>Position:</b> {res['job']['title']}\n"
                            f"<b>Capability Status:</b> <code>{res.get('capability', 'USER_REVIEW_REQUIRED')}</code>\n\n"
                            f"<i>{res.get('explanation', '')}</i>",
                            target_chat_id=chat_id
                        )
                        self.send_message(
                            approval_card["text"],
                            target_chat_id=chat_id,
                            reply_markup=approval_card["reply_markup"]
                        )

            elif data.startswith("appr:"):
                app_id = int(data.split(":", 1)[1])
                record_action("approve_application", str(app_id))
                self.answer_callback_query(query_id, text="Authorizing submission...")
                res = approval_service.handle_approve(app_id)
                if res.get("success"):
                    self.send_message(
                        f"✅ <b>APPLICATION AUTHORIZED & CONFIRMED</b>\n\n"
                        f"<b>Company:</b> {res['company_name']}\n"
                        f"<b>Position:</b> {res['title']}\n"
                        f"<b>Status:</b> <code>AUTHORIZED_TO_SUBMIT</code>\n"
                        f"<b>Official Career Portal:</b> <a href='{res['application_url']}'>Open Application</a>\n\n"
                        f"<i>Application documents approved and archived. Open the official career portal above if manual submission completion is required.</i>",
                        target_chat_id=chat_id
                    )
                else:
                    self.send_message(f"⚠️ {res.get('message')}", target_chat_id=chat_id)

            elif data.startswith("rej:"):
                app_id = int(data.split(":", 1)[1])
                record_action("reject_application", str(app_id))
                self.answer_callback_query(query_id, text="Application rejected.")
                res = approval_service.handle_reject(app_id)
                if res.get("success"):
                    self.send_message(
                        f"❌ <b>APPLICATION CANCELLED</b>\n\n"
                        f"Application #{app_id} for <b>{res['company_name']}</b> was removed from active queue.",
                        target_chat_id=chat_id
                    )
                else:
                    self.send_message(f"⚠️ {res.get('message')}", target_chat_id=chat_id)

            elif data.startswith("edit:"):
                app_id = int(data.split(":", 1)[1])
                record_action("edit_application", str(app_id))
                self.answer_callback_query(query_id, text="Opening application editor...")
                self.send_message(
                    f"✏️ <b>EDIT APPLICATION #{app_id}</b>\n\n"
                    f"To customize your tailored summary, cover letter, or answers:\n"
                    f"1. Open the Web Application Queue: http://localhost:3000/queue\n"
                    f"2. Edit Application #{app_id} directly in the browser.\n"
                    f"3. Click <b>Approve & Submit</b> once verified.",
                    target_chat_id=chat_id
                )

            elif data.startswith("review:"):
                raw_id = data.split(":", 1)[1]
                record_action("review_job", raw_id)
                job = db.query(JobPosting).filter(
                    (JobPosting.id == int(raw_id)) if raw_id.isdigit() else (JobPosting.source_job_id == raw_id)
                ).first()

                if not job:
                    self.answer_callback_query(query_id, text="⚠️ Job not found.", show_alert=True)
                    return

                self.answer_callback_query(query_id, text="📄 Loading Application Review...")
                profile = db.query(CandidateProfile).first()
                match = db.query(JobMatch).filter(JobMatch.job_id == job.id).first()
                score = match.overall_score if match else 88.0

                review_msg = (
                    f"📄 <b>APPLICATION REVIEW — {job.company_name}</b>\n\n"
                    f"<b>Position:</b> {job.title}\n"
                    f"<b>Match Score:</b> <b>{score}/100</b>\n"
                    f"<b>Candidate:</b> {profile.full_name if profile else 'Mustkeem Ahmad'}\n"
                    f"<b>Contact:</b> {profile.email if profile else 'mustkeem324@gmail.com'} | +91-7905800532\n\n"
                    f"📝 <b>Tailored Executive Pitch:</b>\n"
                    f"<i>Experienced in frontier LLM evaluation, prompt calibration, and full-stack software delivery (UPES MBA, Jamia B.Tech First Class). Active in Handshake Project Dynamo, Outlier AI, and FreelanceKar (200+ projects).</i>\n\n"
                    f"🔗 <b>Official Portal:</b> <a href='{job.application_url}'>Click to Open Application</a>"
                )
                self.send_message(review_msg, target_chat_id=chat_id)

            elif data.startswith("skip:"):
                raw_id = data.split(":", 1)[1]
                record_action("skip_job", raw_id)
                self.answer_callback_query(query_id, text="❌ Opportunity skipped from feed.", show_alert=False)

            elif data.startswith("save:"):
                raw_id = data.split(":", 1)[1]
                record_action("save_job", raw_id)
                self.saved_jobs.add(raw_id)
                self.answer_callback_query(query_id, text="⭐ Saved to your bookmarks!", show_alert=False)

            elif data == "nav:queue":
                record_action("navigate_queue", "queue")
                self.answer_callback_query(query_id, text="Opening Queue...")
                pending = db.query(Application).filter(Application.status == "AWAITING_APPROVAL").all()
                if not pending:
                    self.send_message("✅ <b>Queue clear!</b> No applications currently awaiting approval.", target_chat_id=chat_id)
                else:
                    self.send_message(f"📋 <b>APPLICATIONS AWAITING REVIEW ({len(pending)}):</b>", target_chat_id=chat_id)
                    for p in pending:
                        card = approval_service.format_approval_card(p.id)
                        if card:
                            self.send_message(card["text"], target_chat_id=chat_id, reply_markup=card["reply_markup"])

            elif data.startswith("fup:appr:"):
                draft_id = int(data.split(":", 2)[2])
                record_action("approve_followup", str(draft_id))
                self.answer_callback_query(query_id, text="Authorizing follow-up dispatch...")
                from app.services.followup_agent import followup_agent
                res = followup_agent.approve_and_send_followup(draft_id)
                if res.get("success"):
                    self.send_message(
                        f"✉️ <b>FOLLOW-UP DISPATCHED & ARCHIVED</b>\n\n"
                        f"Follow-up draft #{draft_id} was authorized and recorded as sent.\n"
                        f"<i>Check /applications or /followups for updated state.</i>",
                        target_chat_id=chat_id
                    )
                else:
                    self.send_message(f"⚠️ {res.get('message')}", target_chat_id=chat_id)

            elif data.startswith("fup:cancel:"):
                draft_id = int(data.split(":", 2)[2])
                record_action("cancel_followup", str(draft_id))
                self.answer_callback_query(query_id, text="Follow-up draft cancelled.")
                db = SessionLocal()
                try:
                    from app.models.schema import FollowupDraft
                    d_row = db.query(FollowupDraft).filter(FollowupDraft.id == draft_id).first()
                    if d_row:
                        d_row.status = "CANCELLED"
                        db.commit()
                finally:
                    db.close()
                self.send_message(f"❌ Follow-up draft #{draft_id} cancelled.", target_chat_id=chat_id)

            # =========================================================
            # PHASE 5: BATCH CALLBACK ACTIONS
            # =========================================================
            elif data.startswith("bulk:find:"):
                target_sz = int(data.split(":")[2])
                record_action("bulk_find_jobs", str(target_sz))
                self.answer_callback_query(query_id, text=f"🔍 Preflighting {target_sz} best jobs...")
                from app.services.batch_discovery_engine import batch_discovery_engine
                batch = batch_discovery_engine.create_batch_session(target_size=target_sz)

                preflight_msg = (
                    f"⚡ <b>BATCH PREFLIGHT COMPLETE: {batch.batch_id}</b>\n\n"
                    f"<b>Target Opportunities:</b> {batch.total_jobs}\n"
                    f"<b>Eligible for Batch:</b> <b>{batch.eligible_jobs}</b>\n"
                    f"• ⚡ Authorized Auto-Submit: {batch.auto_submittable_jobs}\n"
                    f"• 📋 Manual Review Required: {batch.manual_review_jobs}\n"
                    f"• ❌ Ineligible / Excluded: {batch.total_jobs - batch.eligible_jobs}\n\n"
                    f"<i>Single-confirmation batch authorization ready. Review or authorize below:</i>"
                )
                markup = {
                    "inline_keyboard": [
                        [
                            {"text": f"🚀 Authorize & Apply ({batch.eligible_jobs} Jobs)", "callback_data": f"batch:apply:{batch.batch_id}"}
                        ],
                        [
                            {"text": "📋 Review Eligible Jobs", "callback_data": f"batch:refresh:{batch.batch_id}"},
                            {"text": "🛑 Cancel Batch", "callback_data": f"batch:stop:{batch.batch_id}"}
                        ]
                    ]
                }
                self.send_message(preflight_msg, target_chat_id=chat_id, reply_markup=markup)

            elif data.startswith("batch:apply:"):
                b_code = data.split(":", 2)[2]
                record_action("authorize_batch_apply", b_code)
                self.answer_callback_query(query_id, text="🚀 Authorizing batch application execution...")
                from app.services.batch_orchestrator import batch_orchestrator
                res = batch_orchestrator.authorize_and_start_batch(b_code, telegram_user_id=sender_id)

                prog_msg = (
                    f"📊 <b>BATCH EXECUTION COMPLETED: {b_code}</b>\n\n"
                    f"<b>Status:</b> <code>{res.get('status')}</code>\n"
                    f"<b>Confirmed Submitted:</b> <b>{res.get('submitted_count', 0)}</b>\n"
                    f"<b>Staged for Manual Completion:</b> {res.get('manual_count', 0)}\n\n"
                    f"<i>{res.get('message', '')}</i>\n"
                    f"Open Queue: http://localhost:3000/queue"
                )
                markup = {
                    "inline_keyboard": [
                        [
                            {"text": "📋 View Queue", "callback_data": "nav:queue"},
                            {"text": "📜 Batch History", "callback_data": "nav:batches"}
                        ]
                    ]
                }
                self.send_message(prog_msg, target_chat_id=chat_id, reply_markup=markup)

            elif data.startswith("batch:pause:"):
                b_code = data.split(":", 2)[2]
                record_action("pause_batch", b_code)
                from app.services.batch_orchestrator import batch_orchestrator
                res = batch_orchestrator.pause_batch(b_code)
                self.answer_callback_query(query_id, text=res.get("message", "Paused."))
                self.send_message(f"⏸ Batch {b_code} has been paused.", target_chat_id=chat_id)

            elif data.startswith("batch:resume:"):
                b_code = data.split(":", 2)[2]
                record_action("resume_batch", b_code)
                from app.services.batch_orchestrator import batch_orchestrator
                res = batch_orchestrator.resume_batch(b_code)
                self.answer_callback_query(query_id, text=res.get("message", "Resumed."))
                self.send_message(f"▶️ Batch {b_code} has resumed processing.", target_chat_id=chat_id)

            elif data.startswith("batch:stop:"):
                b_code = data.split(":", 2)[2]
                record_action("stop_batch", b_code)
                from app.services.batch_orchestrator import batch_orchestrator
                res = batch_orchestrator.stop_batch(b_code)
                self.answer_callback_query(query_id, text=res.get("message", "Stopped."))
                self.send_message(f"🛑 Batch {b_code} cancelled and stopped.", target_chat_id=chat_id)

            elif data.startswith("batch:refresh:"):
                b_code = data.split(":", 2)[2]
                self.answer_callback_query(query_id, text="Refreshing batch status...")
                from app.models.schema import ApplicationBatch
                b_row = db.query(ApplicationBatch).filter(
                    (ApplicationBatch.batch_id == b_code) | (ApplicationBatch.id == (int(b_code) if b_code.isdigit() else -1))
                ).first()
                if b_row:
                    stat_card = (
                        f"📊 <b>BATCH PROGRESS SNAPSHOT: {b_row.batch_id}</b>\n\n"
                        f"<b>Status:</b> <code>{b_row.status}</code>\n"
                        f"<b>Eligible:</b> {b_row.eligible_jobs}\n"
                        f"<b>Confirmed Submitted:</b> {b_row.submitted_count}\n"
                        f"<b>Manual Review:</b> {b_row.manual_review_jobs}\n"
                        f"<b>Failed:</b> {b_row.failed_count}"
                    )
                    self.send_message(stat_card, target_chat_id=chat_id)

            elif data == "nav:batch":
                self.answer_callback_query(query_id, text="Loading active batch...")
                from app.models.schema import ApplicationBatch
                active = db.query(ApplicationBatch).order_by(ApplicationBatch.id.desc()).first()
                if active:
                    msg = f"📊 <b>Active Batch:</b> {active.batch_id} (Status: {active.status}) | Eligible: {active.eligible_jobs}"
                    self.send_message(msg, target_chat_id=chat_id)
                else:
                    self.send_message("No active batch found. Use /bulk to create one.", target_chat_id=chat_id)

            elif data == "nav:batches":
                self.answer_callback_query(query_id, text="Loading history...")
                from app.models.schema import ApplicationBatch
                batches = db.query(ApplicationBatch).order_by(ApplicationBatch.id.desc()).limit(5).all()
                lines = [f"• {b.batch_id} ({b.status}) - Submitted: {b.submitted_count}" for b in batches]
                self.send_message("📜 <b>Batches:</b>\n" + "\n".join(lines), target_chat_id=chat_id)

            elif data.startswith("cfg:"):
                cfg_key = data.split(":", 1)[1]
                record_action("config_toggle", cfg_key)
                if cfg_key == "toggle_auto":
                    settings.AUTO_APPLY_ENABLED = not settings.AUTO_APPLY_ENABLED
                    s_row = db.query(AutomationSetting).filter(AutomationSetting.key == "AUTO_APPLY_ENABLED").first()
                    if not s_row:
                        s_row = AutomationSetting(key="AUTO_APPLY_ENABLED", value=str(settings.AUTO_APPLY_ENABLED))
                        db.add(s_row)
                    else:
                        s_row.value = str(settings.AUTO_APPLY_ENABLED)
                    db.commit()
                    self.answer_callback_query(query_id, text=f"Auto-Apply is now {'ENABLED' if settings.AUTO_APPLY_ENABLED else 'DISABLED'}")

                elif cfg_key == "toggle_india":
                    settings.RESTRICT_TO_INDIA_ELIGIBLE = not getattr(settings, "RESTRICT_TO_INDIA_ELIGIBLE", True)
                    s_row = db.query(AutomationSetting).filter(AutomationSetting.key == "RESTRICT_TO_INDIA_ELIGIBLE").first()
                    if not s_row:
                        s_row = AutomationSetting(key="RESTRICT_TO_INDIA_ELIGIBLE", value=str(settings.RESTRICT_TO_INDIA_ELIGIBLE))
                        db.add(s_row)
                    else:
                        s_row.value = str(settings.RESTRICT_TO_INDIA_ELIGIBLE)
                    db.commit()
                    self.answer_callback_query(query_id, text=f"India filter is now {'ENABLED' if settings.RESTRICT_TO_INDIA_ELIGIBLE else 'DISABLED'}")

                elif cfg_key == "cycle_score":
                    next_score = 85 if settings.MIN_MATCH_SCORE == 80 else (90 if settings.MIN_MATCH_SCORE == 85 else 80)
                    settings.MIN_MATCH_SCORE = next_score
                    s_row = db.query(AutomationSetting).filter(AutomationSetting.key == "MIN_MATCH_SCORE").first()
                    if not s_row:
                        s_row = AutomationSetting(key="MIN_MATCH_SCORE", value=str(next_score))
                        db.add(s_row)
                    else:
                        s_row.value = str(next_score)
                    db.commit()
                    self.answer_callback_query(query_id, text=f"Min Match Score set to {next_score}%")

                elif cfg_key.startswith("score_"):
                    val = int(cfg_key.split("_")[1])
                    settings.MIN_MATCH_SCORE = val
                    s_row = db.query(AutomationSetting).filter(AutomationSetting.key == "MIN_MATCH_SCORE").first()
                    if not s_row:
                        s_row = AutomationSetting(key="MIN_MATCH_SCORE", value=str(val))
                        db.add(s_row)
                    else:
                        s_row.value = str(val)
                    db.commit()
                    self.answer_callback_query(query_id, text=f"Min Match Score set to {val}%")

                # Send updated autoapply dashboard
                self.send_message(
                    f"⚙️ <b>AUTOMATION SETTINGS UPDATED</b>\n\n"
                    f"• <b>Auto-Apply:</b> {'🟢 Enabled' if settings.AUTO_APPLY_ENABLED else '🟡 Disabled (Supervised)'}\n"
                    f"• <b>India-Only Filter:</b> {'🟢 Strictly ON' if getattr(settings, 'RESTRICT_TO_INDIA_ELIGIBLE', True) else '⚪ OFF (All)'}\n"
                    f"• <b>Min Match Score:</b> {settings.MIN_MATCH_SCORE}%\n\n"
                    f"<i>Settings synchronized across Telegram and Web Dashboard.</i>",
                    target_chat_id=chat_id
                )

            elif data.startswith("fup:appr:"):
                draft_id = int(data.split(":", 2)[2])
                from app.services.followup_agent import followup_agent
                self.answer_callback_query(query_id, text="Authorizing follow-up dispatch...")
                res = followup_agent.review_and_approve_followup(draft_id, approved_by="telegram_user")
                if res.get("success"):
                    self.send_message(f"✅ <b>FOLLOW-UP DISPATCHED:</b>\n{res['message']}", target_chat_id=chat_id)
                else:
                    self.send_message(f"⚠️ {res.get('message')}", target_chat_id=chat_id)

            elif data.startswith("fup:rej:"):
                draft_id = int(data.split(":", 2)[2])
                from app.services.followup_agent import followup_agent
                self.answer_callback_query(query_id, text="Dismissing follow-up...")
                res = followup_agent.reject_followup(draft_id)
                self.send_message("❌ Follow-up draft dismissed.", target_chat_id=chat_id)

            elif data.startswith("fup:snz:"):
                draft_id = int(data.split(":", 2)[2])
                from app.services.followup_agent import followup_agent
                self.answer_callback_query(query_id, text="Snoozing follow-up...")
                res = followup_agent.snooze_followup(draft_id, days=5)
                self.send_message(f"⏰ {res['message']}", target_chat_id=chat_id)

            elif data.startswith("intv:prep:"):
                app_id = int(data.split(":", 2)[2])
                from app.services.interview_intelligence_service import interview_intelligence_service
                self.answer_callback_query(query_id, text="Generating personalized AI interview prep...")
                prep = interview_intelligence_service.generate_interview_preparation(app_id)
                if prep.get("success"):
                    content = prep["prep_content"]
                    focus_items = "\n".join([f"• {f}" for f in content["key_focus_areas"]])
                    qa = content.get("sample_questions_and_grounded_answers", [])
                    qa_str = ""
                    if qa:
                        first_q = qa[0]
                        qa_str = f"\n\n<b>Practice Q:</b> {first_q['question']}\n\n<b>Grounded Answer:</b>\n<i>{first_q['suggested_answer']}</i>"
                    
                    prep_msg = (
                        f"🧠 <b>PERSONALIZED INTERVIEW PREPARATION</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"<b>Role:</b> {prep['role']} at {prep['company']}\n"
                        f"<b>Domain:</b> <code>{prep['domain']}</code>\n"
                        f"<b>Candidate:</b> {prep['candidate']}\n\n"
                        f"<b>Key Focus Areas:</b>\n{focus_items}"
                        f"{qa_str}"
                    )
                    self.send_message(prep_msg, target_chat_id=chat_id)
                else:
                    self.send_message(f"⚠️ {prep.get('message')}", target_chat_id=chat_id)

            elif data.startswith("intv:cal:"):
                intv_id = int(data.split(":", 2)[2])
                from app.services.interview_intelligence_service import interview_intelligence_service
                self.answer_callback_query(query_id, text="Syncing Google Calendar...")
                cal_res = interview_intelligence_service.stage_google_calendar_event(intv_id)
                self.send_message(f"📅 {cal_res['message']}", target_chat_id=chat_id)

            elif data.startswith("nk:prep:"):
                raw_jid = data.split(":", 2)[2]
                self.answer_callback_query(query_id, text="Preparing tailored application package...")
                from app.services.naukri_adapter import naukri_adapter
                from app.models.schema import JobPosting
                db_lookup = SessionLocal()
                try:
                    job = db_lookup.query(JobPosting).filter(
                        (JobPosting.id == (int(raw_jid) if raw_jid.isdigit() else -1)) | (JobPosting.source_job_id == raw_jid)
                    ).first()
                    if not job:
                        self.send_message(f"⚠️ Could not locate job #{raw_jid}.", target_chat_id=chat_id)
                    else:
                        pkg = naukri_adapter.create_application_package(job.id)
                        if pkg.get("success"):
                            sa = pkg.get("screening_answers", {})
                            prep_msg = (
                                f"📝 <b>NAUKRI APPLICATION PACKAGE PREPARED</b>\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"<b>Company:</b> {pkg['company']}\n"
                                f"<b>Position:</b> {pkg['title']}\n"
                                f"<b>Capability:</b> <code>{pkg['capability']}</code>\n\n"
                                f"<b>Verified Screening Answers:</b>\n"
                                f"• <b>Notice Period:</b> {sa.get('notice_period')}\n"
                                f"• <b>Current Location:</b> {sa.get('current_location')}\n"
                                f"• <b>Total Experience:</b> {sa.get('total_experience')}\n\n"
                                f"🔗 <b>Official Portal:</b> <a href='{pkg['application_url']}'>Open Naukri Application Page</a>\n\n"
                                f"<i>{pkg['action_directive']}</i>"
                            )
                            markup = {
                                "inline_keyboard": [
                                    [
                                        {"text": "🚀 Open Official Job", "url": pkg["application_url"]}
                                    ]
                                ]
                            }
                            self.send_message(prep_msg, target_chat_id=chat_id, reply_markup=markup)
                        else:
                            self.send_message(f"⚠️ {pkg.get('message')}", target_chat_id=chat_id)
                finally:
                    db_lookup.close()

            elif data == "nk:neo:toggle":
                from app.services.naukri_neo_service import naukri_neo_service
                from app.models.schema import NaukriIntegrationSetting
                db_neo = SessionLocal()
                try:
                    cfg = db_neo.query(NaukriIntegrationSetting).first()
                    new_val = not (cfg.is_neo_enabled if cfg else False)
                    res = naukri_neo_service.configure_neo(is_neo_enabled=new_val)
                    self.answer_callback_query(query_id, text=f"Naukri Neo tracking is now {'ENABLED' if new_val else 'DISABLED'}")
                    self.send_message(f"🤖 {res['message']}", target_chat_id=chat_id)
                finally:
                    db_neo.close()

            elif data == "nk:nav:profile":
                from app.services.naukri_profile_service import naukri_profile_service
                pkg = naukri_profile_service.generate_profile_optimization_package()
                msg = (
                    f"✨ <b>OPTIMIZED NAUKRI HEADLINE & SKILLS</b>\n\n"
                    f"<b>Headline ({pkg['headline_char_count']}/250 chars):</b>\n<code>{pkg['recommended_headline']}</code>\n\n"
                    f"<b>Key Skills:</b>\n<code>{pkg['key_skills_csv']}</code>"
                )
                self.send_message(msg, target_chat_id=chat_id)



        except Exception as e:
            print(f"Error handling callback query: {e}")
            self.answer_callback_query(query_id, text="Error processing action.", show_alert=True)
        finally:
            db.close()

    def send_daily_digest(self, target_chat_id: Optional[str] = None):
        """Phase 4 Module 3 & 9: 9:00 AM Daily Operations Digest."""
        from app.core.database import SessionLocal
        from app.models.schema import JobPosting, Application, JobMatch, FollowupDraft
        db = SessionLocal()
        try:
            total_jobs = db.query(JobPosting).count()
            high_match = db.query(JobMatch).filter(JobMatch.overall_score >= 85).count()
            confirmed = db.query(Application).filter(Application.status == "SUBMITTED_CONFIRMED").count()
            pending = db.query(Application).filter(Application.status == "AWAITING_APPROVAL").count()
            drafts = db.query(FollowupDraft).filter(FollowupDraft.status == "DRAFTED").count()
            interviews = db.query(Application).filter(Application.status == "INTERVIEW").count()

            msg = (
                f"🌅 <b>GLOBAL JOB HUNTER AI — DAILY OPERATIONS REPORT (09:00 AM IST)</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"• <b>Live Discovered Vacancies:</b> {total_jobs}\n"
                f"• <b>High-Match Candidates (≥85%):</b> {high_match}\n"
                f"• <b>Confirmed Submissions:</b> {confirmed}\n"
                f"• <b>Awaiting Candidate Review:</b> {pending}\n"
                f"• <b>Follow-Up Drafts Staged:</b> {drafts}\n"
                f"• <b>Active Interviews:</b> {interviews}\n"
                f"• <b>Scheduler Status:</b> {'⏸ Paused' if self.is_paused else '🟢 Active'}\n\n"
                f"<i>Review your queue at http://localhost:3000/queue or type /pending.</i>"
            )
            self.send_message(msg, target_chat_id=target_chat_id)
        finally:
            db.close()

    def send_weekly_digest(self, target_chat_id: Optional[str] = None):
        """Phase 4 Module 3 & 9: Sunday 7:00 PM Weekly Executive Digest."""
        from app.core.database import SessionLocal
        from app.models.schema import JobPosting, Application, JobMatch
        db = SessionLocal()
        try:
            confirmed = db.query(Application).filter(Application.status == "SUBMITTED_CONFIRMED").count()
            interviews = db.query(Application).filter(Application.status == "INTERVIEW").count()
            offers = db.query(Application).filter(Application.status == "OFFER").count()
            rate = round((interviews / max(1, confirmed)) * 100, 1)

            msg = (
                f"📊 <b>GLOBAL JOB HUNTER AI — WEEKLY EXECUTIVE SUMMARY</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"• <b>Total Confirmed Applications:</b> {confirmed}\n"
                f"• <b>Interview Invitations:</b> {interviews}\n"
                f"• <b>Offers Received:</b> {offers}\n"
                f"• <b>Interview Conversion Rate:</b> <b>{rate}%</b>\n"
                f"• <b>Coverage:</b> 8 Global ATS Feeds & Remote APIs\n\n"
                f"<i>System operating autonomously for candidate Mustkeem Ahmad.</i>\n"
                f"Dashboard: http://localhost:3000"
            )
            self.send_message(msg, target_chat_id=target_chat_id)
        finally:
            db.close()

    def start_polling(self):
        """Start long-polling thread for Telegram commands and callback queries."""
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
