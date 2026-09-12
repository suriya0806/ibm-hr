from datetime import datetime
from app.models import db

class InterviewKit(db.Model):
    __tablename__ = "interview_kits"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job_descriptions.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)

    technical_questions = db.Column(db.JSON, default=list)
    resume_questions = db.Column(db.JSON, default=list)
    gap_questions = db.Column(db.JSON, default=list)
    behavioral_questions = db.Column(db.JSON, default=list)
    rubrics = db.Column(db.JSON, default=dict)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate.name if self.candidate else "Unknown",
            "job_title": self.job.title if self.job else "Unknown",
            "technical_questions": self.technical_questions or [],
            "resume_questions": self.resume_questions or [],
            "gap_questions": self.gap_questions or [],
            "behavioral_questions": self.behavioral_questions or [],
            "rubrics": self.rubrics or {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

