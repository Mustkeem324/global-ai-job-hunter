import datetime
from typing import List, Dict, Any
from app.core.database import SessionLocal
from app.models.schema import CompanyRegistry

DEFAULT_VERIFIED_EMPLOYERS = [
    # Greenhouse ATS Verified Boards
    {
        "company_name": "Canonical",
        "official_website": "https://canonical.com",
        "career_page": "https://canonical.com/careers",
        "ats_provider": "Greenhouse",
        "ats_board_identifier": "canonical",
        "supported_locations": ["Worldwide", "India", "Remote - EMEA", "Remote - Americas"]
    },
    {
        "company_name": "Automattic",
        "official_website": "https://automattic.com",
        "career_page": "https://automattic.com/work-with-us/",
        "ats_provider": "Greenhouse",
        "ats_board_identifier": "automattic",
        "supported_locations": ["Worldwide Remote"]
    },
    {
        "company_name": "GitLab",
        "official_website": "https://about.gitlab.com",
        "career_page": "https://about.gitlab.com/jobs/",
        "ats_provider": "Greenhouse",
        "ats_board_identifier": "gitlab",
        "supported_locations": ["Worldwide Remote", "APAC"]
    },
    {
        "company_name": "Scale AI",
        "official_website": "https://scale.com",
        "career_page": "https://scale.com/careers",
        "ats_provider": "Greenhouse",
        "ats_board_identifier": "scaleai",
        "supported_locations": ["Remote", "India", "US"]
    },
    {
        "company_name": "Figma",
        "official_website": "https://figma.com",
        "career_page": "https://figma.com/careers",
        "ats_provider": "Greenhouse",
        "ats_board_identifier": "figma",
        "supported_locations": ["Remote", "US", "APAC"]
    },
    # Lever ATS Verified Boards
    {
        "company_name": "Spotify",
        "official_website": "https://spotify.com",
        "career_page": "https://www.lifeatspotify.com/jobs",
        "ats_provider": "Lever",
        "ats_board_identifier": "spotify",
        "supported_locations": ["Worldwide", "Remote - EMEA", "Remote - Americas"]
    },
    {
        "company_name": "Netflix",
        "official_website": "https://netflix.com",
        "career_page": "https://jobs.netflix.com",
        "ats_provider": "Lever",
        "ats_board_identifier": "netflix",
        "supported_locations": ["Worldwide Remote", "US"]
    },
    # Ashby ATS Verified Boards
    {
        "company_name": "Linear",
        "official_website": "https://linear.app",
        "career_page": "https://linear.app/careers",
        "ats_provider": "Ashby",
        "ats_board_identifier": "linear",
        "supported_locations": ["Worldwide Remote", "Americas", "Europe"]
    },
    {
        "company_name": "Ramp",
        "official_website": "https://ramp.com",
        "career_page": "https://ramp.com/careers",
        "ats_provider": "Ashby",
        "ats_board_identifier": "ramp",
        "supported_locations": ["Remote", "US"]
    },
    {
        "company_name": "Replit",
        "official_website": "https://replit.com",
        "career_page": "https://replit.com/careers",
        "ats_provider": "Ashby",
        "ats_board_identifier": "replit",
        "supported_locations": ["Worldwide Remote"]
    }
]

class CompanyRegistryService:
    def seed_default_employers(self):
        """Seed verified employer board identifiers into the database."""
        db = SessionLocal()
        try:
            for emp in DEFAULT_VERIFIED_EMPLOYERS:
                existing = db.query(CompanyRegistry).filter(
                    CompanyRegistry.ats_board_identifier == emp["ats_board_identifier"],
                    CompanyRegistry.ats_provider == emp["ats_provider"]
                ).first()
                if not existing:
                    db.add(CompanyRegistry(
                        company_name=emp["company_name"],
                        official_website=emp["official_website"],
                        career_page=emp["career_page"],
                        ats_provider=emp["ats_provider"],
                        ats_board_identifier=emp["ats_board_identifier"],
                        supported_locations=emp["supported_locations"],
                        source_status="Active",
                        latest_synchronization_status="Verified"
                    ))
            db.commit()
        finally:
            db.close()

    def get_employers_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Retrieve verified employer records for a given ATS provider."""
        db = SessionLocal()
        try:
            records = db.query(CompanyRegistry).filter(
                CompanyRegistry.ats_provider.ilike(provider),
                CompanyRegistry.source_status == "Active"
            ).all()
            if not records:
                # Return in-memory fallback
                return [e for e in DEFAULT_VERIFIED_EMPLOYERS if e["ats_provider"].lower() == provider.lower()]
            return [
                {
                    "id": r.id,
                    "company_name": r.company_name,
                    "ats_provider": r.ats_provider,
                    "ats_board_identifier": r.ats_board_identifier,
                    "official_website": r.official_website,
                    "career_page": r.career_page
                } for r in records
            ]
        finally:
            db.close()

company_registry_service = CompanyRegistryService()
