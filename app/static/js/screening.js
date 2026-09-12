// Resume Screening and Batch Ingestion Module for HireMind AI

document.addEventListener("DOMContentLoaded", () => {
    initDropzone();
    loadCandidates();
});

let selectedFiles = [];

function initDropzone() {
    const dropzone = document.getElementById("resumeDropzone");
    const fileInput = document.getElementById("resumeFileInput");
    if (!dropzone || !fileInput) return;

    dropzone.addEventListener("click", () => fileInput.click());

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFilesSelection(e.dataTransfer.files);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFilesSelection(e.target.files);
        }
    });

    const uploadBtn = document.getElementById("uploadResumesBtn");
    if (uploadBtn) {
        uploadBtn.addEventListener("click", uploadSelectedResumes);
    }
}

function handleFilesSelection(files) {
    selectedFiles = Array.from(files);
    updateSelectedFilesList();
}

function updateSelectedFilesList() {
    const listContainer = document.getElementById("selectedFilesList");
    const uploadBtn = document.getElementById("uploadResumesBtn");
    if (!listContainer) return;

    if (selectedFiles.length === 0) {
        listContainer.innerHTML = '';
        if (uploadBtn) uploadBtn.disabled = true;
        return;
    }

    if (uploadBtn) uploadBtn.disabled = false;

    listContainer.innerHTML = `
        <div class="mt-3 p-3 bg-light rounded border">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="fw-semibold text-dark">${selectedFiles.length} file(s) queued for AI Screening:</span>
                <button onclick="clearSelectedFiles()" class="btn btn-sm btn-link text-danger p-0 text-decoration-none">Clear all</button>
            </div>
            <ul class="list-group list-group-flush">
                ${selectedFiles.map((file, idx) => `
                    <li class="list-group-item bg-transparent d-flex justify-content-between align-items-center py-2 px-0">
                        <div>
                            <i class="fas ${file.name.endsWith('.pdf') ? 'fa-file-pdf text-danger' : 'fa-file-word text-primary'} me-2"></i>
                            <span class="fw-medium">${escapeHtml(file.name)}</span>
                            <small class="text-muted ms-2">(${(file.size / 1024).toFixed(1)} KB)</small>
                        </div>
                        <button onclick="removeSelectedFile(${idx})" class="btn btn-sm btn-link text-muted p-0">
                            <i class="fas fa-times"></i>
                        </button>
                    </li>
                `).join('')}
            </ul>
        </div>
    `;
}

function removeSelectedFile(index) {
    selectedFiles.splice(index, 1);
    updateSelectedFilesList();
}

function clearSelectedFiles() {
    selectedFiles = [];
    const fileInput = document.getElementById("resumeFileInput");
    if (fileInput) fileInput.value = "";
    updateSelectedFilesList();
}

