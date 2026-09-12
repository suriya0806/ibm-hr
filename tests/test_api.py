import io
import unittest
from app import create_app, db
from app.models.job import JobDescription
from app.models.candidate import Candidate

class TestFlaskAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_pages_render(self):
        for path in ["/", "/jobs", "/screening", "/matching", "/interview"]:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Path {path} failed")

    def test_job_lifecycle(self):
        # Create Job
        res = self.client.post("/api/jobs", json={
            "title": "API Test Engineer",
            "department": "QA",
            "experience_required": "2 years",
            "experience_years_min": 2.0,
            "required_skills": ["Python", "PyTest", "Docker"],
            "raw_description": "We need an API test engineer with Python and Docker."
        })
        self.assertEqual(res.status_code, 201)
        job_data = res.get_json()
        job_id = job_data["id"]

        # Get Jobs
        res = self.client.get("/api/jobs")
        self.assertEqual(res.status_code, 200)
        jobs = res.get_json()
        self.assertTrue(any(j["id"] == job_id for j in jobs))

        # Delete Job
        del_res = self.client.delete(f"/api/jobs/{job_id}")
        self.assertEqual(del_res.status_code, 200)

    def test_resume_upload_and_match(self):
        # Create Job
        job_res = self.client.post("/api/jobs", json={
            "title": "Backend Pythonist",
            "department": "Engineering",
            "experience_required": "3 years",
            "experience_years_min": 3.0,
            "required_skills": ["Python", "Flask", "SQL"],
            "raw_description": "Backend engineer skilled in Python, Flask, and SQL databases."
        })
        job_id = job_res.get_json()["id"]

        # Upload Mock Resume (TXT format)
        resume_content = (
            "Charlie Bucket\n"
            "Email: charlie@bucket.com\n"
            "Phone: 555-9988\n"
            "Skills: Python, Flask, SQL, Docker, Git\n"
            "Summary: Backend developer with 3.5 years of experience in Python and Flask.\n"
            "Experience: 3.5 years as Software Engineer.\n"
        )
        data = {
            "files": (io.BytesIO(resume_content.encode("utf-8")), "charlie_resume.txt")
        }
        upload_res = self.client.post(
            "/api/resumes/upload",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(upload_res.status_code, 200)
        upload_json = upload_res.get_json()
        self.assertEqual(len(upload_json["processed"]), 1)
        cand_id = upload_json["processed"][0]["candidate"]["id"]

        # Run Matching
        match_res = self.client.post("/api/match/run", json={"job_id": job_id})
        self.assertEqual(match_res.status_code, 200)
        match_json = match_res.get_json()
        self.assertGreaterEqual(len(match_json["results"]), 1)

        # Generate Interview Kit
        kit_res = self.client.post("/api/interview/generate", json={
            "job_id": job_id,
            "candidate_id": cand_id
        })
        self.assertEqual(kit_res.status_code, 200)
        kit_json = kit_res.get_json()
        self.assertIn("kit", kit_json)
        self.assertGreaterEqual(len(kit_json["kit"]["technical_questions"]), 1)

if __name__ == "__main__":
    unittest.main()

