import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "hiremind-ai-secret-key-recruitment-2026")
    
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'hiremind.db'}")
    # Handle SQLAlchemy 1.4+ postgresql:// vs postgres:// if needed
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Groq API configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant")

    # ChromaDB & Sentence Transformer configuration (Online Service)
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", os.getenv("HF_TOKEN", ""))
    SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    USE_ONLINE_EMBEDDINGS = os.getenv("USE_ONLINE_EMBEDDINGS", "true").lower() in ("true", "1", "yes")

    # Uploads
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)) # 16 MB max
    ALLOWED_EXTENSIONS = {"pdf", "docx"}

