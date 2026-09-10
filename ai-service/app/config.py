import os
from pathlib import Path

MODEL_NAME = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
MODEL_PATH = os.getenv("MODEL_PATH", MODEL_NAME)
MODEL_VERSION = os.getenv("MODEL_VERSION", "unversioned-development-model")
MATCHER_VERSION = os.getenv("MATCHER_VERSION", "1.0.0")
MAX_CANDIDATES_PER_MATERIAL = int(os.getenv("MAX_CANDIDATES_PER_MATERIAL", "10"))
CANDIDATE_MIN_SIMILARITY = float(os.getenv("CANDIDATE_MIN_SIMILARITY", "0.55"))
TEAMMATE_AI_SRC = os.getenv("TEAMMATE_AI_SRC", str(Path(__file__).resolve().parents[2] / "teammate-ai" / "src"))
ALLOW_FALLBACK = os.getenv("ALLOW_FALLBACK", "true").lower() == "true"
AI_ENGINE_REQUIRED = os.getenv("AI_ENGINE_REQUIRED", "false").lower() == "true"
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "/data/faiss/materials.hnsw")
