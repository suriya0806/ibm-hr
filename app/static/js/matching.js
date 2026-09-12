// Candidate ↔ Job Matching & Ranking Leaderboard Module

document.addEventListener("DOMContentLoaded", () => {
    initMatchingPage();
});

let currentJobId = null;
let currentMatches = [];

async function initMatchingPage() {
    const selector = document.getElementById("matchingJobSelect");
    if (!selector) return;

    try {
        const response = await fetch("/api/jobs");
        const jobs = await response.json();

        if (jobs.length === 0) {
            selector.innerHTML = `<option value="">No job openings created yet</option>`;
            document.getElementById("matchingResultsContainer").innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="fas fa-briefcase fa-3x mb-3 text-secondary opacity-50"></i>
                    <h5>No Job Descriptions Found</h5>
                    <p>Please create a job opening first to evaluate candidates.</p>
                    <a href="/jobs" class="btn btn-primary">Create Job Opening</a>
                </div>
            `;
            return;
        }

        selector.innerHTML = `<option value="">Select a Job Opening...</option>` +
            jobs.map(j => `<option value="${j.id}">${escapeHtml(j.title)} (${j.department || 'Engineering'})</option>`).join('');

        // Check if job_id is passed in query parameter
        const urlParams = new URLSearchParams(window.location.search);
        const qJobId = urlParams.get("job_id");
        if (qJobId) {
            selector.value = qJobId;
            currentJobId = qJobId;
            loadJobMatches(qJobId);
        }

        selector.addEventListener("change", (e) => {
            currentJobId = e.target.value;
            if (currentJobId) {
                loadJobMatches(currentJobId);
            } else {
                document.getElementById("matchingResultsContainer").innerHTML = `
                    <div class="text-center py-5 text-muted">
                        <i class="fas fa-search fa-3x mb-3 text-secondary opacity-50"></i>
                        <h5>Select a Job Opening to View Candidate Rankings</h5>
                    </div>
                `;
            }
        });

        const runBtn = document.getElementById("runMatchingBtn");
        if (runBtn) {
            runBtn.addEventListener("click", runCandidateMatching);
        }

    } catch (err) {
        showToast(`Failed to load jobs: ${err.message}`, "danger");
    }
}

async function loadJobMatches(jobId) {
    const container = document.getElementById("matchingResultsContainer");
    if (!container) return;

    try {
        const response = await fetch(`/api/match/job/${jobId}`);
        const matches = await response.json();
        currentMatches = matches;

        if (matches.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="fas fa-robot fa-3x mb-3 text-primary opacity-50"></i>
                    <h5>No Matches Computed for this Job Yet</h5>
                    <p>Click "Run AI Matching & Ranking" to evaluate all screened candidates with LangGraph.</p>
                    <button onclick="runCandidateMatching()" class="btn btn-primary">
                        <i class="fas fa-bolt me-1"></i>Run AI Matching
                    </button>
                </div>
            `;
            return;
        }

        renderLeaderboard(matches);

    } catch (err) {
        container.innerHTML = `<div class="alert alert-danger">Error loading match results: ${err.message}</div>`;
    }
}

async function runCandidateMatching() {
    if (!currentJobId) {
        showToast("Please select a job opening first", "warning");
        return;
    }

    showLoading("Running LangGraph Semantic Similarity, Skill Overlap & Explainable Ranking Engine...");

    try {
        const response = await fetch("/api/match/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_id: parseInt(currentJobId) })
        });

        const data = await response.json();
        hideLoading();

        if (response.ok) {
            showToast(data.message, "success");
            currentMatches = data.results || [];
            renderLeaderboard(currentMatches);
        } else {
            showToast(`Matching failed: ${data.error || 'Server error'}`, "danger");
        }
    } catch (err) {
        hideLoading();
        showToast(`Request failed: ${err.message}`, "danger");
    }
}

