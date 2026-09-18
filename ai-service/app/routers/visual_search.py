import io
import json
import os
from pathlib import Path
import threading
import faiss
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sentence_transformers import SentenceTransformer

router = APIRouter(tags=["Visual search"])
MODEL_NAME = "clip-ViT-B-32"
DATA_DIR = Path(os.getenv("VISUAL_INDEX_DIR", "/ai-data"))
INDEX_PATH, METADATA_PATH = DATA_DIR / "visual.index", DATA_DIR / "visual_metadata.json"
_model = _index = _metadata = None
_lock = threading.Lock()

def _normalise(vector):
    vector = np.asarray(vector, dtype="float32")
    return vector / np.maximum(np.linalg.norm(vector, axis=-1, keepdims=True), 1e-12)

def _load():
    global _model, _index, _metadata
    with _lock:
        if _model is None:
            _model = SentenceTransformer(os.getenv("VISUAL_MODEL_PATH", MODEL_NAME))
        if _index is None and INDEX_PATH.exists() and METADATA_PATH.exists():
            index, metadata = faiss.read_index(str(INDEX_PATH)), json.loads(METADATA_PATH.read_text(encoding="utf-8"))
            if index.ntotal == len(metadata): _index, _metadata = index, metadata
        if _index is None: _index, _metadata = faiss.IndexFlatIP(512), []
    return _model, _index, _metadata

def add_verified_embedding(image: Image.Image, metadata: dict):
    """Integration hook for controlled ingestion jobs; metadata must contain DB IDs."""
    model, index, entries = _load()
    vector = _normalise(model.encode([image.convert("RGB")], convert_to_numpy=True, show_progress_bar=False))
    with _lock:
        index.add(vector); entries.append(metadata); DATA_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(INDEX_PATH)); METADATA_PATH.write_text(json.dumps(entries), encoding="utf-8")

@router.post("/api/v1/visual-search")
async def search(file: UploadFile = File(...), top_k: int = Form(5)):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(400, "Query image must be JPEG, PNG, or WebP")
    try:
        raw = await file.read(); image = Image.open(io.BytesIO(raw)); image.verify(); image = Image.open(io.BytesIO(raw)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(400, "Query file is not a valid image") from exc
    model, index, entries = _load()
    if not entries: raise HTTPException(409, "Visual index is empty; index verified material images first")
    vector = _normalise(model.encode([image], convert_to_numpy=True, show_progress_bar=False))
    scores, positions = index.search(vector, min(max(1, top_k), len(entries)))
    return {"engine": "CLIP_FAISS", "model": MODEL_NAME, "candidates": [{**{key: entries[position][key] for key in ("material_image_id", "material_id")}, "visual_similarity": round(float(score), 5)} for score, position in zip(scores[0], positions[0]) if position >= 0]}

@router.post("/api/v1/visual-index")
async def index_verified_image(file: UploadFile = File(...), material_image_id: int = Form(...), material_id: int = Form(...)):
    """Called only after the main API verifies an image; it owns the DB workflow."""
    try:
        raw = await file.read(); image = Image.open(io.BytesIO(raw)); image.verify(); image = Image.open(io.BytesIO(raw)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(400, "Image is not valid") from exc
    add_verified_embedding(image, {"material_image_id": material_image_id, "material_id": material_id})
    return {"indexed": True, "engine": "CLIP_FAISS", "embedding_dimension": 512}

@router.get("/api/v1/visual-search/status")
def status():
    _, index, entries = _load()
    return {"engine": "CLIP_FAISS", "model": MODEL_NAME, "embedding_dimension": index.d, "images_indexed": len(entries), "index_path": str(INDEX_PATH)}
