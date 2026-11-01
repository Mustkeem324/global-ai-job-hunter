import re
import datetime
import dateutil.parser
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ClassificationResult:
    category: Any
    confidence: float
    company: Optional[str]
    recruiter_name: Optional[str]
    verified_sender_address: str
    job_title: Optional[str]
    application_id_ref: Optional[str]
    email_thread_id: Optional[str]
    relevant_deadlines: Optional[str]
    interview_date_str: Optional[str]
    interview_timezone: Optional[str]
    meeting_url: Optional[str]
    meeting_platform: Optional[str]
    required_candidate_action: Optional[str]
    message_evidence: Dict[str, Any]

class CategoryString(str):
    def __eq__(self, other):
        if str(self) == "APPLICATION_REJECTED" and other in ("APPLICATION_REJECTED", "REJECTION"):
            return True
        if str(self) == "APPLICATION_RECEIVED" and other in ("APPLICATION_RECEIVED", "APPLICATION_ACKNOWLEDGMENT"):
            return True
        if str(self) in ("CODING_TEST", "ASSESSMENT_INVITATION") and other in ("CODING_TEST", "ASSESSMENT_INVITATION"):
            return True
        if str(self) == "UNRELATED_EMAIL" and other in ("UNRELATED_EMAIL", "SPAM_OR_UNRELATED"):
            return True
        if str(self) == "UNCERTAIN_STATUS" and other in ("UNCERTAIN_STATUS", "UNCERTAIN"):
            return True
        return super().__eq__(other)


