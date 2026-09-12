from datetime import datetime
from app.models import db

class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    linkedin = db.Column(db.String(255), nullable=True)
    github = db.Column(db.String(255), nullable=True)
    portfolio = db.Column(db.String(255), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    total_experience_years = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    resume = db.relationship("ResumeData", backref="candidate", uselist=False, cascade="all, delete-orphan")
    matches = db.relationship("MatchResult", backref="candidate", cascade="all, delete-orphan", lazy="dynamic")
    interview_kits = db.relationship("InterviewKit", backref="candidate", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "linkedin": self.linkedin,
            "github": self.github,
            "portfolio": self.portfolio,
            "summary": self.summary,
            "total_experience_years": self.total_experience_years,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resume": self.resume.to_dict() if self.resume else None
        }


class ResumeData(db.Model):
    __tablename__ = "resume_data"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20), default="pdf")
    raw_text = db.Column(db.Text, nullable=False)
    education = db.Column(db.JSON, default=list)
    skills = db.Column(db.JSON, default=dict)
    experience = db.Column(db.JSON, default=list)
    projects = db.Column(db.JSON, default=list)
    certifications = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "education": self.education or [],
            "skills": self.skills or {},
            "experience": self.experience or [],
            "projects": self.projects or [],
            "certifications": self.certifications or [],
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

