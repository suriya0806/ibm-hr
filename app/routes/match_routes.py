from flask import Blueprint, request, jsonify
from app.models import db
from app.models.job import JobDescription
from app.models.candidate import Candidate
from app.models.match import MatchResult
from app.graphs.matching_graph import build_matching_graph

match_bp = Blueprint("match_api", __name__)

matching_graph = None

def get_matching_graph():
    global matching_graph
    if matching_graph is None:
        matching_graph = build_matching_graph()
    return matching_graph

@match_bp.route("/job/<int:job_id>", methods=["GET"])
def get_job_matches(job_id):
    matches = MatchResult.query.filter_by(job_id=job_id).order_by(MatchResult.overall_score.desc()).all()
    return jsonify([m.to_dict() for m in matches])

@match_bp.route("/<int:match_id>", methods=["GET"])
def get_match_detail(match_id):
    match_record = MatchResult.query.get_or_404(match_id)
    return jsonify(match_record.to_dict())

@match_bp.route("/run", methods=["POST"])
def run_matching():
    data = request.get_json() or {}
    job_id = data.get("job_id")
    candidate_ids = data.get("candidate_ids")

    if not job_id:
        return jsonify({"error": "job_id is required"}), 400

    job = JobDescription.query.get_or_404(job_id)

    if candidate_ids and isinstance(candidate_ids, list):
        candidates = Candidate.query.filter(Candidate.id.in_(candidate_ids)).all()
    else:
        # Match against all registered candidates
        candidates = Candidate.query.all()

    if not candidates:
        return jsonify({"message": "No candidates found to match against", "results": []}), 200

    graph = get_matching_graph()
    results = []

    for candidate in candidates:
        # Extract candidate text & skills
        resume_data = candidate.resume
        cand_text = resume_data.raw_text if resume_data else (candidate.summary or "")
        
        cand_skills = []
        if resume_data and resume_data.skills:
            if isinstance(resume_data.skills, dict):
                for skill_list in resume_data.skills.values():
                    if isinstance(skill_list, list):
                        cand_skills.extend(skill_list)
            elif isinstance(resume_data.skills, list):
                cand_skills = resume_data.skills

        initial_state = {
            "job_id": job.id,
            "candidate_id": candidate.id,
            "job_title": job.title,
            "job_text": f"{job.title}\n{job.raw_description}",
            "candidate_name": candidate.name,
            "candidate_text": cand_text,
            "required_skills": job.required_skills or [],
            "candidate_skills": cand_skills,
            "job_experience_min": job.experience_years_min,
            "candidate_experience": candidate.total_experience_years,
            "semantic_score": 0.0,
            "skills_score": 0.0,
            "experience_score": 0.0,
            "overall_score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "key_strengths": [],
            "key_concerns": [],
            "recommendation": "Review",
            "rationale": "",
            "error": None
        }

        try:
            final_state = graph.invoke(initial_state)
            match_record = MatchResult.query.filter_by(job_id=job.id, candidate_id=candidate.id).first()
            if match_record:
                results.append(match_record.to_dict())
        except Exception as e:
            print(f"[Match API] Error matching candidate {candidate.id}: {e}")

    # Sort results by overall score descending
    results.sort(key=lambda x: x["overall_score"], reverse=True)

    return jsonify({
        "message": f"Successfully evaluated {len(results)} candidates for {job.title}.",
        "job": job.to_dict(),
        "results": results
    }), 200

