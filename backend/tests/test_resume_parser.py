import pytest
from app.services.resume_parser import resume_parser_service

def test_resume_parser_profile_extraction():
    sample_text = """
    Mustkeem Ahmad
    Hyderabad, India
    mustkeem324@gmail.com | +91-7905800532 | github.com/Mustkeem324
    
    AI engineer and full-stack developer with experience in LLM evaluation, prompt engineering, RLHF, and Next.js.
    Delivered 200+ projects at FreelanceKar across Python, Django, React, and PostgreSQL.
    Contributed to Handshake Project Dynamo and Outlier AI.
    """
    
    parsed = resume_parser_service.parse_profile(sample_text)
    
    assert parsed["full_name"] == "Mustkeem Ahmad"
    assert parsed["email"] == "mustkeem324@gmail.com"
    assert "github.com/Mustkeem324" in parsed["github_url"]
    
    # Skills check
    skill_names = [s["name"] for s in parsed["skills"]]
    assert "RLHF" in skill_names
    assert "LLM Evaluation" in skill_names
    assert "Python" in skill_names
    assert "React" in skill_names

    # Check evidence extraction
    for sk in parsed["skills"]:
        assert len(sk["evidence"]) > 0
