import unittest
from app import create_app, db
from app.models.job import JobDescription
from app.models.candidate import Candidate, ResumeData
from app.graphs.matching_graph import build_matching_graph
from app.graphs.interview_graph import build_interview_graph

class TestLangGraphPipelines(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        with cls.app.app_context():
            db.init_app(cls.app)
            db.create_all()

    def test_matching_graph_execution(self):
        with self.app.app_context():
            # Setup mock Job and Candidate
            job = JobDescription(
                title="Python Developer",
                department="Engineering",
                experience_required="2+ years",
                experience_years_min=2.0,
                required_skills=["Python", "Flask", "Docker"],
                raw_description="Looking for Python Flask developer with Docker experience."
            )
            db.session.add(job)

            cand = Candidate(
                name="Alice Wonder",
                email="alice@test.com",
                total_experience_years=3.0,
                summary="Experienced Python engineer specializing in Flask."
            )
            db.session.add(cand)
            db.session.commit()

            resume = ResumeData(
                candidate_id=cand.id,
                filename="alice.pdf",
                raw_text="Alice Wonder. Skills: Python, Flask, Docker, Git. 3 years experience building APIs.",
                skills={"technical": ["Python", "Flask", "Docker", "Git"]}
            )
            db.session.add(resume)
            db.session.commit()

            # Run Matching Graph
            graph = build_matching_graph()
            state = {
                "job_id": job.id,
                "candidate_id": cand.id,
                "job_title": job.title,
                "job_text": job.raw_description,
                "candidate_name": cand.name,
                "candidate_text": resume.raw_text,
                "required_skills": job.required_skills,
                "candidate_skills": ["Python", "Flask", "Docker", "Git"],
                "job_experience_min": job.experience_years_min,
                "candidate_experience": cand.total_experience_years,
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

            result = graph.invoke(state)
            self.assertGreaterEqual(result["overall_score"], 60.0)
            self.assertIn("Python", result["matched_skills"])
            self.assertIn(result["recommendation"], ["Strongly Recommended", "Recommended", "Review"])

    def test_interview_graph_execution(self):
        with self.app.app_context():
            job = JobDescription(
                title="AI Engineer",
                department="AI",
                experience_required="3 years",
                experience_years_min=3.0,
                required_skills=["Python", "LangGraph"],
                raw_description="AI Engineer for multi-agent workflows."
            )
            db.session.add(job)

            cand = Candidate(
                name="Bob Test",
                email="bob@test.com",
                total_experience_years=3.0,
                summary="AI engineer building LangGraph pipelines."
            )
            db.session.add(cand)
            db.session.commit()

            graph = build_interview_graph()
            state = {
                "job_id": job.id,
                "candidate_id": cand.id,
                "job_title": job.title,
                "job_description": job.raw_description,
                "candidate_name": cand.name,
                "candidate_summary": cand.summary,
                "candidate_skills": ["Python", "LangGraph"],
                "candidate_projects": [{"title": "Agentic Search", "tech_stack": ["Python"], "description": "Built agent"}],
                "candidate_experience": [],
                "missing_skills": ["Kubernetes"],
                "technical_questions": [],
                "resume_questions": [],
                "gap_questions": [],
                "behavioral_questions": [],
                "rubrics": {},
                "error": None
            }

            result = graph.invoke(state)
            self.assertGreaterEqual(len(result["technical_questions"]), 1)
            self.assertGreaterEqual(len(result["resume_questions"]), 1)
            self.assertGreaterEqual(len(result["gap_questions"]), 1)
            self.assertGreaterEqual(len(result["behavioral_questions"]), 1)
            self.assertIn("scoring_scale", result["rubrics"])

if __name__ == "__main__":
    unittest.main()

