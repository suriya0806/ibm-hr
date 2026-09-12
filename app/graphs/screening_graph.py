import json
import re
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from app.graphs.state import ScreeningState
from app.services.parser_service import ParserService
from app.services.vector_service import VectorService
from app.services.groq_client import GroqService
from app.models import db
from app.models.candidate import Candidate, ResumeData

def parse_document_node(state: ScreeningState) -> Dict[str, Any]:
    """
    Step 1: Extract text and determine file type from PDF/DOCX.
    """
    try:
        raw_text, file_type = ParserService.extract_text(state["file_path"])
        if not raw_text or len(raw_text.strip()) < 10:
            return {"error": "Failed to extract readable text from document."}
        return {
            "raw_text": raw_text,
            "file_type": file_type
        }
    except Exception as e:
        return {"error": f"Document extraction error: {str(e)}"}


def extract_profile_node(state: ScreeningState) -> Dict[str, Any]:
    """
    Step 2: Use Groq LLM with fallback heuristics to extract structured candidate profile.
    """
    if state.get("error"):
        return {}

    raw_text = state["raw_text"]
    heuristics = ParserService.extract_heuristic_metadata(raw_text)

    system_prompt = (
        "You are an expert HR Recruitment Resume Parser. "
        "Extract structured information from the provided resume text. "
        "Be accurate, concise, and return ONLY a valid JSON object with the specified schema."
    )

    user_prompt = f"""
Analyze this resume text and extract the structured candidate profile:

--- RESUME TEXT START ---
{raw_text[:7000]}
--- RESUME TEXT END ---

Return a JSON object with EXACTLY this structure:
{{
  "name": "Candidate Full Name",
  "email": "Email address",
  "phone": "Phone number",
  "location": "City, Country or State",
  "linkedin": "LinkedIn profile URL or handle",
  "github": "GitHub profile URL or handle",
  "portfolio": "Personal website or portfolio URL",
  "summary": "2-3 sentence executive profile summary highlighting key qualifications",
  "total_experience_years": 3.5,
  "education": [
    {{
      "degree": "B.S. in Computer Science",
      "institution": "University Name",
      "year": "2020",
      "gpa": "3.8/4.0"
    }}
  ],
  "skills": {{
    "technical": ["Python", "Java", "SQL"],
    "frameworks": ["Flask", "FastAPI", "React", "Spring Boot"],
    "tools": ["Docker", "Git", "Kubernetes", "AWS"],
    "soft": ["Problem Solving", "Communication", "Team Leadership"]
  }},
  "experience": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "duration": "Jan 2021 - Present",
      "description": "Key contributions and impact"
    }}
  ],
  "projects": [
    {{
      "title": "Project Name",
      "tech_stack": ["Python", "Docker"],
      "description": "Summary of project goals and achievements"
    }}
  ],
  "certifications": [
    "AWS Certified Solutions Architect",
    "Certified Kubernetes Administrator"
  ]
}}
"""

    extracted = GroqService.call_structured_json(user_prompt, system_prompt)

    # Fallback if Groq call failed or returned empty
    if not extracted:
        extracted = _fallback_heuristic_extraction(raw_text, state["filename"], heuristics)

    # Clean and sanitize extracted fields
    if not extracted.get("name") or extracted.get("name") in ["Candidate Full Name", "Unknown"]:
        extracted["name"] = _guess_name_from_text(raw_text, state["filename"])
    if not extracted.get("email") and heuristics.get("email"):
        extracted["email"] = heuristics["email"]
    if not extracted.get("phone") and heuristics.get("phone"):
        extracted["phone"] = heuristics["phone"]
    if not extracted.get("github") and heuristics.get("github"):
        extracted["github"] = heuristics["github"]
    if not extracted.get("linkedin") and heuristics.get("linkedin"):
        extracted["linkedin"] = heuristics["linkedin"]

    return {"extracted_data": extracted}


def _guess_name_from_text(text: str, filename: str) -> str:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:5]:
        if len(line.split()) in [2, 3, 4] and not any(char.isdigit() for char in line) and "@" not in line:
            return line
    clean_fn = re.sub(r'[_ -]+', ' ', filename.rsplit('.', 1)[0])
    return clean_fn.title()


