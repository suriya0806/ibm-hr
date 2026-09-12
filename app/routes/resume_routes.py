import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.models import db
from app.models.candidate import Candidate, ResumeData
from app.graphs.screening_graph import build_screening_graph

resume_bp = Blueprint("resume_api", __name__)

screening_graph = None

def get_screening_graph():
    global screening_graph
    if screening_graph is None:
        screening_graph = build_screening_graph()
    return screening_graph

@resume_bp.route("/candidates", methods=["GET"])
def get_candidates():
    candidates = Candidate.query.order_by(Candidate.created_at.desc()).all()
    return jsonify([c.to_dict() for c in candidates])

@resume_bp.route("/candidates/<int:candidate_id>", methods=["GET"])
def get_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    return jsonify(candidate.to_dict())

@resume_bp.route("/upload", methods=["POST"])
def upload_resumes():
    if "files" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    uploaded_files = request.files.getlist("files")
    if not uploaded_files or uploaded_files[0].filename == "":
        return jsonify({"error": "No selected files"}), 400

    graph = get_screening_graph()
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    results = []
    errors = []

    for file in uploaded_files:
        filename = secure_filename(file.filename)
        if not filename:
            continue

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in current_app.config["ALLOWED_EXTENSIONS"] and ext != "txt":
            errors.append({"filename": filename, "error": f"Unsupported format .{ext}"})
            continue

        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        try:
            # Execute LangGraph Screening Graph
            initial_state = {
                "file_path": file_path,
                "filename": filename,
                "file_type": ext,
                "raw_text": "",
                "extracted_data": {},
                "candidate_id": None,
                "indexed_in_chroma": False,
                "error": None
            }

            final_state = graph.invoke(initial_state)

            if final_state.get("error"):
                errors.append({"filename": filename, "error": final_state["error"]})
            else:
                candidate_id = final_state.get("candidate_id")
                candidate = Candidate.query.get(candidate_id) if candidate_id else None
                results.append({
                    "filename": filename,
                    "candidate": candidate.to_dict() if candidate else final_state.get("extracted_data")
                })
        except Exception as e:
            errors.append({"filename": filename, "error": str(e)})

    return jsonify({
        "message": f"Processed {len(results)} resumes with {len(errors)} errors.",
        "processed": results,
        "errors": errors
    }), 200

@resume_bp.route("/candidates/<int:candidate_id>", methods=["DELETE"])
def delete_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    db.session.delete(candidate)
    db.session.commit()
    return jsonify({"message": f"Candidate {candidate_id} deleted successfully"}), 200

