import os
from app import create_app, db
from app.models.job import JobDescription
from app.models.candidate import Candidate, ResumeData
from app.models.match import MatchResult
from app.models.interview import InterviewKit
from app.services.vector_service import VectorService
from app.graphs.matching_graph import build_matching_graph
from app.graphs.interview_graph import build_interview_graph

def seed():
    app = create_app()
    with app.app_context():
        print("🌱 Seeding HireMind AI Database...")

        # Clear existing records
        InterviewKit.query.delete()
        MatchResult.query.delete()
        ResumeData.query.delete()
        Candidate.query.delete()
        JobDescription.query.delete()
        db.session.commit()

        # 1. Seed Jobs
        jd_python = JobDescription(
            title="Senior Python & AI Engineer",
            department="AI & Engineering",
            experience_required="3-5 years",
            experience_years_min=3.0,
            required_skills=["Python", "LangGraph", "LangChain", "Flask", "SQLAlchemy", "Docker", "REST APIs"],
            nice_to_have_skills=["ChromaDB", "Kubernetes", "Groq API"],
            responsibilities=[
                "Architect stateful multi-agent workflows using LangGraph and LangChain.",
                "Integrate ChromaDB vector collections for semantic retrieval.",
                "Develop and deploy scalable REST APIs in Flask/FastAPI.",
                "Conduct code reviews and mentor junior engineering staff."
            ],
            raw_description=(
                "We are looking for a Senior Python & AI Engineer to build intelligent workflow agents and scalable REST APIs.\n"
                "Requirements: 3+ years in Python backend engineering, LangGraph/LangChain orchestration, ChromaDB, and Docker containerization."
            )
        )

        jd_java = JobDescription(
            title="Lead Java Backend Engineer",
            department="Core Banking Platform",
            experience_required="4+ years",
            experience_years_min=4.0,
            required_skills=["Java", "Spring Boot", "MySQL", "JDBC", "Microservices", "Kafka"],
            nice_to_have_skills=["Docker", "Kubernetes", "AWS", "Redis"],
            responsibilities=[
                "Build high-throughput transaction engines in Java 17 and Spring Boot.",
                "Optimize MySQL database queries, indexing, and connection pools.",
                "Design event-driven messaging with Apache Kafka."
            ],
            raw_description=(
                "Seeking a Lead Java Backend Developer to build high-throughput transaction engines and distributed microservices.\n"
                "Requirements: 4+ years in Java and Spring Boot, MySQL tuning, JDBC, and Kafka."
            )
        )

        db.session.add(jd_python)
        db.session.add(jd_java)
        db.session.commit()

        # 2. Seed Candidates
        # Candidate 1: Alex Mercer (Strong fit for Python AI)
        c1 = Candidate(
            name="Alex Mercer",
            email="alex.mercer@example.com",
            phone="+1-555-019-2834",
            location="San Francisco, CA",
            linkedin="https://linkedin.com/in/alex-mercer-ai",
            github="https://github.com/alexmercer-dev",
            summary="Senior Python Engineer with 4.5 years of experience architecting LLM-powered applications, multi-agent workflows with LangGraph and LangChain, and high-performance REST APIs.",
            total_experience_years=4.5
        )
        db.session.add(c1)
        db.session.flush()

        r1 = ResumeData(
            candidate_id=c1.id,
            filename="alex_senior_ai.docx",
            file_type="docx",
            raw_text="Alex Mercer. Skills: Python, LangGraph, LangChain, Flask, ChromaDB, Docker, SQLAlchemy, Git, Linux. 4.5 years experience.",
            education=[{"degree": "B.S. in Computer Science", "institution": "UC Berkeley", "year": "2019", "gpa": "3.85"}],
            skills={
                "technical": ["Python", "SQL", "LangGraph", "LangChain"],
                "frameworks": ["Flask", "FastAPI", "SQLAlchemy"],
                "tools": ["Docker", "Git", "ChromaDB", "Linux"],
                "soft": ["System Design", "Leadership"]
            },
            experience=[
                {"company": "NeuroTech Systems", "role": "Senior AI Engineer", "duration": "Feb 2022 - Present", "description": "Architected stateful LangGraph multi-agent pipelines and ChromaDB vector search."},
                {"company": "Apex Cloud Solutions", "role": "Python Developer", "duration": "Aug 2019 - Jan 2022", "description": "Developed REST APIs in Python Flask and SQLAlchemy."}
            ],
            projects=[
                {"title": "Autonomous Document Review Agent", "tech_stack": ["Python", "LangGraph", "ChromaDB"], "description": "Multi-agent system reducing legal document screening time by 65%."}
            ],
            certifications=["AWS Certified Developer - Associate"]
        )
        db.session.add(r1)

        # Candidate 2: Samantha Hayes (Moderate fit for Python AI)
        c2 = Candidate(
            name="Samantha Hayes",
            email="samantha.hayes@example.com",
            phone="+1-555-839-1029",
            location="Austin, TX",
            linkedin="https://linkedin.com/in/sam-hayes-dev",
            github="https://github.com/samhayes",
            summary="Full Stack Web Developer with 3.0 years of experience building modern user interfaces in React and backend APIs in Python Flask and Node.js.",
            total_experience_years=3.0
        )
        db.session.add(c2)
        db.session.flush()

        r2 = ResumeData(
            candidate_id=c2.id,
            filename="sam_fullstack.pdf",
            file_type="pdf",
            raw_text="Samantha Hayes. Skills: React, JavaScript, Python, Flask, Node.js, HTML, CSS, SQL, Docker. 3.0 years experience.",
            education=[{"degree": "B.S. in Information Technology", "institution": "UT Austin", "year": "2020"}],
            skills={
                "technical": ["JavaScript", "Python", "SQL"],
                "frameworks": ["React", "Flask", "Node.js"],
                "tools": ["Docker", "Git", "Postman"],
                "soft": ["Communication", "Agile"]
            },
            experience=[
                {"company": "BrightWave Technologies", "role": "Full Stack Developer", "duration": "Mar 2021 - Present", "description": "Built reactive interfaces in React and backend REST APIs in Python Flask."}
            ],
            projects=[
                {"title": "HR Analytics Dashboard", "tech_stack": ["React", "Flask", "PostgreSQL"], "description": "Web portal for tracking hiring metrics."}
            ]
        )
        db.session.add(r2)

        # Candidate 3: David Chen (Strong fit for Java, Review for Python)
        c3 = Candidate(
            name="David Chen",
            email="david.chen@example.com",
            phone="+1-555-472-8819",
            location="Seattle, WA",
            linkedin="https://linkedin.com/in/davidchen-java",
            github="https://github.com/dchen-backend",
            summary="Lead Java Backend Architect with 6.5 years of experience designing enterprise transaction engines using Java, Spring Boot, MySQL, and Kafka.",
            total_experience_years=6.5
        )
        db.session.add(c3)
        db.session.flush()

        r3 = ResumeData(
            candidate_id=c3.id,
            filename="david_java_architect.docx",
            file_type="docx",
            raw_text="David Chen. Skills: Java, Spring Boot, MySQL, JDBC, Microservices, Kafka, Docker, Kubernetes. 6.5 years experience.",
            education=[{"degree": "M.S. in Computer Science", "institution": "University of Washington", "year": "2017"}],
            skills={
                "technical": ["Java", "SQL", "Kafka"],
                "frameworks": ["Spring Boot", "Hibernate", "Microservices"],
                "tools": ["Docker", "Kubernetes", "Git"],
                "soft": ["Architecture", "Team Mentorship"]
            },
            experience=[
                {"company": "Pinnacle Financial Systems", "role": "Lead Java Engineer", "duration": "Jan 2021 - Present", "description": "Engineered microservices in Java 17 and Spring Boot handling 250M+ transactions."}
            ],
            projects=[
                {"title": "Core Payment Processing Engine", "tech_stack": ["Java", "Spring Boot", "MySQL", "Kafka"], "description": "Resilient banking checkout pipeline."}
            ]
        )
        db.session.add(r3)
        db.session.commit()

        # 3. Compute and save initial match rankings for Python AI role
        matching_graph = build_matching_graph()
        for cand, resume in [(c1, r1), (c2, r2), (c3, r3)]:
            cand_skills = []
            if isinstance(resume.skills, dict):
                for s in resume.skills.values():
                    cand_skills.extend(s)

            state = {
                "job_id": jd_python.id,
                "candidate_id": cand.id,
                "job_title": jd_python.title,
                "job_text": jd_python.raw_description,
                "candidate_name": cand.name,
                "candidate_text": resume.raw_text,
                "required_skills": jd_python.required_skills,
                "candidate_skills": cand_skills,
                "job_experience_min": jd_python.experience_years_min,
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
            matching_graph.invoke(state)

        # 4. Generate Interview Kit for Alex Mercer
        interview_graph = build_interview_graph()
        match_c1 = MatchResult.query.filter_by(job_id=jd_python.id, candidate_id=c1.id).first()
        kit_state = {
            "job_id": jd_python.id,
            "candidate_id": c1.id,
            "job_title": jd_python.title,
            "job_description": jd_python.raw_description,
            "candidate_name": c1.name,
            "candidate_summary": c1.summary,
            "candidate_skills": ["Python", "LangGraph", "LangChain", "Flask", "ChromaDB", "Docker"],
            "candidate_projects": r1.projects,
            "candidate_experience": r1.experience,
            "missing_skills": match_c1.missing_skills if match_c1 else [],
            "technical_questions": [],
            "resume_questions": [],
            "gap_questions": [],
            "behavioral_questions": [],
            "rubrics": {},
            "error": None
        }
        interview_graph.invoke(kit_state)

        print("✅ Database successfully seeded with:")
        print(f"   • {JobDescription.query.count()} Job Descriptions")
        print(f"   • {Candidate.query.count()} Candidates & Extracted Resumes")
        print(f"   • {MatchResult.query.count()} Evaluated Match Rankings")
        print(f"   • {InterviewKit.query.count()} AI Interview Kits")

if __name__ == "__main__":
    seed()