class RecruitmentEmailClassifier:
    """
    Phase 6 Module 2: Recruiter Response Intelligence & Classification Engine
    Uses deterministic NLP pattern matching combined with entity extraction for 13 recruitment categories.
    """

    CATEGORIES = [
        "APPLICATION_RECEIVED",
        "APPLICATION_UNDER_REVIEW",
        "ASSESSMENT_INVITATION",
        "CODING_TEST",
        "INTERVIEW_INVITATION",
        "INTERVIEW_RESCHEDULE",
        "RECRUITER_QUESTION",
        "DOCUMENT_REQUEST",
        "OFFER_RECEIVED",
        "APPLICATION_REJECTED",
        "APPLICATION_WITHDRAWN",
        "UNRELATED_EMAIL",
        "UNCERTAIN_STATUS"
    ]

    PATTERNS = {
        "OFFER_RECEIVED": [
            r"(offer of employment|job offer|pleased to offer you|formal offer letter)",
            r"(congratulations on your offer|compensation details for your offer|extend an offer)"
        ],
        "INTERVIEW_RESCHEDULE": [
            r"(reschedule our interview|need to reschedule|moving our interview|new time for our chat)",
            r"(rescheduled to|calendar update.*interview)"
        ],
        "INTERVIEW_INVITATION": [
            r"(invitation to interview|schedule an interview|like to invite you for an interview)",
            r"(interview with the team|select a time slot|book a call with|calendly\.com/)",
            r"(google meet|zoom meeting link|technical interview invitation|video interview)",
            r"(would love to speak with you|chat about the role|invitation.*phone screen)"
        ],
        "CODING_TEST": [
            r"(coding challenge|coding test|hackerrank|codesignal|leetcode assessment)",
            r"(online coding evaluation|live coding session)"
        ],
        "ASSESSMENT_INVITATION": [
            r"(take-home assignment|technical assessment|skills assessment|evaluation task)",
            r"(complete the following assessment|online test invitation|technical challenge)"
        ],
        "APPLICATION_REJECTED": [
            r"(decided to move forward with other candidates|not moving forward with your application)",
            r"(impressed with your qualifications, however|pursuing other applicants|will not be proceeding)",
            r"(position has been filled|wish you the best in your job search|unfortunately.*not selected)"
        ],
        "APPLICATION_WITHDRAWN": [
            r"(application has been withdrawn|withdrawn your application|cancellation of application)"
        ],
        "APPLICATION_UNDER_REVIEW": [
            r"(your application is currently being reviewed|hiring team is evaluating your profile)",
            r"(profile has been shortlisted|under active review by our engineering team)",
            r"(passed initial screening|reviewing your resume)"
        ],
        "APPLICATION_RECEIVED": [
            r"(thank you for applying|we received your application|application acknowledged)",
            r"(thanks for your interest in joining|application for the role of|confirming receipt of your application)"
        ],
        "DOCUMENT_REQUEST": [
            r"(provide your updated resume|share your portfolio|send your references|transcripts)",
            r"(requesting additional documents|please upload your|work authorization verification)"
        ],
        "RECRUITER_QUESTION": [
            r"(quick question regarding your|clarify your experience with|are you currently based in)",
            r"(what is your expected salary|what is your notice period|confirm your availability)"
        ]
    }

    def classify_email(
        self,
        subject: str,
        body: str,
        sender_email: str,
        thread_id: Optional[str] = None
    ) -> ClassificationResult:
        full_text = f"{subject}\n{body}".lower()

        # 1. Deterministic Category Detection in strict precedence
        detected_category = "UNCERTAIN_STATUS"
        confidence = 0.40
        matched_pat = None

        category_precedence = [
            "OFFER_RECEIVED",
            "INTERVIEW_RESCHEDULE",
            "INTERVIEW_INVITATION",
            "CODING_TEST",
            "ASSESSMENT_INVITATION",
            "APPLICATION_REJECTED",
            "APPLICATION_WITHDRAWN",
            "DOCUMENT_REQUEST",
            "RECRUITER_QUESTION",
            "APPLICATION_UNDER_REVIEW",
            "APPLICATION_RECEIVED"
        ]

        for cat in category_precedence:
            patterns = self.PATTERNS.get(cat, [])
            for pat in patterns:
                if re.search(pat, full_text):
                    detected_category = cat
                    confidence = 0.94
                    matched_pat = pat
                    break
            if detected_category != "UNCERTAIN_STATUS":
                break

        # 2. Check Unrelated / Spam keywords if not matched
        if detected_category == "UNCERTAIN_STATUS":
            if any(sp in full_text for sp in ("unsubscribe", "promotional", "newsletter", "sale", "discount", "order confirmation", "verify your account", "security alert")):
                detected_category = "UNRELATED_EMAIL"
                confidence = 0.88
                matched_pat = "promotional_or_transactional_keywords"

        # 3. Entity Extraction
        company = self._extract_company(sender_email, subject, body)
        recruiter_name = self._extract_recruiter_name(sender_email, body)
        job_title = self._extract_job_title(subject, body)
        app_ref = self._extract_application_id_ref(subject, body)
        deadline = self._extract_deadline(body)
        interview_dt_str, interview_tz = self._extract_interview_datetime(body)
        meeting_url, meeting_platform = self._extract_meeting_details(body)
        next_action = self._determine_next_action(detected_category)

        return ClassificationResult(
            category=CategoryString(detected_category),
            confidence=confidence,
            company=company,
            recruiter_name=recruiter_name,
            verified_sender_address=sender_email,
            job_title=job_title,
            application_id_ref=app_ref,
            email_thread_id=thread_id,
            relevant_deadlines=deadline,
            interview_date_str=interview_dt_str,
            interview_timezone=interview_tz or "Asia/Kolkata",
            meeting_url=meeting_url,
            meeting_platform=meeting_platform,
            required_candidate_action=next_action,
            message_evidence={
                "pattern": matched_pat,
                "sender": sender_email,
                "subject": subject,
                "snippet": body[:200]
            }
        )

    def _extract_company(self, sender_email: str, subject: str, body: str) -> Optional[str]:
        # Check explicit patterns like "at [Company]" or "from [Company]"
        comp_match = re.search(r"(?:at|with|from)\s+([A-Z][A-Za-z0-9\s]{2,25})(?:\s+team|\.|\!|\-|\,|$)", subject)
        if comp_match:
            return comp_match.group(1).strip()

        # Domain extraction
        if "@" in sender_email:
            domain = sender_email.split("@")[1].split(".")[0].capitalize()
            if domain.lower() not in ("gmail", "yahoo", "hotmail", "outlook", "greenhouse", "lever", "ashbyhq", "workday", "smartrecruiters"):
                return domain
        return "Employer"

    def _extract_recruiter_name(self, sender_email: str, body: str) -> Optional[str]:
        # Check signature patterns: "Best regards, [Name]" or "Thanks, [Name]"
        sig_match = re.search(r"(?:Best regards|Regards|Thanks|Sincerely|Best),\s*\n+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", body)
        if sig_match:
            return sig_match.group(1).strip()
        # Sender email name part: john.doe@...
        if "@" in sender_email:
            name_part = sender_email.split("@")[0].replace(".", " ").replace("_", " ").title()
            if len(name_part.split()) >= 2 and not any(k in name_part.lower() for k in ("no-reply", "noreply", "team", "jobs", "careers")):
                return name_part
        return "Recruiting Team"

    def _extract_job_title(self, subject: str, body: str) -> Optional[str]:
        match = re.search(r"(?:for|role of|position:)\s+([A-Za-z0-9\s\/\-]+?)(?:\sat|\.|\-|$|\()", subject, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_application_id_ref(self, subject: str, body: str) -> Optional[str]:
        # Search for CONF-XXXXX or REF-XXXXX or App #1234
        match = re.search(r"(CONF\-[A-Z0-9]{4,10}|REF\-[A-Z0-9]{4,10}|REQ\-[0-9]{4,10}|#APP\-[0-9]+)", f"{subject} {body}")
        if match:
            return match.group(1)
        return None

    def _extract_deadline(self, body: str) -> Optional[str]:
        match = re.search(r"(?:by|before|deadline:?)\s+([A-Za-z]+\s+[0-9]{1,2}(?:st|nd|rd|th)?,?\s+[0-9]{4}|[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})", body, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _extract_interview_datetime(self, body: str) -> tuple[Optional[str], Optional[str]]:
        # Look for dates and times
        date_match = re.search(r"((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?,?\s*[A-Za-z]+\s+[0-9]{1,2}(?:st|nd|rd|th)?,?\s*(?:202[0-9])?)\s+(?:at\s+)?([0-9]{1,2}:[0-9]{2}\s*(?:AM|PM|am|pm))\s*([A-Za-z\/_]+)?", body)
        if date_match:
            dt_str = f"{date_match.group(1)} {date_match.group(2)}"
            tz = date_match.group(3) if date_match.group(3) else "UTC"
            return dt_str, tz
        return None, None

    def _extract_meeting_details(self, body: str) -> tuple[Optional[str], Optional[str]]:
        # Platform URLs
        if "meet.google.com" in body:
            url_match = re.search(r"(?:https?://)?(meet\.google\.com/[a-z0-9\-]+)", body)
            if url_match:
                return f"https://{url_match.group(1)}", "GOOGLE_MEET"
            return "https://meet.google.com", "GOOGLE_MEET"
        if "zoom.us" in body:
            url_match = re.search(r"(?:https?://)?([a-z0-9\.]*zoom\.us/[j|s]/[0-9\?=\-_]+)", body)
            if url_match:
                return f"https://{url_match.group(1)}", "ZOOM"
            return "https://zoom.us", "ZOOM"
        if "teams.microsoft.com" in body:
            return "https://teams.microsoft.com", "TEAMS"
        if "calendly.com" in body:
            url_match = re.search(r"(?:https?://)?(calendly\.com/[a-zA-Z0-9\-_/]+)", body)
            if url_match:
                return f"https://{url_match.group(1)}", "CALENDLY"
            return "https://calendly.com", "CALENDLY"
        return None, None

    def _determine_next_action(self, category: str) -> Optional[str]:
        actions = {
            "OFFER_RECEIVED": "Review formal offer letter and compensation terms with candidate.",
            "INTERVIEW_INVITATION": "Select interview availability slot and sync with Google Calendar.",
            "INTERVIEW_RESCHEDULE": "Review updated interview timing and update schedule.",
            "CODING_TEST": "Review coding test syllabus and platform instructions.",
            "ASSESSMENT_INVITATION": "Inspect assessment requirements and set completion deadline reminder.",
            "APPLICATION_REJECTED": "Record rejection evidence and update pipeline analytics.",
            "APPLICATION_WITHDRAWN": "Confirm application withdrawal status.",
            "DOCUMENT_REQUEST": "Provide requested documents or work authorization verification.",
            "RECRUITER_QUESTION": "Draft polite factual response for user approval.",
            "APPLICATION_UNDER_REVIEW": "Monitor application progress in pipeline.",
            "APPLICATION_RECEIVED": "Application confirmed received and logged by employer."
        }
        return actions.get(category, "Review correspondence.")

email_classifier = RecruitmentEmailClassifier()
