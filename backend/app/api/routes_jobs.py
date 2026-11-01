from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.models.schema import JobPosting, JobMatch, CandidateProfile, Application, User
from app.services.discovery_service import discovery_service
from app.services.matching_engine import matching_engine
from app.services.document_generator import document_generator
from app.services.telegram_service import telegram_service
from app.core.state_machine import ApplicationStatus, ApplicationMode
import uuid

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/")
def get_jobs(
    q: Optional[str] = None,
    category: Optional[str] = None,
    min_score: Optional[float] = None,
    india_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(JobPosting)
    if q:
        query = query.filter(JobPosting.title.ilike(f"%{q}%") | JobPosting.company_name.ilike(f"%{q}%"))
    if category and category != "All":
        query = query.filter(JobPosting.category == category)
    if india_only:
        query = query.filter(JobPosting.is_india_eligible == True)
        
    jobs = query.order_by(JobPosting.id.desc()).all()
    
    # Enrich with match scores
    results = []
    for j in jobs:
        match = db.query(JobMatch).filter(JobMatch.job_id == j.id).first()
        score = match.overall_score if match else 85.0
        if min_score and score < min_score:
            continue
        results.append({
            "id": j.id,
            "company_name": j.company_name,
            "company_website": getattr(j, "company_website", ""),
            "title": j.title,
            "category": j.category,
            "employment_type": j.employment_type,
            "work_arrangement": j.work_arrangement,
            "country_eligibility": j.country_eligibility,
            "is_india_eligible": j.is_india_eligible,
            "compensation_text": j.compensation_text,
            "currency": j.currency,
            "required_experience": j.required_experience,
            "application_url": j.application_url,
            "application_capability": getattr(j, "application_capability", "USER_REVIEW_REQUIRED"),
            "verification_state": getattr(j, "verification_state", "VERIFIED_OPEN"),
            "location_evidence": getattr(j, "location_evidence", ""),
            "description": j.description,
            "status": j.status,
            "match_score": score,
            "match_tier": match.match_tier if match else "Suitable"
        })
        
    return {
        "total": len(results),
        "jobs": results[offset:offset + limit]
    }

@router.get("/companies")
def get_verified_companies(db: Session = Depends(get_db)):
    """Return list of verified employer career boards from the registry."""
    from app.models.schema import CompanyRegistry
    records = db.query(CompanyRegistry).all()
    return [
        {
            "id": r.id,
            "company_name": r.company_name,
            "official_website": r.official_website,
            "career_page": r.career_page,
            "ats_provider": r.ats_provider,
            "ats_board_identifier": r.ats_board_identifier,
            "supported_locations": r.supported_locations,
            "source_status": r.source_status
        } for r in records
    ]

@router.get("/{job_id}")
def get_job_detail(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    match = db.query(JobMatch).filter(JobMatch.job_id == job.id).first()
    return {
        "id": job.id,
        "company_name": job.company_name,
        "title": job.title,
        "category": job.category,
        "employment_type": job.employment_type,
        "work_arrangement": job.work_arrangement,
        "country_eligibility": job.country_eligibility,
        "is_india_eligible": job.is_india_eligible,
        "compensation_text": job.compensation_text,
        "currency": job.currency,
        "required_experience": job.required_experience,
        "application_url": job.application_url,
        "description": job.description,
        "status": job.status,
        "match": match.explanation_json if match else None,
        "match_score": match.overall_score if match else 85.0
    }

@router.post("/discover")
def trigger_discovery(query: str = "", db: Session = Depends(get_db)):
    """Discover new jobs, calculate match scores, and stage in database."""
    discovered = discovery_service.run_discovery(query=query)
    profile = db.query(CandidateProfile).first()
    
    cand_dict = {
        "skills": [s.name for s in profile.skills] if profile else ["Python", "RLHF", "React", "Django"],
        "total_experience_months": profile.total_experience_months if profile else 25
    }
    
    added_count = 0
    for item in discovered:
        existing = db.query(JobPosting).filter(
            JobPosting.company_name == item["company_name"],
            JobPosting.title == item["title"]
        ).first()
        
        if not existing:
            job = JobPosting(
                source_job_id=item.get("source_job_id"),
                company_name=item["company_name"],
                title=item["title"],
                category=item.get("category", "Software Development"),
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
            db.add(job)
            db.flush()
            
            # Match calculation
            match_res = matching_engine.calculate_match(item, cand_dict)
            job_match = JobMatch(
                job_id=job.id,
                profile_id=profile.id if profile else 1,
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
            )
            db.add(job_match)
            added_count += 1
            
            # Send Telegram notification for high matches (>= 90)
            if match_res["overall_score"] >= 90:
                telegram_service.notify_high_match_job(item, match_res["overall_score"])
                
    db.commit()
    return {"status": "success", "jobs_discovered": len(discovered), "new_jobs_added": added_count}

@router.post("/{job_id}/prepare")
def prepare_application(job_id: int, db: Session = Depends(get_db)):
    """Prepare tailored documents and queue for approval or assisted submission."""
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=400, detail="No active user found. Initialize profile first.")
        
    existing_app = db.query(Application).filter(
        Application.user_id == user.id,
        Application.job_id == job.id
    ).first()
    
    if existing_app:
        return {"status": "already_prepared", "application_id": existing_app.id}

    job_dict = {
        "title": job.title,
        "company_name": job.company_name,
        "location": job.location,
        "compensation_text": job.compensation_text
    }
    
    docs = document_generator.generate_application_documents(job_dict, {})
    
    app = Application(
        user_id=user.id,
        job_id=job.id,
        mode=ApplicationMode.MODE_B_APPROVAL,
        status=ApplicationStatus.AWAITING_APPROVAL,
        idempotency_key=str(uuid.uuid4()),
        match_score=92.0,
        tailored_headline=docs["tailored_headline"],
        tailored_summary=docs["tailored_summary"],
        cover_letter=docs["cover_letter"],
        answers_payload=docs["standard_answers"]
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    
    # Notify Telegram that application is ready for approval
    telegram_service.notify_ready_for_approval(app.id, job_dict, 92.0)
    
    return {"status": "success", "application_id": app.id, "state": app.status}
