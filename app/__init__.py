import os
from flask import Flask
from flask_cors import CORS
from config import Config
from app.models import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS
    CORS(app)

    # Initialize SQLAlchemy database
    db.init_app(app)

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["CHROMA_PERSIST_DIR"], exist_ok=True)

    with app.app_context():
        # Create database tables
        db.create_all()

    # Register Blueprints
    from app.routes.web_routes import web_bp
    from app.routes.job_routes import job_bp
    from app.routes.resume_routes import resume_bp
    from app.routes.match_routes import match_bp
    from app.routes.interview_routes import interview_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(job_bp, url_prefix="/api/jobs")
    app.register_blueprint(resume_bp, url_prefix="/api/resumes")
    app.register_blueprint(match_bp, url_prefix="/api/match")
    app.register_blueprint(interview_bp, url_prefix="/api/interview")

    return app

