from flask import Blueprint, request, jsonify
from app.models import db
from app.models.job import JobDescription
from app.models.candidate import Candidate
from app.models.match import MatchResult
from app.models.interview import InterviewKit
from app.graphs.interview_graph import build_interview_graph

interview_bp = Blueprint("interview_api", __name__)

interview_graph = None

def get_interview_graph():
    global interview_graph
    if interview_graph is None:
        interview_graph = build_interview_graph()
    return interview_graph

@interview_bp.route("/<int:job_id>/<int:candidate_id>", methods=["GET"])
def get_interview_kit(job_id, candidate_id):
    kit = InterviewKit.query.filter_by(job_id=job_id, candidate_id=candidate_id).first()
    if not kit:
        return jsonify({"message": "Interview kit not generated yet", "kit": None}), 404
    return jsonify(kit.to_dict())

@interview_bp.route("/generate", methods=["POST"])
def generate_interview_kit():
    data = request.get_json() or {}
    job_id = data.get("job_id")
    candidate_id = data.get("candidate_id")

    if not job_id or not candidate_id:
        return jsonify({"error": "job_id and candidate_id are required"}), 400

    job = JobDescription.query.get_or_404(job_id)
    candidate = Candidate.query.get_or_404(candidate_id)

    # Check for existing match gaps
    match_result = MatchResult.query.filter_by(job_id=job.id, candidate_id=candidate.id).first()
    missing_skills = match_result.missing_skills if match_result else []

    resume = candidate.resume
    candidate_skills = []
    if resume and resume.skills:
        if isinstance(resume.skills, dict):
            for s_list in resume.skills.values():
                if isinstance(s_list, list):
                    candidate_skills.extend(s_list)
        elif isinstance(resume.skills, list):
            candidate_skills = resume.skills

    projects = resume.projects if resume and resume.projects else []
    experience = resume.experience if resume and resume.experience else []

    graph = get_interview_graph()

    initial_state = {
        "job_id": job.id,
        "candidate_id": candidate.id,
        "job_title": job.title,
        "job_description": job.raw_description,
        "candidate_name": candidate.name,
        "candidate_summary": candidate.summary or "",
        "candidate_skills": candidate_skills,
        "candidate_projects": projects,
        "candidate_experience": experience,
        "missing_skills": missing_skills,
        "technical_questions": [],
        "resume_questions": [],
        "gap_questions": [],
        "behavioral_questions": [],
        "rubrics": {},
        "error": None
    }

    try:
        final_state = graph.invoke(initial_state)
        kit = InterviewKit.query.filter_by(job_id=job.id, candidate_id=candidate.id).first()
        if kit:
            return jsonify({
                "message": "Interview kit successfully generated",
                "kit": kit.to_dict()
            }), 200
        else:
            return jsonify({
                "message": "Generated interview questions",
                "kit": {
                    "job_id": job.id,
                    "candidate_id": candidate.id,
                    "job_title": job.title,
                    "candidate_name": candidate.name,
                    "technical_questions": final_state.get("technical_questions", []),
                    "resume_questions": final_state.get("resume_questions", []),
                    "gap_questions": final_state.get("gap_questions", []),
                    "behavioral_questions": final_state.get("behavioral_questions", []),
                    "rubrics": final_state.get("rubrics", {})
                }
            }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to generate interview kit: {str(e)}"}), 500

