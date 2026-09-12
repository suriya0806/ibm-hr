from typing import TypedDict, List, Dict, Any, Optional

class ScreeningState(TypedDict):
    file_path: str
    filename: str
    file_type: str
    raw_text: str
    extracted_data: Dict[str, Any]
    candidate_id: Optional[int]
    indexed_in_chroma: bool
    error: Optional[str]


class MatchingState(TypedDict):
    job_id: int
    candidate_id: int
    job_title: str
    job_text: str
    candidate_name: str
    candidate_text: str
    required_skills: List[str]
    candidate_skills: List[str]
    job_experience_min: float
    candidate_experience: float
    semantic_score: float
    skills_score: float
    experience_score: float
    overall_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    key_strengths: List[str]
    key_concerns: List[str]
    recommendation: str
    rationale: str
    error: Optional[str]


class InterviewState(TypedDict):
    job_id: int
    candidate_id: int
    job_title: str
    job_description: str
    candidate_name: str
    candidate_summary: str
    candidate_skills: List[str]
    candidate_projects: List[Dict[str, Any]]
    candidate_experience: List[Dict[str, Any]]
    missing_skills: List[str]
    technical_questions: List[Dict[str, Any]]
    resume_questions: List[Dict[str, Any]]
    gap_questions: List[Dict[str, Any]]
    behavioral_questions: List[Dict[str, Any]]
    rubrics: Dict[str, Any]
    error: Optional[str]

