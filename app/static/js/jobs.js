// Jobs Management Module for HireMind AI

document.addEventListener("DOMContentLoaded", () => {
    loadJobs();

    const jobForm = document.getElementById("createJobForm");
    if (jobForm) {
        jobForm.addEventListener("submit", handleCreateJob);
    }
});

const SAMPLE_JDS = {
    "python_ai": {
        title: "Senior Python & AI Engineer",
        department: "AI & Engineering",
        experience_required: "3-5 years",
        experience_years_min: 3.0,
        required_skills: ["Python", "Flask", "LangChain", "SQLAlchemy", "REST APIs", "Docker"],
        nice_to_have_skills: ["LangGraph", "ChromaDB", "Kubernetes", "Groq API"],
        raw_description: `We are looking for a Senior Python & AI Engineer to build intelligent workflow agents and scalable REST APIs.
Responsibilities:
- Design and implement stateful agentic workflows using LangGraph and LangChain.
- Integrate high-performance vector databases (ChromaDB) for dense semantic retrieval.
- Build reliable REST services using Python (Flask / FastAPI) and SQLAlchemy.
- Collaborate with product managers to deliver explainable AI features.

Requirements:
- 3+ years of professional backend software development in Python.
- Proven experience with LLM orchestration (LangChain, LangGraph, or LlamaIndex).
- Strong proficiency in relational databases (PostgreSQL/MySQL/SQLite) and ORMs.
- Hands-on experience with containerization (Docker) and CI/CD pipelines.`
    },
    "fullstack": {
        title: "Full Stack Web Developer",
        department: "Product Engineering",
        experience_required: "2-4 years",
        experience_years_min: 2.0,
        required_skills: ["JavaScript", "React", "Node.js", "HTML", "CSS", "SQL"],
        nice_to_have_skills: ["TypeScript", "Bootstrap", "AWS", "GraphQL"],
        raw_description: `Seeking a talented Full Stack Developer to craft intuitive, responsive web interfaces and modern microservices.
Key Duties:
- Develop scalable front-end client dashboards using React, modern CSS, and JavaScript.
- Build and maintain server-side APIs in Node.js or Python.
- Optimize database queries and schema designs.

Requirements:
- 2+ years of full stack software engineering experience.
- Deep expertise with JavaScript, modern UI frameworks (React or Vue), and SQL databases.`
    },
    "java_dev": {
        title: "Java Backend Developer",
        department: "Core Platform",
        experience_required: "3+ years",
        experience_years_min: 3.0,
        required_skills: ["Java", "Spring Boot", "MySQL", "JDBC", "Microservices", "Git"],
        nice_to_have_skills: ["Kafka", "Redis", "Docker", "AWS"],
        raw_description: `We are hiring a Java Backend Developer to build high-throughput transaction engines and distributed microservices.
Requirements:
- 3+ years hands-on experience in Java and Spring Boot framework.
- Strong knowledge of concurrency, collections, and JVM tuning.
- Solid experience with MySQL databases, indexing, and JDBC.
- Experience building RESTful web services and distributed systems.`
    }
};

function fillSampleJD(type) {
    const data = SAMPLE_JDS[type];
    if (!data) return;

    document.getElementById("jobTitle").value = data.title;
    document.getElementById("jobDepartment").value = data.department;
    document.getElementById("jobExperience").value = data.experience_required;
    document.getElementById("jobExpYears").value = data.experience_years_min;
    document.getElementById("jobSkills").value = data.required_skills.join(", ");
    document.getElementById("jobNiceSkills").value = data.nice_to_have_skills.join(", ");
    document.getElementById("jobDescription").value = data.raw_description;

    showToast(`Loaded sample template: ${data.title}`, "info");
}

