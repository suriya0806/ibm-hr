from flask import Blueprint, render_template
from app.models.job import JobDescription
from app.models.candidate import Candidate
from app.models.match import MatchResult
from app.models.interview import InterviewKit

web_bp = Blueprint("web", __name__)

@web_bp.route("/")
def index():
    jobs_count = JobDescription.query.count()
    candidates_count = Candidate.query.count()
    matches_count = MatchResult.query.count()
    interviews_count = InterviewKit.query.count()

    recent_candidates = Candidate.query.order_by(Candidate.created_at.desc()).limit(5).all()
    recent_jobs = JobDescription.query.order_by(JobDescription.created_at.desc()).limit(5).all()

    return render_template(
        "index.html",
        jobs_count=jobs_count,
        candidates_count=candidates_count,
        matches_count=matches_count,
        interviews_count=interviews_count,
        recent_candidates=[c.to_dict() for c in recent_candidates],
        recent_jobs=[j.to_dict() for j in recent_jobs]
    )

@web_bp.route("/jobs")
def jobs_page():
    return render_template("jobs.html")

@web_bp.route("/screening")
def screening_page():
    return render_template("screening.html")

@web_bp.route("/matching")
def matching_page():
    return render_template("matching.html")

@web_bp.route("/interview")
def interview_page():
    return render_template("interview.html")

