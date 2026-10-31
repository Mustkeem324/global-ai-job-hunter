import re
from typing import Dict, Any, Tuple

class WorldwideEligibilityEngine:
    """
    Phase 4: Worldwide Remote Eligibility Analyzer
    Default candidate location: India.
    Distinguishes published job location from applicant legal eligibility.
    Never invents worldwide eligibility.
    """

    US_RESTRICTED_KEYWORDS = [
        "us only", "u.s. only", "united states only", "must reside in the united states",
        "must be located in the us", "us citizens only", "w2 only", "us timezone only",
        "50 states", "authorized to work in the us without sponsorship", "us work authorization required"
    ]

    EMEA_RESTRICTED_KEYWORDS = [
        "emea only", "europe only", "uk only", "eu only", "germany only",
        "must reside in europe", "european timezones"
    ]

    INDIA_ACCEPTING_KEYWORDS = [
        "india", "remote - india", "apac", "asia", "ist", "worldwide", "anywhere",
        "global remote", "work from anywhere", "remote worldwide", "any location",
        "international contractor", "b2b contract"
    ]

    def evaluate_eligibility(self, location_text: str, description_text: str) -> Dict[str, Any]:
        """
        Determines:
        - classification: Worldwide Remote, Remote — India, Remote — APAC, Remote — EMEA, Remote — US Only, or Eligibility Unknown
        - is_india_eligible: bool
        - confidence: float (0.0 to 1.0)
        - evidence_quote: str
        - review_required: bool
        """
        loc_lower = (location_text or "").lower()
        desc_lower = (description_text or "")[:4000].lower()
        combined = f"{loc_lower} {desc_lower}"

        # 1. Check for strict US-only restriction
        for kw in self.US_RESTRICTED_KEYWORDS:
            if kw in loc_lower or (kw in desc_lower and "not " + kw not in desc_lower):
                return {
                    "classification": "Remote — US Only",
                    "is_india_eligible": False,
                    "confidence": 0.95,
                    "evidence_quote": f"Restriction detected: '{kw}' in posting details.",
                    "review_required": False
                }

        # 2. Check for strict EMEA-only restriction
        for kw in self.EMEA_RESTRICTED_KEYWORDS:
            if kw in loc_lower or (kw in desc_lower and "not " + kw not in desc_lower):
                return {
                    "classification": "Remote — EMEA",
                    "is_india_eligible": False,
                    "confidence": 0.90,
                    "evidence_quote": f"Regional restriction: '{kw}' in posting details.",
                    "review_required": False
                }

        # 3. Check for explicit India availability
        if "india" in loc_lower:
            return {
                "classification": "Remote — India",
                "is_india_eligible": True,
                "confidence": 1.0,
                "evidence_quote": f"Location explicitly specifies: '{location_text}'.",
                "review_required": False
            }

        # 4. Check for explicit Worldwide / Anywhere Remote
        if any(w in loc_lower for w in ("worldwide", "anywhere", "global", "remote - anywhere")):
            return {
                "classification": "Worldwide Remote",
                "is_india_eligible": True,
                "confidence": 0.95,
                "evidence_quote": f"Posting open worldwide: '{location_text}'.",
                "review_required": False
            }

        # 5. Check description for international contractor or worldwide phrasing
        if any(w in desc_lower for w in ("work from anywhere", "remote worldwide", "international contractors welcome")):
            return {
                "classification": "Worldwide Remote",
                "is_india_eligible": True,
                "confidence": 0.85,
                "evidence_quote": "Job description confirms work from anywhere / international contractor status.",
                "review_required": False
            }

        if any(w in desc_lower for w in ("apac", "asia")):
            return {
                "classification": "Remote — APAC",
                "is_india_eligible": True,
                "confidence": 0.80,
                "evidence_quote": "APAC / Asian timezone acceptance detected in description.",
                "review_required": False
            }

        # 6. Default: Eligibility Unknown -> Flag for candidate review
        return {
            "classification": "Eligibility Unknown",
            "is_india_eligible": True,  # Permitted for review queue, but marked review_required
            "confidence": 0.50,
            "evidence_quote": f"Location stated as '{location_text}'. No explicit country exclusions or worldwide declarations found.",
            "review_required": True
        }

eligibility_engine = WorldwideEligibilityEngine()
