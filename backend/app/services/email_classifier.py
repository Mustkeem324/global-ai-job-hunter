import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ClassificationResult:
    category: str
    confidence: float
    employer_name: Optional[str]
    job_title: Optional[str]
    event_date: Optional[str]
    next_action: Optional[str]
    matched_criteria: Dict[str, Any]

class RecruitmentEmailClassifier:
    """
    Phase 3 Module 9: Recruitment Email Classification & Entity Extraction Engine
    Categorizes recruiter correspondence into 12 structured recruitment categories.
    """

    CATEGORIES = [
        "APPLICATION_ACKNOWLEDGMENT",
        "APPLICATION_UNDER_REVIEW",
        "ASSESSMENT_INVITATION",
        "INTERVIEW_INVITATION",
        "INTERVIEW_RESCHEDULE",
        "RECRUITER_QUESTION",
        "DOCUMENT_REQUEST",
        "OFFER_RECEIVED",
        "REJECTION",
        "GENERAL_RECRUITMENT_MESSAGE",
        "SPAM_OR_UNRELATED",
        "UNCERTAIN"
    ]

    PATTERNS = {
        "OFFER_RECEIVED": [
            r"(offer of employment|job offer|pleased to offer you|formal offer letter)",
            r"(congratulations on your offer|compensation details for your offer)"
        ],
        "INTERVIEW_INVITATION": [
            r"(invitation to interview|schedule an interview|like to invite you for an interview)",
            r"(interview with the team|select a time slot|book a call with|calendly\.com/)",
            r"(google meet|zoom meeting link|technical interview invitation)"
        ],
        "INTERVIEW_RESCHEDULE": [
            r"(reschedule our interview|need to reschedule|moving our interview|new time for our chat)"
        ],
        "ASSESSMENT_INVITATION": [
            r"(coding assessment|technical assessment|take-home assignment|hackerrank|codesignal)",
            r"(complete the following assessment|online test invitation|technical challenge)"
        ],
        "REJECTION": [
            r"(decided to move forward with other candidates|not moving forward with your application)",
            r"(impressed with your qualifications, however|pursuing other applicants|will not be proceeding)",
            r"(position has been filled|wish you the best in your job search)"
        ],
        "APPLICATION_ACKNOWLEDGMENT": [
            r"(thank you for applying|we received your application|application acknowledged)",
            r"(thanks for your interest in joining|application for the role of)"
        ],
        "APPLICATION_UNDER_REVIEW": [
            r"(your application is currently being reviewed|hiring team is evaluating your profile)",
            r"(profile has been shortlisted|under active review by our engineering team)"
        ],
        "DOCUMENT_REQUEST": [
            r"(provide your updated resume|share your portfolio|send your references|transcripts)",
            r"(requesting additional documents|please upload your)"
        ],
        "RECRUITER_QUESTION": [
            r"(quick question regarding your|clarify your experience with|are you currently based in)",
            r"(what is your expected salary|what is your notice period)"
        ]
    }

    def classify_email(self, subject: str, body: str, sender_email: str) -> ClassificationResult:
        full_text = f"{subject}\n{body}".lower()

        # Check in priority order: Offer -> Interview -> Assessment -> Rejection -> Acknowledgment
        for category in ["OFFER_RECEIVED", "INTERVIEW_INVITATION", "INTERVIEW_RESCHEDULE", "ASSESSMENT_INVITATION", "REJECTION", "DOCUMENT_REQUEST", "RECRUITER_QUESTION", "APPLICATION_UNDER_REVIEW", "APPLICATION_ACKNOWLEDGMENT"]:
            patterns = self.PATTERNS.get(category, [])
            for pat in patterns:
                if re.search(pat, full_text):
                    # Extract entities
                    employer = self._extract_employer(sender_email, body)
                    job_title = self._extract_job_title(subject, body)
                    next_action = self._determine_next_action(category)

                    return ClassificationResult(
                        category=category,
                        confidence=0.92,
                        employer_name=employer,
                        job_title=job_title,
                        event_date=None,
                        next_action=next_action,
                        matched_criteria={"pattern": pat, "sender": sender_email}
                    )

        # Check if spam / unrelated
        if any(sp in full_text for sp in ("unsubscribe", "promotional", "newsletter", "sale", "discount", "order confirmation")):
            return ClassificationResult(
                category="SPAM_OR_UNRELATED",
                confidence=0.85,
                employer_name=None,
                job_title=None,
                event_date=None,
                next_action=None,
                matched_criteria={"reason": "promotional_keywords"}
            )

        return ClassificationResult(
            category="UNCERTAIN",
            confidence=0.40,
            employer_name=self._extract_employer(sender_email, body),
            job_title=self._extract_job_title(subject, body),
            event_date=None,
            next_action="Manual candidate review recommended",
            matched_criteria={"reason": "unmatched_keywords"}
        )

    def _extract_employer(self, sender_email: str, body: str) -> Optional[str]:
        # Domain parsing
        if "@" in sender_email:
            domain = sender_email.split("@")[1].split(".")[0].capitalize()
            if domain.lower() not in ("gmail", "yahoo", "hotmail", "outlook", "greenhouse", "lever", "ashbyhq"):
                return domain
        return "Hiring Organization"

    def _extract_job_title(self, subject: str, body: str) -> Optional[str]:
        # Simple extraction from subject line
        match = re.search(r"(?:for|role of|position:)\s+([A-Za-z0-9\s\-]+?)(?:\sat|\.|\-|$)", subject, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "Software Engineer"

    def _determine_next_action(self, category: str) -> Optional[str]:
        actions = {
            "OFFER_RECEIVED": "Review formal offer letter and compensation terms with candidate.",
            "INTERVIEW_INVITATION": "Select interview availability slot and sync with Google Calendar.",
            "INTERVIEW_RESCHEDULE": "Review updated interview timing.",
            "ASSESSMENT_INVITATION": "Inspect assessment requirements and set completion reminder.",
            "REJECTION": "Record rejection evidence and update pipeline analytics.",
            "DOCUMENT_REQUEST": "Provide requested documents.",
            "RECRUITER_QUESTION": "Draft polite factual response.",
            "APPLICATION_ACKNOWLEDGMENT": "Application confirmed logged."
        }
        return actions.get(category)

email_classifier = RecruitmentEmailClassifier()