def _fallback_heuristic_extraction(text: str, filename: str, heuristics: dict) -> dict:
    name = _guess_name_from_text(text, filename)
    # Simple skill keywords matching
    common_skills = [
        "python", "java", "c++", "c#", "javascript", "typescript", "react", "angular", "vue",
        "node.js", "django", "flask", "fastapi", "spring boot", "sql", "postgresql", "mysql",
        "mongodb", "redis", "docker", "kubernetes", "aws", "azure", "gcp", "git", "ci/cd",
        "rest api", "graphql", "html", "css", "machine learning", "deep learning", "pytorch",
        "tensorflow", "pandas", "numpy", "scikit-learn", "linux", "agile", "scrum"
    ]
    found_skills = []
    text_lower = text.lower()
    for s in common_skills:
        if re.search(r'\b' + re.escape(s) + r'\b', text_lower):
            found_skills.append(s.title())

    return {
        "name": name,
        "email": heuristics.get("email", ""),
        "phone": heuristics.get("phone", ""),
        "location": "Not specified",
        "linkedin": heuristics.get("linkedin", ""),
        "github": heuristics.get("github", ""),
        "portfolio": "",
        "summary": f"Professional profile for {name} with expertise in {', '.join(found_skills[:5])}.",
        "total_experience_years": 2.0,
        "education": [],
        "skills": {
            "technical": found_skills[:8],
            "frameworks": found_skills[8:14],
            "tools": ["Git"],
            "soft": ["Problem Solving", "Collaboration"]
        },
        "experience": [],
        "projects": [],
        "certifications": []
    }


def save_and_index_node(state: ScreeningState) -> Dict[str, Any]:
    """
    Step 3: Persist candidate and extracted resume data into DB and ChromaDB vector store.
    """
    if state.get("error"):
        return {}

    data = state["extracted_data"]
    raw_text = state["raw_text"]

    try:
        # Check if candidate with this email exists
        email = data.get("email", "").strip().lower()
        candidate = None
        if email:
            candidate = Candidate.query.filter_by(email=email).first()

        if not candidate:
            candidate = Candidate(
                name=data.get("name", "Unknown Candidate"),
                email=data.get("email"),
                phone=data.get("phone"),
                location=data.get("location"),
                linkedin=data.get("linkedin"),
                github=data.get("github"),
                portfolio=data.get("portfolio"),
                summary=data.get("summary"),
                total_experience_years=float(data.get("total_experience_years", 0.0) or 0.0)
            )
            db.session.add(candidate)
            db.session.flush()
        else:
            # Update candidate
            candidate.name = data.get("name", candidate.name)
            candidate.phone = data.get("phone", candidate.phone)
            candidate.location = data.get("location", candidate.location)
            candidate.summary = data.get("summary", candidate.summary)
            candidate.total_experience_years = float(data.get("total_experience_years", candidate.total_experience_years) or 0.0)

        # Update or create ResumeData
        resume = ResumeData.query.filter_by(candidate_id=candidate.id).first()
        if not resume:
            resume = ResumeData(candidate_id=candidate.id)
            db.session.add(resume)

        resume.filename = state["filename"]
        resume.file_type = state["file_type"]
        resume.raw_text = raw_text
        resume.education = data.get("education", [])
        resume.skills = data.get("skills", {})
        resume.experience = data.get("experience", [])
        resume.projects = data.get("projects", [])
        resume.certifications = data.get("certifications", [])

        db.session.commit()

        # ChromaDB Indexing
        try:
            vector_svc = VectorService()
            all_skills = []
            if isinstance(data.get("skills"), dict):
                for skill_list in data["skills"].values():
                    if isinstance(skill_list, list):
                        all_skills.extend(skill_list)
            elif isinstance(data.get("skills"), list):
                all_skills = data["skills"]

            vector_svc.index_resume(
                candidate_id=candidate.id,
                text=f"Candidate: {candidate.name}\nSummary: {candidate.summary}\nSkills: {', '.join(all_skills)}\n\n{raw_text[:3000]}",
                metadata={
                    "name": candidate.name,
                    "email": candidate.email or "",
                    "experience": candidate.total_experience_years
                }
            )
        except Exception as e:
            print(f"[ScreeningGraph] Warning: Chroma indexing skipped: {e}")

        return {
            "candidate_id": candidate.id,
            "indexed_in_chroma": True
        }
    except Exception as e:
        db.session.rollback()
        return {"error": f"Database persistence error: {str(e)}"}


def build_screening_graph():
    """
    Constructs the LangGraph workflow for resume screening.
    """
    workflow = StateGraph(ScreeningState)

    workflow.add_node("parse_document", parse_document_node)
    workflow.add_node("extract_profile", extract_profile_node)
    workflow.add_node("save_and_index", save_and_index_node)

    workflow.set_entry_point("parse_document")

    def check_error(state: ScreeningState):
        if state.get("error"):
            return END
        return "extract_profile"

    def check_extract_error(state: ScreeningState):
        if state.get("error"):
            return END
        return "save_and_index"

    workflow.add_conditional_edges("parse_document", check_error, {"extract_profile": "extract_profile", END: END})
    workflow.add_conditional_edges("extract_profile", check_extract_error, {"save_and_index": "save_and_index", END: END})
    workflow.add_edge("save_and_index", END)

    return workflow.compile()

