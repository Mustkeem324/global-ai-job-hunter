import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api.routes_jobs import router as jobs_router
from app.api.routes_resumes import router as resumes_router
from app.api.routes_applications import router as apps_router
from app.api.routes_settings import router as settings_router
from app.api.routes_telegram import router as telegram_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_audit import router as audit_router
from app.services.scheduler_service import scheduler_service
from app.services.telegram_service import telegram_service
from app.services.resume_parser import resume_parser_service
from app.services.discovery_service import discovery_service
from app.services.matching_engine import matching_engine
from app.models.schema import User, CandidateProfile, JobPosting, JobMatch, Skill, ProfessionalExperience, AutomationPolicy

def bootstrap_initial_state():
    """Seed initial candidate profile and jobs if database is fresh."""
    db = SessionLocal()
    try:
        # 1. Initialize User & Profile
        user = db.query(User).first()
        if not user:
            user = User(
                email="mustkeem324@gmail.com",
                name="Mustkeem Ahmad",
                role="candidate"
            )
            db.add(user)
            db.flush()

        profile = db.query(CandidateProfile).first()
        if not profile:
            # Check if resume.pdf exists in /home/nx-pro
            sample_resume = "/home/nx-pro/resume.pdf"
            if os.path.exists(sample_resume):
                raw_text = resume_parser_service.extract_text_from_file(sample_resume)
                parsed = resume_parser_service.parse_profile(raw_text, sample_resume)
            else:
                parsed = resume_parser_service.parse_profile("", "")

            profile = CandidateProfile(
                user_id=user.id,
                full_name=parsed["full_name"],
                email=parsed["email"],
                phone=parsed["phone"],
                location=parsed["location"],
                country=parsed["country"],
                headline=parsed["headline"],
                summary=parsed["summary"],
                github_url=parsed["github_url"],
                portfolio_url=parsed["portfolio_url"],
                education_data=parsed["education"]
            )
            db.add(profile)
            db.flush()

            for sk in parsed["skills"]:
                db.add(Skill(
                    profile_id=profile.id,
                    name=sk["name"],
                    category=sk["category"],
                    proficiency_level=sk["proficiency"],
                    evidence_text=sk["evidence"]
                ))
            for exp in parsed["experiences"]:
                db.add(ProfessionalExperience(
                    profile_id=profile.id,
                    company=exp["company"],
                    role_title=exp["role_title"],
                    start_date=exp["start_date"],
                    end_date=exp["end_date"],
                    is_current=exp["is_current"],
                    is_remote=exp["is_remote"],
                    description=exp["description"],
                    skills_used=exp.get("skills_used", [])
                ))

        # 2. Initialize Automation Policy
        policy = db.query(AutomationPolicy).first()
        if not policy:
            db.add(AutomationPolicy(
                user_id=user.id,
                auto_apply_enabled=False,
                approval_required=True,
                min_match_score=80,
                max_daily_applications=10,
                allowed_sources=["mock_ats", "greenhouse_sandbox"]
            ))

        # 3. Seed initial catalog jobs
        if db.query(JobPosting).count() == 0:
            catalog_jobs = discovery_service.run_discovery()
            cand_dict = {
                "skills": [s.name for s in profile.skills] if profile else ["Python", "RLHF", "React"],
                "total_experience_months": 25
            }
            for item in catalog_jobs:
                jp = JobPosting(
                    source_job_id=item.get("source_job_id"),
                    company_name=item["company_name"],
                    title=item["title"],
                    category=item.get("category", "Software Engineering"),
                    employment_type=item.get("employment_type", "Contract"),
                    work_arrangement=item.get("work_arrangement", "Remote"),
                    country_eligibility=item.get("country_eligibility", "Worldwide"),
                    is_india_eligible=item.get("is_india_eligible", True),
                    compensation_text=item.get("compensation_text", "Not disclosed"),
                    currency=item.get("currency", "USD"),
                    required_experience=item.get("required_experience", "2+ years"),
                    application_url=item.get("application_url", "#"),
                    description=item.get("description", ""),
                    status="Active"
                )
                db.add(jp)
                db.flush()

                match_res = matching_engine.calculate_match(item, cand_dict)
                db.add(JobMatch(
                    job_id=jp.id,
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
        print(f"Error bootstrapping initial state: {e}")
    finally:
        db.close()

# Ensure tables exist on load
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    bootstrap_initial_state()
    scheduler_service.start()
    telegram_service.start_polling()
    yield
    # Shutdown
    scheduler_service.stop()
    telegram_service.stop_polling()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous Global AI Job Discovery, Matching & Application Engine",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(jobs_router, prefix=settings.API_V1_STR)
app.include_router(resumes_router, prefix=settings.API_V1_STR)
app.include_router(apps_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)
app.include_router(telegram_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "scheduler_running": scheduler_service.is_running
    }

@app.get("/")
def root():
    return {
        "message": "Global Job Hunter AI Platform Backend API is running.",
        "documentation": "/docs",
        "health": "/health"
    }
