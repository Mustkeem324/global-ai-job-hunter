import datetime
from typing import Dict, Any, List, Optional

from app.core.database import SessionLocal
from app.models.schema import CandidateProfile, NaukriProfileRecommendation

class NaukriProfileOptimizationService:
    """
    Phase 7 Module 5: Naukri Profile & Resume Optimization Assistant
    Synthesizes tailored, high-ranking profile improvements grounded strictly in Mustkeem Ahmad's credentials.
    Enforces Naukri's exact field constraints (e.g. 250-char headline limit, comma-separated key skills).
    """

    def generate_profile_optimization_package(self, user_id: int = 1) -> Dict[str, Any]:
        """
        Synthesizes an editable, high-impact profile update package tailored for Naukri's search algorithm.
        """
        db = SessionLocal()
        try:
            prof = db.query(CandidateProfile).first()
            candidate_name = prof.full_name if prof else "Mustkeem Ahmad"

            # 1. Headline (strictly ≤ 250 characters)
            headline = (
                "AI Engineer & Full-Stack Developer | Python, FastAPI, Next.js | "
                "RLHF & LLM Model Evaluation (GSM8K, HumanEval) | Ex-Outlier AI, Handshake Dynamo | "
                "MBA (UPES), B.Tech (Jamia Millia Islamia)"
            )[:250]

            # 2. Key Skills (Naukri comma-separated tags)
            key_skills = [
                "Python", "FastAPI", "Next.js", "React", "PostgreSQL", "RLHF Evaluation",
                "LLM Benchmarking", "GSM8K", "HumanEval", "Prompt Engineering", "RAG",
                "REST APIs", "Docker", "Git", "System Design", "JavaScript", "TypeScript",
                "Data Annotation", "Model Alignment", "Code Review"
            ]
            key_skills_csv = ", ".join(key_skills)

            # 3. Profile Summary
            profile_summary = (
                f"Results-oriented AI Engineer and Full-Stack Developer with over 2 years of professional "
                f"experience designing robust distributed backend APIs and conducting rigorous LLM evaluation.\n\n"
                f"Proven track record reviewing multi-turn AI reasoning traces, benchmark design (GSM8K, HumanEval), "
                f"and reward model alignment at Outlier AI and FreelanceKar. Experienced in building full-stack applications "
                f"with Python, FastAPI, Next.js, and PostgreSQL at Handshake Dynamo.\n\n"
                f"Holds a Master of Business Administration (MBA) in Power Management from UPES Dehradun and a Bachelor of "
                f"Technology (B.Tech) in Electrical Engineering from Jamia Millia Islamia, New Delhi."
            )

            # 4. Project Highlights
            project_highlights = [
                {
                    "title": "Global AI Job Hunter & Application Engine",
                    "technologies": "Python, FastAPI, Next.js, SQLite/PostgreSQL, Telegram Bot API, LLMs",
                    "description": "Engineered autonomous global job search, resume matching, and multi-job batch application engine with strict preflight verification and receipt confirmation."
                },
                {
                    "title": "LLM Reasoning & Coding Benchmark Evaluation Framework",
                    "technologies": "Python, Benchmark Datasets (GSM8K, HumanEval), Pairwise Ranking",
                    "description": "Evaluated complex programming outputs, identified algorithmic edge-case failures, and calibrated prompt evaluation rubrics for frontier AI training."
                }
            ]

            # 5. Preferences & Notice Period
            notice_period = "Immediate / 15 Days"
            preferred_roles = [
                "AI Trainer", "LLM Evaluator", "AI Coding Evaluator", "Full-Stack Developer", 
                "Python Backend Developer", "Generative AI Engineer"
            ]
            preferred_locations = ["Delhi NCR", "Noida", "Gurugram", "Remote India", "Worldwide Remote"]
            expected_ctc = "Market Competitive / Negotiable based on role scope"

            # Persist in DB
            rec = db.query(NaukriProfileRecommendation).filter(
                NaukriProfileRecommendation.user_id == user_id,
                NaukriProfileRecommendation.status == "ACTIVE"
            ).first()

            if not rec:
                rec = NaukriProfileRecommendation(
                    user_id=user_id,
                    recommended_headline=headline,
                    profile_summary=profile_summary,
                    key_skills_csv=key_skills_csv,
                    project_highlights=project_highlights,
                    notice_period_text=notice_period,
                    target_ctc_text=expected_ctc,
                    status="ACTIVE"
                )
                db.add(rec)
            else:
                rec.recommended_headline = headline
                rec.profile_summary = profile_summary
                rec.key_skills_csv = key_skills_csv
                rec.project_highlights = project_highlights
                rec.generated_at = datetime.datetime.now(datetime.timezone.utc)

            db.commit()

            return {
                "success": True,
                "candidate": candidate_name,
                "recommended_headline": headline,
                "headline_char_count": len(headline),
                "key_skills_csv": key_skills_csv,
                "profile_summary": profile_summary,
                "project_highlights": project_highlights,
                "notice_period": notice_period,
                "preferred_locations": preferred_locations,
                "preferred_roles": preferred_roles,
                "expected_ctc": expected_ctc,
                "instructions": "Copy and paste these optimized text blocks directly into your Naukri profile editor to maximize recruiter search impressions."
            }
        finally:
            db.close()

naukri_profile_service = NaukriProfileOptimizationService()