async function uploadSelectedResumes() {
    if (selectedFiles.length === 0) return;

    const formData = new FormData();
    selectedFiles.forEach(file => formData.append("files", file));

    showLoading(`Executing LangGraph Screening Pipeline on ${selectedFiles.length} resume(s)...`);

    try {
        const response = await fetch("/api/resumes/upload", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        hideLoading();

        if (response.ok) {
            showToast(data.message, "success");
            clearSelectedFiles();
            loadCandidates();
        } else {
            showToast(`Upload failed: ${data.error || 'Unknown error'}`, "danger");
        }
    } catch (err) {
        hideLoading();
        showToast(`Upload failed: ${err.message}`, "danger");
    }
}

async function loadCandidates() {
    const container = document.getElementById("candidatesListContainer");
    if (!container) return;

    try {
        const response = await fetch("/api/resumes/candidates");
        const candidates = await response.json();

        if (candidates.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="fas fa-user-graduate fa-3x mb-3 text-secondary opacity-50"></i>
                    <h5>No Candidates Screened Yet</h5>
                    <p>Upload candidate resumes in PDF or DOCX format above to begin screening.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = candidates.map(c => {
            const resume = c.resume || {};
            const skills = resume.skills || {};
            let allSkills = [];
            if (typeof skills === "object" && !Array.isArray(skills)) {
                Object.values(skills).forEach(arr => {
                    if (Array.isArray(arr)) allSkills.push(...arr);
                });
            } else if (Array.isArray(skills)) {
                allSkills = skills;
            }

            return `
                <div class="custom-card mb-3 p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <div class="d-flex align-items-center gap-2 mb-1">
                                <h5 class="fw-bold mb-0 text-dark">${escapeHtml(c.name)}</h5>
                                <span class="badge bg-secondary-subtle text-secondary border">
                                    <i class="fas fa-briefcase me-1"></i>${c.total_experience_years || 0} yrs exp
                                </span>
                                ${c.location ? `<span class="badge bg-light text-dark border"><i class="fas fa-map-marker-alt me-1"></i>${escapeHtml(c.location)}</span>` : ''}
                            </div>
                            <div class="small text-muted d-flex gap-3 mt-1">
                                ${c.email ? `<span><i class="fas fa-envelope me-1"></i>${escapeHtml(c.email)}</span>` : ''}
                                ${c.phone ? `<span><i class="fas fa-phone me-1"></i>${escapeHtml(c.phone)}</span>` : ''}
                                ${c.github ? `<span><a href="${escapeHtml(c.github)}" target="_blank" class="text-muted text-decoration-none"><i class="fab fa-github me-1"></i>GitHub</a></span>` : ''}
                                ${c.linkedin ? `<span><a href="${escapeHtml(c.linkedin)}" target="_blank" class="text-muted text-decoration-none"><i class="fab fa-linkedin me-1"></i>LinkedIn</a></span>` : ''}
                            </div>
                        </div>
                        <div class="d-flex gap-2">
                            <button onclick="viewCandidateProfile(${c.id})" class="btn btn-sm btn-primary">
                                <i class="fas fa-eye me-1"></i>View Profile
                            </button>
                            <button onclick="deleteCandidate(${c.id})" class="btn btn-sm btn-outline-danger" title="Delete Candidate">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>

                    ${c.summary ? `
                        <div class="mt-2 text-dark small" style="background: #f8fafc; padding: 0.6rem 0.85rem; border-radius: 6px;">
                            <strong>AI Summary:</strong> ${escapeHtml(c.summary)}
                        </div>
                    ` : ''}

                    <div class="mt-2">
                        <div class="text-muted small fw-semibold mb-1">Extracted Core Skills:</div>
                        <div>
                            ${allSkills.slice(0, 10).map(s => `<span class="skill-pill primary">${escapeHtml(s)}</span>`).join('')}
                            ${allSkills.length > 10 ? `<span class="badge bg-light text-muted border">+${allSkills.length - 10} more</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (err) {
        container.innerHTML = `<div class="alert alert-danger">Error loading candidates: ${err.message}</div>`;
    }
}

async function viewCandidateProfile(candidateId) {
    try {
        const response = await fetch(`/api/resumes/candidates/${candidateId}`);
        const c = await response.json();
        const resume = c.resume || {};

        const modalBody = document.getElementById("candidateProfileModalBody");
        const modalTitle = document.getElementById("candidateProfileModalTitle");

        if (!modalBody) return;

        modalTitle.innerText = `${c.name} — Candidate Profile`;

        const skills = resume.skills || {};
        let techSkills = Array.isArray(skills.technical) ? skills.technical : [];
        let frameworks = Array.isArray(skills.frameworks) ? skills.frameworks : [];
        let tools = Array.isArray(skills.tools) ? skills.tools : [];
        let soft = Array.isArray(skills.soft) ? skills.soft : [];

        const education = resume.education || [];
        const experience = resume.experience || [];
        const projects = resume.projects || [];
        const certifications = resume.certifications || [];

        modalBody.innerHTML = `
            <div class="mb-3 p-3 bg-light rounded border">
                <h6 class="fw-bold text-dark mb-1">Executive Summary</h6>
                <p class="mb-0 text-muted small">${escapeHtml(c.summary || 'No summary available.')}</p>
            </div>

            <div class="row g-3 mb-3">
                <div class="col-md-6">
                    <h6 class="fw-bold text-dark mb-2"><i class="fas fa-tools text-primary me-2"></i>Technical Skills</h6>
                    <div>
                        ${techSkills.map(s => `<span class="skill-pill primary">${escapeHtml(s)}</span>`).join('')}
                        ${frameworks.map(s => `<span class="skill-pill neutral">${escapeHtml(s)}</span>`).join('')}
                        ${tools.map(s => `<span class="skill-pill neutral">${escapeHtml(s)}</span>`).join('')}
                    </div>
                </div>
                <div class="col-md-6">
                    <h6 class="fw-bold text-dark mb-2"><i class="fas fa-graduation-cap text-success me-2"></i>Education</h6>
                    ${education.length > 0 ? education.map(e => `
                        <div class="small text-muted mb-1">
                            <strong class="text-dark">${escapeHtml(e.degree || 'Degree')}</strong> - ${escapeHtml(e.institution || 'Institution')} (${escapeHtml(e.year || '')})
                        </div>
                    `).join('') : '<small class="text-muted">Not specified</small>'}
                </div>
            </div>

            <div class="mb-3">
                <h6 class="fw-bold text-dark mb-2"><i class="fas fa-briefcase text-secondary me-2"></i>Work Experience (${c.total_experience_years || 0} years)</h6>
                ${experience.length > 0 ? experience.map(exp => `
                    <div class="p-2 border-bottom small">
                        <div class="d-flex justify-content-between">
                            <strong class="text-dark">${escapeHtml(exp.role || 'Role')}</strong>
                            <span class="text-muted">${escapeHtml(exp.duration || '')}</span>
                        </div>
                        <div class="text-primary fw-medium">${escapeHtml(exp.company || '')}</div>
                        <div class="text-muted mt-1">${escapeHtml(exp.description || '')}</div>
                    </div>
                `).join('') : '<small class="text-muted">No explicit experience entries found.</small>'}
            </div>

            <div class="mb-3">
                <h6 class="fw-bold text-dark mb-2"><i class="fas fa-project-diagram text-warning me-2"></i>Highlighted Projects</h6>
                ${projects.length > 0 ? projects.map(p => `
                    <div class="p-2 border-bottom small">
                        <strong class="text-dark">${escapeHtml(p.title || 'Project')}</strong>
                        ${Array.isArray(p.tech_stack) ? p.tech_stack.map(t => `<span class="skill-pill neutral ms-1">${escapeHtml(t)}</span>`).join('') : ''}
                        <div class="text-muted mt-1">${escapeHtml(p.description || '')}</div>
                    </div>
                `).join('') : '<small class="text-muted">No project details extracted.</small>'}
            </div>

            ${certifications.length > 0 ? `
                <div>
                    <h6 class="fw-bold text-dark mb-2"><i class="fas fa-award text-info me-2"></i>Certifications</h6>
                    <ul class="list-unstyled small text-muted mb-0">
                        ${certifications.map(cert => `<li><i class="fas fa-check text-success me-2"></i>${escapeHtml(cert)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        `;

        const modal = new bootstrap.Modal(document.getElementById("candidateProfileModal"));
        modal.show();

    } catch (err) {
        showToast(`Failed to load profile: ${err.message}`, "danger");
    }
}

async function deleteCandidate(candidateId) {
    if (!confirm("Are you sure you want to delete this candidate?")) return;

    try {
        const response = await fetch(`/api/resumes/candidates/${candidateId}`, { method: "DELETE" });
        if (response.ok) {
            showToast("Candidate deleted", "success");
            loadCandidates();
        } else {
            showToast("Failed to delete candidate", "danger");
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

