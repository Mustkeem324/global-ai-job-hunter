from typing import Dict, Any

class DocumentGeneratorService:
    def generate_application_documents(self, job_dict: Dict[str, Any], candidate_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate tailored cover letter, headline, summary, and standard answers
        using substantiated facts only.
        """
        job_title = job_dict.get("title", "Software Engineer")
        company = job_dict.get("company_name", "the hiring organization")
        location = job_dict.get("location", "Remote")
        comp = job_dict.get("compensation_text", "competitive market rate")
        
        # 1. Tailored Headline
        if any(kw in job_title.lower() for kw in ("trainer", "evaluat", "rlhf", "model")):
            headline = f"AI Trainer & Model Evaluation Specialist | RLHF, Reasoning & Code Review"
        elif any(kw in job_title.lower() for kw in ("fullstack", "full stack", "full-stack")):
            headline = f"Full-Stack Software Engineer | Python, React, Next.js & REST/GraphQL APIs"
        elif "python" in job_title.lower():
            headline = f"Python Developer & AI Solutions Engineer | Django, FastAPI & Automation"
        else:
            headline = f"AI Engineer & Full-Stack Developer | Generative AI & Scalable Systems"

        # 2. Tailored Professional Summary
        summary = (
            f"AI engineer and full-stack developer with direct experience in LLM evaluation, "
            f"prompt engineering, and RLHF criteria alongside production web and API delivery. "
            f"Currently contributing to AI evaluation workstreams (Handshake Project Dynamo, Outlier AI) "
            f"and founder of FreelanceKar with 200+ delivered projects spanning AI agents, Python automation, "
            f"Next.js, Django, PostgreSQL, and cloud deployments on AWS and Azure. "
            f"Holds an MBA in Strategy & Operations (UPES, 8.90 CGPA) and B.Tech in Electrical Engineering (Jamia Millia Islamia, 83.3%)."
        )

        # 3. Personalized Cover Letter
        cover_letter = (
            f"Dear Hiring Team at {company},\n\n"
            f"I am writing to express my enthusiastic interest in the {job_title} position. "
            f"With active contributions in frontier LLM evaluation and RLHF workflows at Handshake Project Dynamo "
            f"and Outlier AI, combined with over 200 delivered client and independent software projects through FreelanceKar, "
            f"I offer a rare blend of rigorous model assessment capabilities and end-to-end full-stack software craftsmanship.\n\n"
            f"Key qualifications relevant to this role:\n"
            f"• AI Model Evaluation & RLHF: Skilled in evaluating instruction-following, multi-turn reasoning, safety, and code correctness against exacting rubrics.\n"
            f"• Full-Stack & Systems Engineering: Extensive hands-on delivery in Python (Django, FastAPI), TypeScript/JavaScript (React, Next.js, Node.js), GraphQL, and relational/NoSQL databases (PostgreSQL, MongoDB).\n"
            f"• Proven Execution: Architected and deployed production autonomous scheduling agents, on-chain Web3 bots, and enterprise security dashboards with AWS and Azure cloud integration.\n"
            f"• Academic Foundation: MBA in Strategy & Operations (UPES Dehradun, 8.90 CGPA) and B.Tech in Electrical Engineering (Jamia Millia Islamia, First Class Honours 83.3%).\n\n"
            f"I am based in India and fully available for remote engagement via international independent contractor (1099/B2B) or EOR agreements. "
            f"My complete portfolio and verifiable repositories are accessible at https://github.com/Mustkeem324 and https://freelancekar.com.\n\n"
            f"Thank you for considering my application. I look forward to discussing how my experience can contribute to {company}'s goals.\n\n"
            f"Warm regards,\n"
            f"Mustkeem Ahmad\n"
            f"+91-7905800532 | mustkeem324@gmail.com | Hyderabad / New Delhi, India"
        )

        # 4. Standard Factual Answers Library
        standard_answers = {
            "work_authorization": "Authorized to work remotely from India as an international independent contractor (B2B/1099) or via Employer of Record (EOR).",
            "visa_sponsorship_needed": "No visa sponsorship required for remote independent contractor or global remote roles.",
            "notice_period": "Immediately available / flexible schedule (up to 40 hours/week).",
            "compensation_expectation": f"{comp} (aligned with the stated compensation band).",
            "years_of_experience": "2+ years of specialized AI evaluation & full-stack development, with 5+ years of broader software consulting and engineering delivery.",
            "github_portfolio": "https://github.com/Mustkeem324",
            "personal_website": "https://freelancekar.com",
            "relevant_project": "Smart Scheduler AI Agent (Voice-driven intent parsing with LLM integration) and Full-Stack Product Application (Django + GraphQL + React/Apollo)."
        }

        return {
            "tailored_headline": headline,
            "tailored_summary": summary,
            "cover_letter": cover_letter,
            "standard_answers": standard_answers
        }

    def generate_tailored_summary(self, candidate_dict: Dict[str, Any], job_dict: Dict[str, Any]) -> str:
        docs = self.generate_application_documents(job_dict, candidate_dict)
        return docs["tailored_summary"]

    def generate_cover_letter(self, candidate_dict: Dict[str, Any], job_dict: Dict[str, Any]) -> str:
        docs = self.generate_application_documents(job_dict, candidate_dict)
        return docs["cover_letter"]

document_generator = DocumentGeneratorService()
