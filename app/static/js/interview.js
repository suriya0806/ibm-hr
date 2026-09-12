// AI Interview Question Generator & Recruiter Studio Module

document.addEventListener("DOMContentLoaded", () => {
    initInterviewStudio();
});

let currentKit = null;

async function initInterviewStudio() {
    const jobSelect = document.getElementById("interviewJobSelect");
    const candSelect = document.getElementById("interviewCandSelect");
    if (!jobSelect || !candSelect) return;

    try {
        const [jobsRes, candsRes] = await Promise.all([
            fetch("/api/jobs"),
            fetch("/api/resumes/candidates")
        ]);

        const jobs = await jobsRes.json();
        const cands = await candsRes.json();

        jobSelect.innerHTML = `<option value="">Select Job Opening...</option>` +
            jobs.map(j => `<option value="${j.id}">${escapeHtml(j.title)}</option>`).join('');

        candSelect.innerHTML = `<option value="">Select Candidate...</option>` +
            cands.map(c => `<option value="${c.id}">${escapeHtml(c.name)} (${c.total_experience_years || 0} yrs exp)</option>`).join('');

        // Handle URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const qJobId = urlParams.get("job_id");
        const qCandId = urlParams.get("candidate_id");

        if (qJobId) jobSelect.value = qJobId;
        if (qCandId) candSelect.value = qCandId;

        if (qJobId && qCandId) {
            checkExistingKit(qJobId, qCandId);
        }

        const genBtn = document.getElementById("generateKitBtn");
        if (genBtn) {
            genBtn.addEventListener("click", () => generateKit());
        }

        const copyBtn = document.getElementById("copyMarkdownBtn");
        if (copyBtn) {
            copyBtn.addEventListener("click", copyKitAsMarkdown);
        }

        const printBtn = document.getElementById("printKitBtn");
        if (printBtn) {
            printBtn.addEventListener("click", () => window.print());
        }

    } catch (err) {
        showToast(`Initialization error: ${err.message}`, "danger");
    }
}

async function checkExistingKit(jobId, candId) {
    try {
        const res = await fetch(`/api/interview/${jobId}/${candId}`);
        if (res.ok) {
            const kit = await res.json();
            currentKit = kit;
            renderInterviewKit(kit);
        }
    } catch (err) {
        // Kit doesn't exist yet, wait for user to click generate
    }
}

async function generateKit(forceRegenerate = false) {
    const jobSelect = document.getElementById("interviewJobSelect");
    const candSelect = document.getElementById("interviewCandSelect");

    const jobId = jobSelect.value;
    const candidateId = candSelect.value;

    if (!jobId || !candidateId) {
        showToast("Please select both a Job Opening and a Candidate", "warning");
        return;
    }

    showLoading("Synthesizing Tailored Interview Questions with LangGraph & Groq...");

    try {
        const response = await fetch("/api/interview/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                job_id: parseInt(jobId),
                candidate_id: parseInt(candidateId)
            })
        });

        const data = await response.json();
        hideLoading();

        if (response.ok) {
            showToast("Interview Kit generated successfully!", "success");
            currentKit = data.kit;
            renderInterviewKit(data.kit);
        } else {
            showToast(`Generation failed: ${data.error || 'Server error'}`, "danger");
        }
    } catch (err) {
        hideLoading();
        showToast(`Request failed: ${err.message}`, "danger");
    }
}

