import os
import datetime
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.database import SessionLocal
from app.models.schema import JobPosting, JobMatch, CandidateProfile
from app.services.connectors.greenhouse import greenhouse_connector
from app.services.connectors.lever import lever_connector
from app.services.connectors.ashby import ashby_connector
from app.services.connectors.himalayas import himalayas_connector
from app.services.connectors.jobicy import jobicy_connector
from app.services.connectors.remotive import remotive_connector
from app.services.connectors.arbeitnow import arbeitnow_connector
from app.services.connectors.catalog import catalog_connector, mock_ats_connector
from app.services.query_planner import query_planner
from app.services.company_registry import company_registry_service
from app.services.matching_engine import matching_engine

class GlobalDiscoveryService:
    """
    Phase 2 & Phase 3: Global Vacancy Discovery & Ingestion Engine
    Coordinates all ATS, Remote Job, and Catalog connectors.
    Executes automatic query expansion, deduplication, match calculation, and database persistence.
    """
    def __init__(self):
        # Ensure company registry default employers are seeded
        try:
            company_registry_service.seed_default_employers()
        except Exception:
            pass

        self.connectors = {
            "catalog": catalog_connector,
            "greenhouse": greenhouse_connector,
            "lever": lever_connector,
            "ashby": ashby_connector,
            "himalayas": himalayas_connector,
            "jobicy": jobicy_connector,
            "remotive": remotive_connector,
            "arbeitnow": arbeitnow_connector,
            "mock_ats": mock_ats_connector
        }

    def run_discovery(self, query: str = "", seed_terms: Optional[List[str]] = None, persist: bool = True) -> List[Dict[str, Any]]:
        """
        Execute concurrent multi-source job sweep across all registered connectors.
        """
        # 1. Expand query if seeds provided
        if seed_terms:
            plan = query_planner.create_query_plan(seed_terms)
            queries = plan["expanded_queries"][:4] # Take top 4 expanded terms for sweep
        elif query:
            queries = [query]
        else:
            queries = ["AI", "Python", "Full Stack"]

        all_discovered: List[Dict[str, Any]] = []
        seen_keys: Set[str] = set()

        def fetch_from_connector(conn_key, connector, q):
            try:
                return connector.search_jobs(query=q)
            except Exception as e:
                print(f"Connector error [{conn_key}] query='{q}': {e}")
                return []

        # 2. Run searches with bounded concurrency
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_conn = {}
            for q in queries:
                for k, conn in self.connectors.items():
                    future = executor.submit(fetch_from_connector, k, conn, q)
                    future_to_conn[future] = (k, q)

            for future in as_completed(future_to_conn):
                jobs = future.result()
                for j in jobs:
                    # Deduplication key: company_name + normalized title + clean application URL
                    company_norm = (j.get("company_name") or "").lower().strip()
                    title_norm = (j.get("job_title") or "").lower().strip()
                    app_url_norm = (j.get("application_url") or "").split("?")[0].lower()
                    dedup_key = f"{company_norm}::{title_norm}::{app_url_norm}"

                    if dedup_key not in seen_keys:
                        seen_keys.add(dedup_key)
                        all_discovered.append(j)

        # 3. Persist and Score if requested
        if persist and all_discovered:
            self._persist_and_match(all_discovered)

        return all_discovered

    def _persist_and_match(self, jobs: List[Dict[str, Any]]):
        """Store discovered canonical records in SQLite and calculate 6-pillar match scores."""
        db = SessionLocal()
        try:
            profile = db.query(CandidateProfile).first()
            cand_dict = {
                "headline": profile.headline if profile else "AI Trainer & Full-Stack Developer",
                "summary": profile.summary if profile else "",
                "skills": [s.name for s in profile.skills] if (profile and profile.skills) else [
                    "Python", "Django", "FastAPI", "React", "Next.js", "RLHF", "LLM Evaluation", "PostgreSQL", "AWS"
                ]
            }

            for j in jobs:
                # Check if posting exists by application_url or source_job_id
                existing = db.query(JobPosting).filter(
                    (JobPosting.application_url == j["application_url"]) |
                    ((JobPosting.source_job_id == j["source_job_id"]) & (JobPosting.company_name == j["company_name"]))
                ).first()

                if not existing:
                    posting = JobPosting(
                        source_job_id=j["source_job_id"],
                        company_name=j["company_name"],
                        company_website=j.get("company_website"),
                        title=j["job_title"],
                        normalized_role=j.get("normalized_role", j["job_title"]),
                        category="AI & Software Engineering",
                        employment_type=j.get("employment_type", "Full-time"),
                        workplace_type=j.get("workplace_type", "Remote"),
                        country_eligibility=j.get("location", "Worldwide Remote"),
                        is_india_eligible=j.get("is_india_eligible", True),
                        compensation_text=j.get("compensation_text", "Competitive"),
                        currency=j.get("salary_currency", "USD"),
                        min_comp=j.get("salary_min"),
                        max_comp=j.get("salary_max"),
                        required_experience=j.get("experience_requirements", "2+ years"),
                        location=j.get("location", "Remote"),
                        application_url=j["application_url"],
                        description=j["description"],
                        location_evidence=j.get("location_evidence"),
                        application_capability=j.get("application_capability", "USER_REVIEW_REQUIRED"),
                        verification_state=j.get("verification_state", "VERIFIED_OPEN"),
                        status="Active",
                        posted_date=datetime.datetime.now(datetime.timezone.utc)
                    )
                    db.add(posting)
                    db.flush()

                    # Calculate 6-factor match score
                    if profile:
                        match_res = matching_engine.calculate_match(cand_dict, j)
                        db.add(JobMatch(
                            job_id=posting.id,
                            profile_id=profile.id,
                            overall_score=match_res["overall_score"],
                            skills_score=match_res["skills_score"],
                            experience_score=match_res["experience_score"],
                            eligibility_score=match_res["eligibility_score"],
                            education_score=match_res["education_score"],
                            preferences_score=match_res["preferences_score"],
                            recency_score=match_res["recency_score"],
                            match_tier=match_res["match_tier"],
                            is_india_eligible=match_res["is_india_eligible"],
                            explanation_json=match_res["explanation"]
                        ))

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error persisting discovered jobs: {e}")
        finally:
            db.close()

discovery_service = GlobalDiscoveryService()
