// Main Utilities and Toast Notification Engine for HireMind AI

function showToast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    const toastId = "toast-" + Date.now();
    const bgClass = type === "success" ? "bg-success text-white" :
                    type === "danger" ? "bg-danger text-white" :
                    type === "warning" ? "bg-warning text-dark" : "bg-primary text-white";

    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center ${bgClass} border-0 show shadow-lg mb-2" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center gap-2">
                    <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'danger' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
                    <span>${message}</span>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    container.insertAdjacentHTML("beforeend", toastHtml);

    setTimeout(() => {
        const toastElem = document.getElementById(toastId);
        if (toastElem) {
            toastElem.classList.remove("show");
            setTimeout(() => toastElem.remove(), 300);
        }
    }, 4500);
}

function showLoading(text = "Processing with AI...") {
    let overlay = document.getElementById("spinner-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "spinner-overlay";
        overlay.className = "spinner-overlay";
        overlay.innerHTML = `
            <div class="spinner-border text-light mb-3" style="width: 3.5rem; height: 3.5rem;" role="status"></div>
            <h5 id="spinner-text" class="fw-semibold text-white tracking-wide">${text}</h5>
            <small class="text-light opacity-75">Powered by LangGraph & Groq</small>
        `;
        document.body.appendChild(overlay);
    } else {
        document.getElementById("spinner-text").innerText = text;
        overlay.style.display = "flex";
    }
}

function hideLoading() {
    const overlay = document.getElementById("spinner-overlay");
    if (overlay) {
        overlay.style.display = "none";
    }
}

// Highlight active sidebar navigation
document.addEventListener("DOMContentLoaded", () => {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll(".sidebar-nav .nav-link");
    navLinks.forEach(link => {
        if (link.getAttribute("href") === currentPath) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });
});

