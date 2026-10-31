import os
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.core.database import get_db
from app.core.config import settings
from app.models.schema import User, CandidateProfile, Resume, Skill, ProfessionalExperience
from app.services.resume_parser import resume_parser_service

router = APIRouter(prefix="/resumes", tags=["Resumes & Candidate Profile"])

@router.get("/")
def list_workspace_resumes():
    """List all detected resume files in the configured folder."""
    files = resume_parser_service.scan_folder(settings.RESUME_FOLDER)
    return {
        "folder": settings.RESUME_FOLDER,
        "total_found": len(files),
        "files": files
    }

@router.post("/scan")
def scan_custom_folder(folder_path: str = Body(..., embed=True)):
    """Scan an arbitrary folder path for resumes."""
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=400, detail="Folder path does not exist.")
    files = resume_parser_service.scan_folder(folder_path)
    return {
        "folder": folder_path,
        "total_found": len(files),
        "files": files
    }

@router.post("/parse")
def parse_resume_file(file_path: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """Parse a resume file and populate/update candidate profile in database."""
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    raw_text = resume_parser_service.extract_text_from_file(file_path)
    parsed = resume_parser_service.parse_profile(raw_text, file_path)
    
    # Ensure default user
    user = db.query(User).first()
    if not user:
        user = User(
            email=parsed["email"],
            name=parsed["full_name"],
            role="candidate"
        )
        db.add(user)
        db.flush()
        
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not profile:
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
    else:
        profile.full_name = parsed["full_name"]
        profile.email = parsed["email"]
        profile.phone = parsed["phone"]
        profile.headline = parsed["headline"]
        profile.summary = parsed["summary"]
        profile.github_url = parsed["github_url"]
        profile.portfolio_url = parsed["portfolio_url"]
        profile.education_data = parsed["education"]

    # Save Resume document record
    resume_doc = Resume(
        profile_id=profile.id,
        file_path=file_path,
        file_name=os.path.basename(file_path),
        file_type=os.path.splitext(file_path)[1].lower().replace(".", ""),
        file_size_bytes=os.path.getsize(file_path),
        raw_text=raw_text,
        is_primary=True
    )
    db.add(resume_doc)

    # Re-populate skills
    db.query(Skill).filter(Skill.profile_id == profile.id).delete()
    for sk in parsed["skills"]:
        skill = Skill(
            profile_id=profile.id,
            name=sk["name"],
            category=sk["category"],
            proficiency_level=sk["proficiency"],
            evidence_text=sk["evidence"]
        )
        db.add(skill)

    # Re-populate experiences
    db.query(ProfessionalExperience).filter(ProfessionalExperience.profile_id == profile.id).delete()
    for exp in parsed["experiences"]:
        pe = ProfessionalExperience(
            profile_id=profile.id,
            company=exp["company"],
            role_title=exp["role_title"],
            start_date=exp["start_date"],
            end_date=exp["end_date"],
            is_current=exp["is_current"],
            is_remote=exp["is_remote"],
            description=exp["description"],
            skills_used=exp.get("skills_used", [])
        )
        db.add(pe)

    db.commit()
    return {
        "status": "success",
        "profile_id": profile.id,
        "candidate": parsed["full_name"],
        "skills_count": len(parsed["skills"]),
        "experiences_count": len(parsed["experiences"])
    }

@router.get("/profile")
def get_candidate_profile(db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not yet initialized. Please parse a resume first.")
        
    skills = db.query(Skill).filter(Skill.profile_id == profile.id).all()
    experiences = db.query(ProfessionalExperience).filter(ProfessionalExperience.profile_id == profile.id).all()
    resumes = db.query(Resume).filter(Resume.profile_id == profile.id).all()
    
    return {
        "id": profile.id,
        "full_name": profile.full_name,
        "email": profile.email,
        "phone": profile.phone,
        "location": profile.location,
        "country": profile.country,
        "headline": profile.headline,
        "summary": profile.summary,
        "github_url": profile.github_url,
        "portfolio_url": profile.portfolio_url,
        "education": profile.education_data or [],
        "certifications": profile.certifications_data or [],
        "projects": profile.projects_data or [],
        "work_authorization": profile.work_authorization or {},
        "uncertain_claims": profile.uncertain_claims or [],
        "traceable_claims": profile.traceable_claims or [],
        "skills": [{"name": s.name, "category": s.category, "evidence": s.evidence_text} for s in skills],
        "experiences": [
            {
                "company": e.company,
                "role_title": e.role_title,
                "start_date": e.start_date,
                "end_date": e.end_date,
                "description": e.description
            } for e in experiences
        ],
        "active_resumes": [
            {"id": r.id, "file_name": r.file_name, "file_path": r.file_path, "is_primary": r.is_primary} for r in resumes
        ]
    }

@router.post("/resolve-uncertainty")
def resolve_uncertainty(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Allow candidate to confirm or resolve an uncertain claim (e.g. experience seniority or relocation)."""
    profile = db.query(CandidateProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    
    field = payload.get("field")
    confirmed_value = payload.get("confirmed_value")
    
    current_uncertain = list(profile.uncertain_claims or [])
    updated_uncertain = []
    resolved = False
    
    for item in current_uncertain:
        if item.get("field") == field:
            item["resolved"] = True
            item["confirmed_value"] = confirmed_value
            resolved = True
        updated_uncertain.append(item)
        
    profile.uncertain_claims = updated_uncertain
    db.commit()
    return {"status": "success", "field": field, "confirmed_value": confirmed_value, "resolved": resolved}