async function loadJobs() {
    const container = document.getElementById("jobsListContainer");
    if (!container) return;

    try {
        const response = await fetch("/api/jobs");
        const jobs = await response.json();

        if (jobs.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="fas fa-briefcase fa-3x mb-3 text-secondary opacity-50"></i>
                    <h5>No Job Descriptions Posted Yet</h5>
                    <p>Create your first job opening above or load a sample template to get started.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = jobs.map(job => `
            <div class="custom-card mb-3 p-3">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <div class="d-flex align-items-center gap-2 mb-1">
                            <h5 class="fw-bold mb-0 text-dark">${escapeHtml(job.title)}</h5>
                            <span class="badge bg-light text-dark border">${escapeHtml(job.department || 'Engineering')}</span>
                            <span class="badge bg-primary-subtle text-primary border border-primary-subtle">
                                <i class="fas fa-clock me-1"></i>${escapeHtml(job.experience_required || 'Any exp')}
                            </span>
                        </div>
                        <small class="text-muted">Posted on ${new Date(job.created_at).toLocaleDateString()}</small>
                    </div>
                    <div class="d-flex gap-2">
                        <a href="/matching?job_id=${job.id}" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-balance-scale me-1"></i>Match Candidates
                        </a>
                        <button onclick="deleteJob(${job.id})" class="btn btn-sm btn-outline-danger" title="Delete Job">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>

                <div class="mt-3">
                    <div class="text-muted small fw-semibold mb-1">Required Skills:</div>
                    <div>
                        ${(job.required_skills || []).map(s => `<span class="skill-pill primary">${escapeHtml(s)}</span>`).join('')}
                    </div>
                </div>

                <div class="mt-2 text-muted small" style="white-space: pre-line; max-height: 80px; overflow: hidden; text-overflow: ellipsis;">
                    ${escapeHtml(job.raw_description.slice(0, 240))}...
                </div>
            </div>
        `).join('');

    } catch (err) {
        container.innerHTML = `<div class="alert alert-danger">Error loading jobs: ${err.message}</div>`;
    }
}

async function handleCreateJob(e) {
    e.preventDefault();

    const title = document.getElementById("jobTitle").value.trim();
    const department = document.getElementById("jobDepartment").value.trim();
    const experience_required = document.getElementById("jobExperience").value.trim();
    const experience_years_min = parseFloat(document.getElementById("jobExpYears").value || 0.0);
    const raw_description = document.getElementById("jobDescription").value.trim();

    const skillsInput = document.getElementById("jobSkills").value.trim();
    const required_skills = skillsInput ? skillsInput.split(",").map(s => s.trim()).filter(Boolean) : [];

    const niceSkillsInput = document.getElementById("jobNiceSkills").value.trim();
    const nice_to_have_skills = niceSkillsInput ? niceSkillsInput.split(",").map(s => s.trim()).filter(Boolean) : [];

    if (!raw_description) {
        showToast("Please provide job description content", "danger");
        return;
    }

    showLoading("Creating Job & Vectorizing in ChromaDB...");

    try {
        const response = await fetch("/api/jobs", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title,
                department,
                experience_required,
                experience_years_min,
                required_skills,
                nice_to_have_skills,
                raw_description
            })
        });

        const resData = await response.json();
        hideLoading();

        if (response.ok) {
            showToast(`Job "${resData.title}" created & indexed successfully!`, "success");
            document.getElementById("createJobForm").reset();
            loadJobs();
        } else {
            showToast(`Failed to create job: ${resData.error || 'Server error'}`, "danger");
        }
    } catch (err) {
        hideLoading();
        showToast(`Request error: ${err.message}`, "danger");
    }
}

async function deleteJob(jobId) {
    if (!confirm("Are you sure you want to delete this job description and its match history?")) return;

    try {
        const response = await fetch(`/api/jobs/${jobId}`, { method: "DELETE" });
        if (response.ok) {
            showToast("Job opening deleted", "success");
            loadJobs();
        } else {
            showToast("Failed to delete job", "danger");
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, "danger");
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, m => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[m]));
}

