from flask import Blueprint, request, jsonify
from app.models import db
from app.models.job import JobDescription
from app.services.groq_client import GroqService
from app.services.vector_service import VectorService

job_bp = Blueprint("job_api", __name__)

@job_bp.route("", methods=["GET"])
def get_jobs():
    jobs = JobDescription.query.order_by(JobDescription.created_at.desc()).all()
    return jsonify([job.to_dict() for job in jobs])

@job_bp.route("/<int:job_id>", methods=["GET"])
def get_job(job_id):
    job = JobDescription.query.get_or_404(job_id)
    return jsonify(job.to_dict())

@job_bp.route("", methods=["POST"])
def create_job():
    data = request.get_json() or {}
    raw_desc = data.get("raw_description", "").strip()

    if not raw_desc:
        return jsonify({"error": "Job description content is required"}), 400

    title = data.get("title", "").strip()
    department = data.get("department", "Engineering").strip()
    experience_required = data.get("experience_required", "").strip()
    experience_years_min = float(data.get("experience_years_min", 0.0) or 0.0)
    required_skills = data.get("required_skills", [])
    nice_to_have_skills = data.get("nice_to_have_skills", [])

    # If title or skills are missing, use Groq to intelligently parse JD
    if not title or not required_skills:
        system_prompt = (
            "You are an expert HR Talent Acquisition Specialist. "
            "Extract structured job requirements from this job description text. "
            "Return ONLY a valid JSON object."
        )
        user_prompt = f"""
Job Description Text:
{raw_desc[:4000]}

Extract and return JSON with:
{{
  "title": "Clean Role Title (e.g. Senior Full Stack Engineer)",
  "department": "Department or function (e.g. Engineering)",
  "experience_years_min": 3.0,
  "experience_required": "3-5 years",
  "required_skills": ["Skill1", "Skill2", "Skill3"],
  "nice_to_have_skills": ["Bonus1", "Bonus2"],
  "responsibilities": ["Responsibility 1", "Responsibility 2"]
}}
"""
        extracted = GroqService.call_structured_json(user_prompt, system_prompt)
        if extracted:
            if not title:
                title = extracted.get("title", "Open Role")
            if not experience_required:
                experience_required = extracted.get("experience_required", "2+ years")
                experience_years_min = float(extracted.get("experience_years_min", 2.0) or 2.0)
            if not required_skills:
                required_skills = extracted.get("required_skills", [])
            if not nice_to_have_skills:
                nice_to_have_skills = extracted.get("nice_to_have_skills", [])

    if not title:
        first_line = raw_desc.split("\n")[0][:60].strip()
        title = first_line if first_line else "Software Role"

    job = JobDescription(
        title=title,
        department=department or "Engineering",
        experience_required=experience_required or "1-3 years",
        experience_years_min=experience_years_min,
        required_skills=required_skills if isinstance(required_skills, list) else [required_skills],
        nice_to_have_skills=nice_to_have_skills if isinstance(nice_to_have_skills, list) else [],
        raw_description=raw_desc
    )

    db.session.add(job)
    db.session.commit()

    # Index into ChromaDB
    try:
        vector_svc = VectorService()
        vector_svc.index_job(
            job_id=job.id,
            text=f"Title: {job.title}\nSkills: {', '.join(job.required_skills)}\n\n{raw_desc[:3000]}",
            metadata={"title": job.title, "department": job.department}
        )
    except Exception as e:
        print(f"[Jobs API] Chroma indexing warning: {e}")

    return jsonify(job.to_dict()), 201

@job_bp.route("/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
    job = JobDescription.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return jsonify({"message": f"Job {job_id} deleted successfully"}), 200

