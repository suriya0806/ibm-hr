import os
import math
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from config import Config

class VectorService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VectorService, cls).__new__(cls)
            cls._instance._init_chroma()
        return cls._instance

    def _init_chroma(self):
        persist_dir = Config.CHROMA_PERSIST_DIR
        os.makedirs(persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persist_dir)

        # Choose embedding function: Chroma's default sentence-transformer
        try:
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=Config.EMBEDDING_MODEL
            )
        except Exception:
            # Fallback to Chroma's built-in default embedding function
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        # Sentence Transformer configuration - Use Online Service
        self.embedding_fn = None
        hf_key = (Config.HUGGINGFACE_API_KEY or "").strip()
        is_real_key = hf_key and not hf_key.startswith("your_") and len(hf_key) > 5

        if Config.USE_ONLINE_EMBEDDINGS and is_real_key:
            try:
                # Online Sentence Transformer via Hugging Face Inference API
                self.embedding_fn = embedding_functions.HuggingFaceEmbeddingFunction(
                    api_key=hf_key,
                    model_name=Config.SENTENCE_TRANSFORMER_MODEL
                )
                print(f"[VectorService] Using Online Sentence Transformer API: {Config.SENTENCE_TRANSFORMER_MODEL}")
            except Exception as e:
                print(f"[VectorService] Could not initialize online HuggingFace embedding: {e}")

        # Fallback to Chroma's built-in ONNX embedding function if online is not configured or fails
        if not self.embedding_fn:
            try:
                self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
                print("[VectorService] Using Chroma built-in DefaultEmbeddingFunction (ONNX MiniLM)")
            except Exception as e:
                print(f"[VectorService] DefaultEmbeddingFunction warning: {e}")

        # Collections
        self.resume_collection = self.client.get_or_create_collection(
            name="hiremind_resumes",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
        self.job_collection = self.client.get_or_create_collection(
            name="hiremind_jobs",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def index_resume(self, candidate_id: int, text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Store candidate resume embedding in ChromaDB.
        """
        meta = metadata or {}
        meta["candidate_id"] = int(candidate_id)
        # Ensure values in metadata are primitive types accepted by Chroma
        safe_meta = {k: str(v) if isinstance(v, (list, dict)) else v for k, v in meta.items()}

        self.resume_collection.upsert(
            ids=[f"candidate_{candidate_id}"],
            documents=[text[:8000]],  # Cap text for embedding performance
            metadatas=[safe_meta]
        )
        try:
            self.resume_collection.upsert(
                ids=[f"candidate_{candidate_id}"],
                documents=[text[:8000]],
                metadatas=[safe_meta]
            )
        except Exception as e:
            print(f"[VectorService] Warning: Resume ChromaDB upsert skipped/failed: {e}")

    def index_job(self, job_id: int, text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Store job description embedding in ChromaDB.
        """
        meta = metadata or {}
        meta["job_id"] = int(job_id)
        safe_meta = {k: str(v) if isinstance(v, (list, dict)) else v for k, v in meta.items()}

        self.job_collection.upsert(
            ids=[f"job_{job_id}"],
            documents=[text[:8000]],
            metadatas=[safe_meta]
        )
        try:
            self.job_collection.upsert(
                ids=[f"job_{job_id}"],
                documents=[text[:8000]],
                metadatas=[safe_meta]
            )
        except Exception as e:
            print(f"[VectorService] Warning: Job ChromaDB upsert skipped/failed: {e}")

    def compute_semantic_similarity(self, resume_text: str, job_text: str) -> float:
        """
        Computes cosine similarity between resume text and job text as a percentage (0 - 100%).
        """
        try:
            # Generate embeddings
            embeddings = self.embedding_fn([resume_text[:4000], job_text[:4000]])
            v1, v2 = embeddings[0], embeddings[1]

            # Cosine similarity formula: (A . B) / (||A|| * ||B||)
            dot_product = sum(a * b for a, b in zip(v1, v2))
            norm_a = math.sqrt(sum(a * a for a in v1))
            norm_b = math.sqrt(sum(b * b for b in v2))

            if norm_a == 0 or norm_b == 0:
                return 50.0

            cosine_sim = dot_product / (norm_a * norm_b)
            # Map cosine similarity (-1 to 1 or 0 to 1) to percentage 0 to 100
            score = max(0.0, min(100.0, (cosine_sim + 1.0) / 2.0 * 100.0 if cosine_sim < 0 else cosine_sim * 100.0))
            return round(score, 1)
        except Exception as e:
            # Simple word overlap fallback if embedding computation fails
            r_words = set(resume_text.lower().split())
            j_words = set(job_text.lower().split())
            if not j_words:
                return 50.0
            overlap = len(r_words.intersection(j_words)) / max(len(j_words), 1)
            return round(min(100.0, overlap * 200.0), 1)

    def find_top_candidates_for_job(self, job_text: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Query top matching resumes for a job description via ChromaDB.
        """
        try:
            count = self.resume_collection.count()
            if count == 0:
                return []
            
            n = min(n_results, count)
            results = self.resume_collection.query(
                query_texts=[job_text[:4000]],
                n_results=n
            )

            matches = []
            if results and results.get("ids") and len(results["ids"]) > 0:
                ids = results["ids"][0]
                distances = results.get("distances", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]

                for doc_id, dist, meta in zip(ids, distances, metadatas):
                    # Cosine distance to similarity: similarity = 1 - distance
                    sim_score = max(0.0, min(100.0, (1.0 - dist) * 100.0))
                    candidate_id = int(doc_id.replace("candidate_", ""))
                    matches.append({
                        "candidate_id": candidate_id,
                        "semantic_score": round(sim_score, 1),
                        "metadata": meta
                    })
            return matches
        except Exception:
            return []

