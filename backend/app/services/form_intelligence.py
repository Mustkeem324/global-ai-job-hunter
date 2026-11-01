import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class NormalizedField:
    field_id: str
    field_label: str
    field_type: str # text, email, phone, country, dropdown, radio, checkbox, textarea, file_upload, url
    required: bool
    options: List[str] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    mapped_profile_field: Optional[str] = None
    proposed_value: Optional[str] = None
    value_source: str = "deterministic_rule" # deterministic_rule, candidate_fact, llm_inferred, manual_review_required
    confidence: float = 1.0
    requires_manual_review: bool = False

class ApplicationFormIntelligenceService:
    """
    Phase 3 Module 4: Application Form Intelligence & Deterministic Field Mapping Engine
    Analyzes job application forms, maps candidate data safely, and flags sensitive declarations.
    """

    DETERMINISTIC_RULES = [
        # (pattern, field_type, profile_key, fallback_value, requires_review)
        (r"(first\s*name|given\s*name)", "text", "first_name", "Mustkeem", False),
        (r"(last\s*name|family\s*name|surname)", "text", "last_name", "Ahmad", False),
        (r"(full\s*name|candidate\s*name|your\s*name)", "text", "full_name", "Mustkeem Ahmad", False),
        (r"(email|e-mail)", "email", "email", "mustkeem324@gmail.com", False),
        (r"(phone|mobile|telephone|contact\s*number)", "phone", "phone", "+91-7905800532", False),
        (r"(country|current\s*country|citizenship)", "country", "country", "India", False),
        (r"(city|current\s*city|location)", "text", "city", "Hyderabad / New Delhi, India", False),
        (r"(linkedin|linked\s*in)", "url", "linkedin_url", "https://www.linkedin.com/in/mustkeem-ahmad-324", False),
        (r"(github|git\s*hub)", "url", "github_url", "https://github.com/Mustkeem324", False),
        (r"(portfolio|personal\s*website|website|url)", "url", "portfolio_url", "https://freelancekar.com", False),
        (r"(resume|cv|curriculum\s*vitae|attach\s*resume)", "file_upload", "resume_file", "resume.pdf", False),
        (r"(cover\s*letter|attach\s*cover\s*letter)", "file_upload", "cover_letter_file", "cover_letter.pdf", False),
        (r"(sponsorship|visa|require\s*sponsorship)", "radio", "visa_sponsorship", "No", False),
        (r"(work\s*authorization|legally\s*authorized|authorized\s*to\s*work)", "radio", "work_authorization", "Yes", False),
        (r"(notice\s*period|availability|when\s*can\s*you\s*start)", "dropdown", "notice_period", "Immediately available", False),
        (r"(salary\s*expectation|desired\s*salary|compensation|rate)", "text", "salary_expectation", "Aligned with stated range", False),
        (r"(gender|race|veteran|disability|demographic)", "dropdown", "demographic", "Decline to self-identify", True),
        (r"(nda|non-disclosure|arbitration|agreement|contract|terms)", "checkbox", "legal_agreement", None, True)
    ]

    def extract_form_fields(self, html_content_or_schema: Any) -> List[NormalizedField]:
        """
        Parses raw form descriptors or HTML inputs into normalized fields.
        """
        if isinstance(html_content_or_schema, list):
            fields = []
            for item in html_content_or_schema:
                fields.append(NormalizedField(
                    field_id=item.get("id", item.get("name", "field")),
                    field_label=item.get("label", item.get("name", "Field")),
                    field_type=item.get("type", "text"),
                    required=item.get("required", False),
                    options=item.get("options", []),
                    validation_rules=item.get("validation", {})
                ))
            return fields

        # Default synthetic discovery for public ATS patterns
        return [
            NormalizedField("name", "Full Name", "text", True),
            NormalizedField("email", "Email Address", "email", True),
            NormalizedField("phone", "Phone Number", "phone", True),
            NormalizedField("resume", "Resume / CV", "file_upload", True),
            NormalizedField("cover_letter", "Cover Letter", "file_upload", False),
            NormalizedField("linkedin", "LinkedIn Profile", "url", False),
            NormalizedField("github", "GitHub Profile", "url", False),
            NormalizedField("work_auth", "Are you legally authorized to work remotely from your location?", "radio", True, options=["Yes", "No"]),
            NormalizedField("sponsorship", "Will you now or in the future require visa sponsorship?", "radio", True, options=["Yes", "No"])
        ]

    def map_fields(self, form_fields: List[NormalizedField], candidate_profile: Optional[Dict[str, Any]] = None) -> List[NormalizedField]:
        """
        Maps normalized form fields to candidate facts using deterministic rules.
        Blocks auto-filling for sensitive declarations or legal agreements.
        """
        cand = candidate_profile or {}
        mapped_fields = []

        for f in form_fields:
            label_lower = f.field_label.lower()
            matched = False

            for pattern, f_type, profile_key, default_val, needs_review in self.DETERMINISTIC_RULES:
                if re.search(pattern, label_lower):
                    val = cand.get(profile_key) or default_val
                    f.field_type = f_type
                    f.mapped_profile_field = profile_key
                    f.proposed_value = val
                    f.value_source = "deterministic_rule"
                    f.confidence = 0.95
                    f.requires_manual_review = needs_review
                    matched = True
                    break

            if not matched:
                # Unmapped custom screening question -> requires human review
                f.mapped_profile_field = "custom_screening"
                f.proposed_value = None
                f.value_source = "manual_review_required"
                f.confidence = 0.40
                f.requires_manual_review = True

            mapped_fields.append(f)

        return mapped_fields

    def validate_mapped_answers(self, mapped_fields: List[NormalizedField]) -> Dict[str, Any]:
        """
        Verifies whether all required fields are safely satisfied.
        Returns validation summary and list of blocking review items.
        """
        missing_required = []
        review_required = []

        for f in mapped_fields:
            if f.requires_manual_review:
                review_required.append(f"{f.field_label} (requires explicit authorization)")
            elif f.required and not f.proposed_value:
                missing_required.append(f"{f.field_label} (required but unmapped)")

        is_submittable = len(missing_required) == 0 and len(review_required) == 0

        return {
            "is_submittable": is_submittable,
            "total_fields": len(mapped_fields),
            "missing_required": missing_required,
            "review_required": review_required,
            "can_auto_submit": is_submittable
        }

form_intelligence_service = ApplicationFormIntelligenceService()