function renderInterviewKit(kit) {
    const container = document.getElementById("interviewKitContainer");
    const actionsBar = document.getElementById("kitActionsBar");
    if (!container) return;

    if (actionsBar) actionsBar.style.display = "flex";

    const techQuestions = kit.technical_questions || [];
    const resumeQuestions = kit.resume_questions || [];
    const gapQuestions = kit.gap_questions || [];
    const behavioralQuestions = kit.behavioral_questions || [];
    const rubrics = kit.rubrics || {};

    container.innerHTML = `
        <div class="custom-card p-4 mb-4">
            <div class="d-flex justify-content-between align-items-center border-bottom pb-3 mb-4">
                <div>
                    <h4 class="fw-bold mb-1 text-dark">${escapeHtml(kit.candidate_name)}</h4>
                    <span class="text-muted">Target Role: <strong class="text-primary">${escapeHtml(kit.job_title)}</strong></span>
                </div>
                <div class="text-end">
                    <span class="badge bg-success-subtle text-success border border-success-subtle px-3 py-2">
                        <i class="fas fa-check-circle me-1"></i>AI Interview Kit Ready
                    </span>
                </div>
            </div>

            <!-- Tabs Navigation -->
            <ul class="nav nav-pills mb-4" id="interviewTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="tech-tab" data-bs-toggle="pill" data-bs-target="#tech-pane" type="button" role="tab">
                        <i class="fas fa-code me-2"></i>Technical (${techQuestions.length})
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="resume-tab" data-bs-toggle="pill" data-bs-target="#resume-pane" type="button" role="tab">
                        <i class="fas fa-file-alt me-2"></i>Resume Claims (${resumeQuestions.length})
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="gap-tab" data-bs-toggle="pill" data-bs-target="#gap-pane" type="button" role="tab">
                        <i class="fas fa-shield-alt me-2"></i>Skill Gaps (${gapQuestions.length})
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="beh-tab" data-bs-toggle="pill" data-bs-target="#beh-pane" type="button" role="tab">
                        <i class="fas fa-users me-2"></i>Behavioral (${behavioralQuestions.length})
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="rubric-tab" data-bs-toggle="pill" data-bs-target="#rubric-pane" type="button" role="tab">
                        <i class="fas fa-clipboard-check me-2"></i>Scoring Rubrics
                    </button>
                </li>
            </ul>

            <!-- Tab Panes -->
            <div class="tab-content" id="interviewTabsContent">
                <!-- 1. Technical Pane -->
                <div class="tab-pane fade show active" id="tech-pane" role="tabpanel">
                    <div class="alert alert-info py-2 px-3 small mb-3">
                        <i class="fas fa-info-circle me-1"></i>Evaluates candidate's conceptual and practical mastery of core JD technologies.
                    </div>
                    ${techQuestions.map((q, i) => `
                        <div class="question-card">
                            <div class="d-flex justify-content-between">
                                <span class="badge bg-primary mb-2">${escapeHtml(q.topic || 'Technical')}</span>
                                <span class="text-muted small">Q${i + 1}</span>
                            </div>
                            <div class="question-title">${i + 1}. ${escapeHtml(q.question)}</div>
                            <div class="question-guidance">
                                <div class="text-success mb-1">
                                    <strong><i class="fas fa-check me-1"></i>What a Strong Answer Looks Like:</strong>
                                    <div class="text-muted mt-1">${escapeHtml(q.expected_answer || '')}</div>
                                </div>
                                ${q.red_flags ? `
                                    <div class="text-danger mt-2">
                                        <strong><i class="fas fa-flag me-1"></i>Red Flags to Watch For:</strong>
                                        <div class="text-muted mt-1">${escapeHtml(q.red_flags)}</div>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>

                <!-- 2. Resume Pane -->
                <div class="tab-pane fade" id="resume-pane" role="tabpanel">
                    <div class="alert alert-primary py-2 px-3 small mb-3">
                        <i class="fas fa-info-circle me-1"></i>Specifically validates projects, contributions, and architectural claims made on the candidate's resume.
                    </div>
                    ${resumeQuestions.map((q, i) => `
                        <div class="question-card resume-card">
                            <div class="d-flex justify-content-between">
                                <span class="badge bg-info text-dark mb-2">Claim: ${escapeHtml(q.reference_claim || 'Project Claim')}</span>
                                <span class="text-muted small">Q${i + 1}</span>
                            </div>
                            <div class="question-title">${i + 1}. ${escapeHtml(q.question)}</div>
                            <div class="question-guidance">
                                <div class="text-success mb-1">
                                    <strong><i class="fas fa-check me-1"></i>Key Verification Points:</strong>
                                    <div class="text-muted mt-1">${escapeHtml(q.expected_answer || '')}</div>
                                </div>
                                ${q.red_flags ? `
                                    <div class="text-danger mt-2">
                                        <strong><i class="fas fa-flag me-1"></i>Red Flags:</strong>
                                        <div class="text-muted mt-1">${escapeHtml(q.red_flags)}</div>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>

                <!-- 3. Skill Gap Pane -->
                <div class="tab-pane fade" id="gap-pane" role="tabpanel">
                    <div class="alert alert-warning py-2 px-3 small mb-3">
                        <i class="fas fa-info-circle me-1"></i>Evaluates how candidate handles tools or requirements flagged as missing or weak during screening.
                    </div>
                    ${gapQuestions.map((q, i) => `
                        <div class="question-card gap-card">
                            <div class="d-flex justify-content-between">
                                <span class="badge bg-warning text-dark mb-2">Skill Gap: ${escapeHtml(q.skill_gap || 'Unverified Area')}</span>
                                <span class="text-muted small">Q${i + 1}</span>
                            </div>
                            <div class="question-title">${i + 1}. ${escapeHtml(q.question)}</div>
                            <div class="question-guidance">
                                <div class="text-success mb-1">
                                    <strong><i class="fas fa-check me-1"></i>Desired Response:</strong>
                                    <div class="text-muted mt-1">${escapeHtml(q.expected_answer || '')}</div>
                                </div>
                                ${q.red_flags ? `
                                    <div class="text-danger mt-2">
                                        <strong><i class="fas fa-flag me-1"></i>Red Flags:</strong>
                                        <div class="text-muted mt-1">${escapeHtml(q.red_flags)}</div>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>

                <!-- 4. Behavioral Pane -->
                <div class="tab-pane fade" id="beh-pane" role="tabpanel">
                    <div class="alert alert-success py-2 px-3 small mb-3">
                        <i class="fas fa-info-circle me-1"></i>STAR-format questions evaluating engineering collaboration, problem resolution, and communication.
                    </div>
                    ${behavioralQuestions.map((q, i) => `
                        <div class="question-card behavioral-card">
                            <div class="d-flex justify-content-between">
                                <span class="badge bg-success mb-2">${escapeHtml(q.situation_type || 'Behavioral')}</span>
                                <span class="text-muted small">Q${i + 1}</span>
                            </div>
                            <div class="question-title">${i + 1}. ${escapeHtml(q.question)}</div>
                            <div class="question-guidance">
                                <div>
                                    <strong class="text-primary"><i class="fas fa-star me-1"></i>STAR Evaluation Guidelines:</strong>
                                    <div class="text-muted mt-1">${escapeHtml(q.star_guidelines || '')}</div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>

                <!-- 5. Rubrics Pane -->
                <div class="tab-pane fade" id="rubric-pane" role="tabpanel">
                    <div class="row g-3">
                        <div class="col-md-7">
                            <h6 class="fw-bold text-dark mb-3">Standard 5-Point Scoring Scale</h6>
                            <div class="list-group">
                                ${rubrics.scoring_scale ? Object.entries(rubrics.scoring_scale).map(([score, desc]) => `
                                    <div class="list-group-item d-flex align-items-start gap-3 py-2">
                                        <span class="badge ${score >= '4' ? 'bg-success' : score === '3' ? 'bg-primary' : 'bg-secondary'} fs-6">${score}.0</span>
                                        <span class="small text-muted">${escapeHtml(desc)}</span>
                                    </div>
                                `).join('') : '<small class="text-muted">Standard 1-5 scale</small>'}
                            </div>
                        </div>
                        <div class="col-md-5">
                            <div class="p-3 bg-light rounded border h-100">
                                <h6 class="fw-bold text-dark mb-2"><i class="fas fa-weight-hanging text-primary me-2"></i>Weighting Breakdown</h6>
                                <ul class="list-unstyled small text-muted mb-3">
                                    ${(rubrics.evaluation_criteria || []).map(crit => `
                                        <li class="py-1"><i class="fas fa-check text-primary me-2"></i>${escapeHtml(crit)}</li>
                                    `).join('')}
                                </ul>
                                <div class="alert alert-primary p-2 small mb-0">
                                    <strong>Recommendation Threshold:</strong> ${escapeHtml(rubrics.hiring_recommendation_guidelines || 'Score 4.0+ to recommend for offer.')}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function copyKitAsMarkdown() {
    if (!currentKit) return;

    let md = `# Interview Kit: ${currentKit.candidate_name}\n`;
    md += `**Target Role:** ${currentKit.job_title}\n\n`;

    md += `## 1. Technical Questions\n`;
    (currentKit.technical_questions || []).forEach((q, i) => {
        md += `### Q${i+1}: ${q.question} (${q.topic || ''})\n`;
        md += `- **Expected Answer:** ${q.expected_answer || ''}\n`;
        if (q.red_flags) md += `- **Red Flags:** ${q.red_flags}\n`;
        md += `\n`;
    });

    md += `## 2. Resume-Based Questions\n`;
    (currentKit.resume_questions || []).forEach((q, i) => {
        md += `### Q${i+1}: ${q.question}\n`;
        md += `- **Referenced Claim:** ${q.reference_claim || ''}\n`;
        md += `- **Expected Answer:** ${q.expected_answer || ''}\n`;
        md += `\n`;
    });

    md += `## 3. Skill Gap / Probe Questions\n`;
    (currentKit.gap_questions || []).forEach((q, i) => {
        md += `### Q${i+1}: ${q.question}\n`;
        md += `- **Target Gap:** ${q.skill_gap || ''}\n`;
        md += `- **Expected Answer:** ${q.expected_answer || ''}\n`;
        md += `\n`;
    });

    md += `## 4. Behavioral Questions (STAR)\n`;
    (currentKit.behavioral_questions || []).forEach((q, i) => {
        md += `### Q${i+1}: ${q.question}\n`;
        md += `- **Focus:** ${q.situation_type || ''}\n`;
        md += `- **STAR Guidelines:** ${q.star_guidelines || ''}\n`;
        md += `\n`;
    });

    navigator.clipboard.writeText(md).then(() => {
        showToast("Interview Kit copied to clipboard as Markdown!", "success");
    }).catch(err => {
        showToast(`Failed to copy: ${err.message}`, "danger");
    });
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, m => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[m]));
}

