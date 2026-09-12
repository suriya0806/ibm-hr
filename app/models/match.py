from datetime import datetime
from app.models import db

class MatchResult(db.Model):
    __tablename__ = "match_results"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job_descriptions.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    
    overall_score = db.Column(db.Float, nullable=False, default=0.0)
    skills_score = db.Column(db.Float, nullable=False, default=0.0)
    experience_score = db.Column(db.Float, nullable=False, default=0.0)
    semantic_score = db.Column(db.Float, nullable=False, default=0.0)
    
    # "Strongly Recommended", "Recommended", "Review", "Not Recommended"
    recommendation = db.Column(db.String(50), nullable=False, default="Review")
    
    matched_skills = db.Column(db.JSON, default=list)
    missing_skills = db.Column(db.JSON, default=list)
    key_strengths = db.Column(db.JSON, default=list)
    key_concerns = db.Column(db.JSON, default=list)
    rationale = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate.name if self.candidate else "Unknown",
            "candidate_email": self.candidate.email if self.candidate else "",
            "candidate_experience": self.candidate.total_experience_years if self.candidate else 0,
            "job_title": self.job.title if self.job else "Unknown",
            "overall_score": round(self.overall_score, 1),
            "skills_score": round(self.skills_score, 1),
            "experience_score": round(self.experience_score, 1),
            "semantic_score": round(self.semantic_score, 1),
            "recommendation": self.recommendation,
            "matched_skills": self.matched_skills or [],
            "missing_skills": self.missing_skills or [],
            "key_strengths": self.key_strengths or [],
            "key_concerns": self.key_concerns or [],
            "rationale": self.rationale or "",
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

