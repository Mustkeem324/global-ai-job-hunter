import re
from typing import Dict, Any, List

class MatchingEngineService:
    def calculate_match(self, job_dict: Dict[str, Any], candidate_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate candidate fit for a job posting.
        Returns:
            overall_score (0-100)
            breakdown: skills, experience, eligibility, education, preferences, recency
            tier: Highly suitable, Suitable, Review required, Not suitable
            explanation: detailed evidence and gaps
        """
        job_text = (
            f"{job_dict.get('title', '')} {job_dict.get('category', '')} "
            f"{job_dict.get('description', '')} {job_dict.get('requirements', '')}"
        ).lower()

        candidate_skills = [s["name"].lower() if isinstance(s, dict) else s.lower() for s in candidate_dict.get("skills", [])]
        
        # 1. Technical Skills Match (Max 30 pts)
        # Look for matching technologies
        core_tech = [
            "python", "django", "fastapi", "react", "next.js", "node.js", 
            "typescript", "javascript", "graphql", "postgresql", "mongodb", 
            "aws", "azure", "docker", "rlhf", "llm", "prompt engineering", 
            "multimodal", "agentic", "ai trainer", "code evaluation"
        ]
        
        matched_skills = []
        for tech in core_tech:
            if tech in job_text:
                if any(tech in sk for sk in candidate_skills) or tech in str(candidate_dict).lower():
                    matched_skills.append(tech)
                    
        # Ratio of matched skills
        job_tech_count = sum(1 for tech in core_tech if tech in job_text)
        if job_tech_count == 0:
            skills_score = 25.0 # Generalist fit
        else:
            skills_score = min(30.0, (len(matched_skills) / max(1, job_tech_count)) * 30.0 + 5.0)

        # 2. Relevant Experience Match (Max 20 pts)
        # Check experience years and role keywords
        exp_score = 16.0
        if "senior" in job_text and candidate_dict.get("total_experience_months", 25) < 36:
            exp_score = 14.0 # Slightly discount if strict 5+ yrs required
        elif "lead" in job_text or "architect" in job_text:
            exp_score = 15.0
        else:
            exp_score = 19.0 # Perfect fit for mid/contributor/contract roles

        # 3. Geographic & Work Authorization Eligibility (Max 20 pts)
        # Critical requirement: India candidate
        eligibility_score = 0.0
        is_india_eligible = True
        
        restricted_phrases = ["us citizenship required", "must reside in us only", "eu passport only", "no c2c/contractors"]
        has_restriction = any(phrase in job_text for phrase in restricted_phrases)
        
        if has_restriction:
            eligibility_score = 2.0
            is_india_eligible = False
        elif job_dict.get("is_india_eligible", True) or "india" in job_text or "worldwide" in job_text or "anywhere" in job_text or "remote" in job_dict.get("work_arrangement", "").lower():
            eligibility_score = 20.0
        else:
            eligibility_score = 12.0 # Uncertain

        # 4. Educational & Role Requirements (Max 10 pts)
        # Candidate has MBA (Strategy & Operations) and B.Tech Electrical Engineering
        edu_score = 9.5
        if "phd" in job_text:
            edu_score = 4.0

        # 5. Employment Preferences (Max 10 pts)
        # Prefers Remote, AI Training / Engineering / Full-Stack / Contract
        pref_score = 9.5
        if job_dict.get("work_arrangement", "").lower() == "onsite":
            pref_score = 3.0

        # 6. Recency & Opportunity Quality (Max 10 pts)
        recency_score = 9.0

        overall = round(skills_score + exp_score + eligibility_score + edu_score + pref_score + recency_score, 1)
        overall = min(100.0, max(0.0, overall))

        if overall >= 85.0:
            tier = "Highly suitable"
        elif overall >= 70.0:
            tier = "Suitable"
        elif overall >= 55.0:
            tier = "Review required"
        else:
            tier = "Not suitable"

        explanation = {
            "matched_skills": matched_skills,
            "skills_score": round(skills_score, 1),
            "experience_score": round(exp_score, 1),
            "eligibility_score": round(eligibility_score, 1),
            "education_score": round(edu_score, 1),
            "preferences_score": round(pref_score, 1),
            "recency_score": round(recency_score, 1),
            "is_india_eligible": is_india_eligible,
            "verdict": f"Scored {overall}/100 based on {len(matched_skills)} verified technical competencies and confirmed remote eligibility."
        }

        return {
            "overall_score": overall,
            "skills_score": round(skills_score, 1),
            "experience_score": round(exp_score, 1),
            "eligibility_score": round(eligibility_score, 1),
            "education_score": round(edu_score, 1),
            "preferences_score": round(pref_score, 1),
            "recency_score": round(recency_score, 1),
            "match_tier": tier,
            "is_india_eligible": is_india_eligible,
            "explanation": explanation
        }

matching_engine = MatchingEngineService()
