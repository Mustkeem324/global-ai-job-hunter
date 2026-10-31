import pytest
from app.services.matching_engine import matching_engine

def test_matching_engine_high_match():
    job = {
        "title": "Senior AI Trainer - Python & RLHF",
        "category": "AI Training",
        "description": "Evaluate LLM reasoning and python coding tasks using RLHF rubrics.",
        "country_eligibility": "Worldwide",
        "work_arrangement": "Remote",
        "is_india_eligible": True
    }
    candidate = {
        "skills": ["Python", "RLHF", "LLM Evaluation", "Prompt Engineering"],
        "total_experience_months": 25
    }
    
    result = matching_engine.calculate_match(job, candidate)
    
    assert result["overall_score"] >= 80.0
    assert result["match_tier"] in ("Highly suitable", "Suitable")
    assert result["is_india_eligible"] is True
    assert result["skills_score"] <= 30.0
    assert result["eligibility_score"] == 20.0

def test_matching_engine_restricted_job():
    job = {
        "title": "Defense Analyst",
        "category": "Defense",
        "description": "US Citizenship Required. No C2C/contractors.",
        "country_eligibility": "United States Only",
        "work_arrangement": "Onsite",
        "is_india_eligible": False
    }
    candidate = {
        "skills": ["Python", "RLHF"],
        "total_experience_months": 25
    }
    
    result = matching_engine.calculate_match(job, candidate)
    assert result["is_india_eligible"] is False
    assert result["eligibility_score"] <= 5.0