function renderLeaderboard(matches) {
    const container = document.getElementById("matchingResultsContainer");
    if (!container) return;

    if (matches.length === 0) {
        container.innerHTML = `<div class="text-center py-4 text-muted">No candidates to rank. Please upload resumes first.</div>`;
        return;
    }

    container.innerHTML = `
        <div class="table-responsive custom-card">
            <table class="table table-hover align-middle mb-0">
                <thead class="table-light">
                    <tr>
                        <th class="ps-4" style="width: 70px;">Rank</th>
                        <th>Candidate</th>
                        <th>Overall Fit</th>
                        <th>Skills Match</th>
                        <th>Experience</th>
                        <th>Recommendation</th>
                        <th class="text-end pe-4">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${matches.map((m, index) => {
                        const rankClass = index === 0 ? 'badge bg-warning text-dark' :
                                          index === 1 ? 'badge bg-secondary' :
                                          index === 2 ? 'badge bg-dark-subtle text-dark' : 'badge bg-light text-muted border';

                        const recClass = m.recommendation === "Strongly Recommended" ? "strongly-rec" :
                                         m.recommendation === "Recommended" ? "rec" :
                                         m.recommendation === "Review" ? "review" : "not-rec";

                        const barClass = m.overall_score >= 85 ? "high" :
                                         m.overall_score >= 70 ? "med" :
                                         m.overall_score >= 50 ? "low" : "danger";

                        return `
                            <tr>
                                <td class="ps-4">
                                    <span class="${rankClass} fw-bold" style="font-size: 0.9rem;">#${index + 1}</span>
                                </td>
                                <td>
                                    <div class="fw-bold text-dark">${escapeHtml(m.candidate_name)}</div>
                                    <small class="text-muted">${escapeHtml(m.candidate_email || '')} • ${m.candidate_experience || 0} yrs exp</small>
                                </td>
                                <td style="min-width: 150px;">
                                    <div class="d-flex justify-content-between align-items-center mb-1">
                                        <span class="fw-bold fs-6 text-dark">${m.overall_score}%</span>
                                        <small class="text-muted">Semantic: ${m.semantic_score}%</small>
                                    </div>
                                    <div class="score-progress">
                                        <div class="score-progress-bar ${barClass}" style="width: ${m.overall_score}%;"></div>
                                    </div>
                                </td>
                                <td>
                                    <span class="fw-semibold">${m.skills_score}%</span>
                                    <div class="small text-muted">${(m.matched_skills || []).length} matched</div>
                                </td>
                                <td>
                                    <span class="fw-semibold">${m.experience_score}%</span>
                                </td>
                                <td>
                                    <span class="rec-badge ${recClass}">
                                        <i class="fas ${m.recommendation === 'Strongly Recommended' ? 'fa-star' : m.recommendation === 'Recommended' ? 'fa-check' : m.recommendation === 'Review' ? 'fa-eye' : 'fa-times'}"></i>
                                        ${escapeHtml(m.recommendation)}
                                    </span>
                                </td>
                                <td class="text-end pe-4">
                                    <div class="d-flex gap-2 justify-content-end">
                                        <button onclick="viewDeepDive(${m.id})" class="btn btn-sm btn-outline-primary" title="Explainable AI Deep Dive">
                                            <i class="fas fa-chart-pie me-1"></i>Deep Dive
                                        </button>
                                        <a href="/interview?job_id=${m.job_id}&candidate_id=${m.candidate_id}" class="btn btn-sm btn-primary" title="Generate Interview Kit">
                                            <i class="fas fa-question-circle me-1"></i>Interview Kit
                                        </a>
                                    </div>
                                </td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function viewDeepDive(matchId) {
    const match = currentMatches.find(m => m.id === matchId);
    if (!match) return;

    const modalTitle = document.getElementById("deepDiveModalTitle");
    const modalBody = document.getElementById("deepDiveModalBody");
    if (!modalBody) return;

    modalTitle.innerText = `${match.candidate_name} vs ${match.job_title} — Explainable AI Analysis`;

    const recClass = match.recommendation === "Strongly Recommended" ? "strongly-rec" :
                     match.recommendation === "Recommended" ? "rec" :
                     match.recommendation === "Review" ? "review" : "not-rec";

    modalBody.innerHTML = `
        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="p-3 bg-light rounded text-center border">
                    <div class="small text-muted fw-semibold">Overall Match</div>
                    <div class="display-6 fw-bold text-primary">${match.overall_score}%</div>
                    <span class="rec-badge ${recClass} mt-1">${match.recommendation}</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="p-3 bg-light rounded text-center border">
                    <div class="small text-muted fw-semibold">Skills Match</div>
                    <div class="display-6 fw-bold text-success">${match.skills_score}%</div>
                    <small class="text-muted">${(match.matched_skills || []).length} Matched</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="p-3 bg-light rounded text-center border">
                    <div class="small text-muted fw-semibold">Semantic Cosine</div>
                    <div class="display-6 fw-bold text-info">${match.semantic_score}%</div>
                    <small class="text-muted">ChromaDB Embedding</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="p-3 bg-light rounded text-center border">
                    <div class="small text-muted fw-semibold">Experience Score</div>
                    <div class="display-6 fw-bold text-warning">${match.experience_score}%</div>
                    <small class="text-muted">${match.candidate_experience || 0} Years</small>
                </div>
            </div>
        </div>

        <div class="mb-4 p-3 bg-light rounded border">
            <h6 class="fw-bold text-dark mb-1"><i class="fas fa-brain text-primary me-2"></i>Recruiter Decision Rationale</h6>
            <p class="mb-0 text-muted" style="line-height: 1.6;">${escapeHtml(match.rationale || 'Detailed assessment available.')}</p>
        </div>

        <div class="row g-3 mb-3">
            <div class="col-md-6">
                <div class="p-3 border rounded h-100">
                    <h6 class="fw-bold text-success mb-2"><i class="fas fa-check-circle me-2"></i>Matched Competencies</h6>
                    <div>
                        ${(match.matched_skills && match.matched_skills.length > 0) ?
                            match.matched_skills.map(s => `<span class="skill-pill success"><i class="fas fa-check me-1"></i>${escapeHtml(s)}</span>`).join('') :
                            '<small class="text-muted">No direct skill matches detected.</small>'}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="p-3 border rounded h-100">
                    <h6 class="fw-bold text-danger mb-2"><i class="fas fa-exclamation-triangle me-2"></i>Missing Critical Skills</h6>
                    <div>
                        ${(match.missing_skills && match.missing_skills.length > 0) ?
                            match.missing_skills.map(s => `<span class="skill-pill danger"><i class="fas fa-times me-1"></i>${escapeHtml(s)}</span>`).join('') :
                            '<small class="text-success"><i class="fas fa-check-circle me-1"></i>All critical required skills fulfilled!</small>'}
                    </div>
                </div>
            </div>
        </div>

        <div class="row g-3">
            <div class="col-md-6">
                <h6 class="fw-bold text-dark mb-2"><i class="fas fa-thumbs-up text-primary me-2"></i>Key Strengths</h6>
                <ul class="list-group list-group-flush small">
                    ${(match.key_strengths || []).map(str => `<li class="list-group-item bg-transparent px-0 py-1 text-muted"><i class="fas fa-plus text-success me-2"></i>${escapeHtml(str)}</li>`).join('')}
                </ul>
            </div>
            <div class="col-md-6">
                <h6 class="fw-bold text-dark mb-2"><i class="fas fa-binoculars text-warning me-2"></i>Interview Probe Areas</h6>
                <ul class="list-group list-group-flush small">
                    ${(match.key_concerns || []).map(c => `<li class="list-group-item bg-transparent px-0 py-1 text-muted"><i class="fas fa-arrow-right text-warning me-2"></i>${escapeHtml(c)}</li>`).join('')}
                </ul>
            </div>
        </div>

        <div class="mt-4 pt-3 border-top text-end">
            <a href="/interview?job_id=${match.job_id}&candidate_id=${match.candidate_id}" class="btn btn-primary">
                <i class="fas fa-bolt me-1"></i>Generate Tailored Interview Questions
            </a>
        </div>
    `;

    const modal = new bootstrap.Modal(document.getElementById("deepDiveModal"));
    modal.show();
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, m => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[m]));
}

