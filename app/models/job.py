from datetime import datetime
from app.models import db

class JobDescription(db.Model):
    __tablename__ = "job_descriptions"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100), nullable=True, default="Engineering")
    experience_required = db.Column(db.String(100), nullable=True, default="0-2 years")
    experience_years_min = db.Column(db.Float, default=0.0)
    required_skills = db.Column(db.JSON, default=list)
    nice_to_have_skills = db.Column(db.JSON, default=list)
    responsibilities = db.Column(db.JSON, default=list)
    raw_description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    matches = db.relationship("MatchResult", backref="job", cascade="all, delete-orphan", lazy="dynamic")
    interview_kits = db.relationship("InterviewKit", backref="job", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "department": self.department,
            "experience_required": self.experience_required,
            "experience_years_min": self.experience_years_min,
            "required_skills": self.required_skills or [],
            "nice_to_have_skills": self.nice_to_have_skills or [],
            "responsibilities": self.responsibilities or [],
            "raw_description": self.raw_description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "match_count": self.matches.count() if hasattr(self, "matches") else 0
        }

