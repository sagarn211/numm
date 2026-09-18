"""
CPSE Material Image Search
----------------------------------
AI-Driven Standardization & Harmonization of Material Codes Across CPSEs.

Single pipeline:
    CSV + Images -> CLIP embeddings -> FAISS index -> FastAPI search API -> Frontend

Run with:
    uvicorn image_recog:app --reload
"""

import io
import pickle
from pathlib import Path
from typing import Dict, List, Optional

import faiss
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from sentence_transformers import SentenceTransformer

# ----------------------------------------------------------------------------
# Paths / constants
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
INDEX_DIR = BASE_DIR / "index"
CSV_PATH = BASE_DIR / "materials.csv"
FAISS_INDEX_PATH = INDEX_DIR / "faiss.index"
METADATA_PATH = INDEX_DIR / "metadata.pkl"

EMBEDDING_DIM = 512  # output dimension of clip-ViT-B-32
REQUIRED_COLUMNS = {"material_code", "description", "category", "unit", "manufacturer", "image"}

IMAGES_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)

# ----------------------------------------------------------------------------
# App setup
# ----------------------------------------------------------------------------
app = FastAPI(title="CPSE Material Image Search")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the images folder directly so the frontend can show matched photos.
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

print("[INFO] Loading CLIP model (sentence-transformers/clip-ViT-B-32)...")
print("[INFO] The first run downloads the model - this can take a minute.")
model = SentenceTransformer("clip-ViT-B-32")
print("[INFO] CLIP model loaded successfully.")

# Global in-memory index state (single source of truth - no duplicate pipelines).
faiss_index: Optional[faiss.Index] = None
metadata_store: List[Dict] = []


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def normalize(vec: np.ndarray) -> np.ndarray:
    """L2-normalize embeddings so inner product == cosine similarity."""
    vec = vec.astype("float32")
    norm = np.linalg.norm(vec, axis=-1, keepdims=True)
    norm[norm == 0] = 1e-10
    return vec / norm


def embed_image(img: Image.Image) -> np.ndarray:
    """Generate a normalized CLIP embedding for a single PIL image."""
    img = img.convert("RGB")
    emb = model.encode([img], convert_to_numpy=True, show_progress_bar=False)
    return normalize(emb)[0]


def build_index() -> Dict:
    """
    Rebuild the FAISS index from materials.csv + images/.
    This is the ONLY indexing pipeline in the project (used both at startup
    and by the /reindex endpoint) so there is never a second, out-of-sync copy.

    Skips bad rows / missing / corrupted images instead of crashing.
    """
    global faiss_index, metadata_store

    summary = {
        "total_rows": 0,
        "indexed": 0,
        "skipped_missing_image": 0,
        "skipped_bad_image": 0,
        "skipped_bad_row": 0,
        "warnings": [],
    }

    if not CSV_PATH.exists():
        raise HTTPException(status_code=500, detail=f"materials.csv not found at {CSV_PATH}")

    try:
        df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read materials.csv: {e}")

    df.columns = [c.strip() for c in df.columns]
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        raise HTTPException(
            status_code=500,
            detail=f"materials.csv is missing required columns: {sorted(missing_cols)}",
        )

    summary["total_rows"] = len(df)

    embeddings = []
    records = []

    for idx, row in df.iterrows():
        try:
            material_code = str(row["material_code"]).strip()
            image_name = str(row["image"]).strip()

            if not material_code or not image_name:
                summary["skipped_bad_row"] += 1
                msg = f"Row {idx}: missing material_code or image filename - skipped."
                print("[WARN]", msg)
                summary["warnings"].append(msg)
                continue

            image_path = IMAGES_DIR / image_name

            if not image_path.exists():
                summary["skipped_missing_image"] += 1
                msg = f"Row {idx} ({material_code}): image '{image_name}' not found in images/ - skipped."
                print("[WARN]", msg)
                summary["warnings"].append(msg)
                continue

            try:
                img = Image.open(image_path)
                img.verify()  # detects corrupted files
                img = Image.open(image_path)  # must reopen after verify()
            except (UnidentifiedImageError, OSError) as e:
                summary["skipped_bad_image"] += 1
                msg = f"Row {idx} ({material_code}): could not open image '{image_name}' ({e}) - skipped."
                print("[WARN]", msg)
                summary["warnings"].append(msg)
                continue

            emb = embed_image(img)
            embeddings.append(emb)
            records.append(
                {
                    "material_code": material_code,
                    "description": str(row["description"]).strip(),
                    "category": str(row["category"]).strip(),
                    "unit": str(row["unit"]).strip(),
                    "manufacturer": str(row["manufacturer"]).strip(),
                    "image": image_name,
                }
            )
            summary["indexed"] += 1

        except Exception as e:
            summary["skipped_bad_row"] += 1
            msg = f"Row {idx}: unexpected error ({e}) - skipped."
            print("[WARN]", msg)
            summary["warnings"].append(msg)
            continue

    if embeddings:
        matrix = np.vstack(embeddings).astype("float32")
        new_index = faiss.IndexFlatIP(matrix.shape[1])
        new_index.add(matrix)
    else:
        new_index = faiss.IndexFlatIP(EMBEDDING_DIM)
        msg = "No valid images were indexed. Search will return no results until you add images and re-index."
        print("[WARN]", msg)
        summary["warnings"].append(msg)

    faiss_index = new_index
    metadata_store = records

    try:
        faiss.write_index(faiss_index, str(FAISS_INDEX_PATH))
        with open(METADATA_PATH, "wb") as f:
            pickle.dump(metadata_store, f)
    except Exception as e:
        print("[WARN] Could not save index to disk:", e)

    print(f"[INFO] Index build complete. Indexed {summary['indexed']} / {summary['total_rows']} rows.")
    return summary


def load_index_from_disk() -> bool:
    """Try to load a previously saved index instead of rebuilding on every restart."""
    global faiss_index, metadata_store
    if FAISS_INDEX_PATH.exists() and METADATA_PATH.exists():
        try:
            faiss_index = faiss.read_index(str(FAISS_INDEX_PATH))
            with open(METADATA_PATH, "rb") as f:
                metadata_store = pickle.load(f)
            print(f"[INFO] Loaded saved index with {len(metadata_store)} materials.")
            return True
        except Exception as e:
            print("[WARN] Could not load saved index, will rebuild from scratch:", e)
    return False


# ----------------------------------------------------------------------------
# Startup
# ----------------------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    if not load_index_from_disk():
        build_index()


# ----------------------------------------------------------------------------
# API routes
# ----------------------------------------------------------------------------
@app.post("/reindex")
def reindex():
    """Rebuild the FAISS index from the current materials.csv + images/ folder."""
    summary = build_index()
    return JSONResponse(content=summary)


@app.get("/status")
def status():
    return {
        "materials_indexed": len(metadata_store),
        "images_dir": str(IMAGES_DIR),
        "csv_path": str(CSV_PATH),
    }


@app.post("/search")
async def search(file: UploadFile = File(...), top_k: int = 5):
    if faiss_index is None or len(metadata_store) == 0:
        raise HTTPException(
            status_code=400,
            detail="Index is empty. Add images + CSV rows, then click 'Re-index Materials'.",
        )

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not an image.")

    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        img.verify()
        img = Image.open(io.BytesIO(contents))  # reopen after verify()
    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(status_code=400, detail=f"Could not read uploaded image: {e}")

    try:
        query_emb = embed_image(img).reshape(1, -1).astype("float32")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {e}")

    k = max(1, min(top_k, len(metadata_store)))
    scores, indices = faiss_index.search(query_emb, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(metadata_store):
            continue
        record = metadata_store[idx]
        results.append(
            {
                "material_code": record["material_code"],
                "description": record["description"],
                "category": record["category"],
                "unit": record["unit"],
                "manufacturer": record["manufacturer"],
                "image": record["image"],
                "image_url": f"/images/{record['image']}",
                "similarity": round(float(score), 4),
            }
        )

    return {"query_filename": file.filename, "results": results}


# ----------------------------------------------------------------------------
# Frontend (single HTML page served directly by FastAPI)
# ----------------------------------------------------------------------------
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CPSE Material Image Search</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  :root {
    --accent: #1a5fb4;
    --bg: #f4f6f9;
    --card: #ffffff;
    --border: #dfe3e8;
    --text: #1e2430;
    --muted: #667085;
  }
  * { box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    margin: 0;
    padding: 24px;
  }
  h1 { font-size: 22px; margin-bottom: 4px; }
  p.subtitle { color: var(--muted); margin-top: 0; margin-bottom: 24px; }
  .panel {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    max-width: 900px;
    margin: 0 auto 20px auto;
  }
  .row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
  input[type=file] { flex: 1; min-width: 220px; }
  button {
    background: var(--accent);
    color: white;
    border: none;
    padding: 10px 18px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
  }
  button.secondary {
    background: #ffffff;
    color: var(--accent);
    border: 1px solid var(--accent);
  }
  button:disabled { opacity: 0.6; cursor: not-allowed; }
  #status-bar {
    max-width: 900px;
    margin: 0 auto 20px auto;
    font-size: 13px;
    color: var(--muted);
  }
  #message {
    max-width: 900px;
    margin: 0 auto 16px auto;
    font-size: 14px;
  }
  .msg-error { color: #c0392b; }
  .msg-ok { color: #1e8449; }
  #preview {
    max-width: 220px;
    max-height: 220px;
    border-radius: 8px;
    border: 1px solid var(--border);
    margin-top: 12px;
    display: none;
  }
  .results {
    max-width: 900px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px;
  }
  .result-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }
  .result-card img {
    width: 100%;
    height: 160px;
    object-fit: cover;
    background: #eee;
    display: block;
  }
  .result-body { padding: 12px 14px; }
  .rank {
    display: inline-block;
    background: var(--accent);
    color: white;
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 12px;
    margin-bottom: 6px;
  }
  .code { font-weight: 600; font-size: 15px; }
  .desc { font-size: 13px; color: var(--text); margin: 4px 0; }
  .meta { font-size: 12px; color: var(--muted); line-height: 1.6; }
  .score { font-size: 12px; font-weight: 600; color: var(--accent); margin-top: 6px; }
</style>
</head>
<body>

  <h1>CPSE Material Image Search</h1>
  <p class="subtitle">AI-driven standardization &amp; harmonization of material codes across CPSEs - upload a photo to find matching materials.</p>

  <div class="panel">
    <div class="row">
      <input type="file" id="fileInput" accept="image/*">
      <button id="searchBtn">Search</button>
      <button id="reindexBtn" class="secondary">Re-index Materials</button>
    </div>
    <img id="preview" alt="preview">
  </div>

  <div id="status-bar">Loading status...</div>
  <div id="message"></div>
  <div class="results" id="results"></div>

<script>
const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const searchBtn = document.getElementById('searchBtn');
const reindexBtn = document.getElementById('reindexBtn');
const resultsEl = document.getElementById('results');
const messageEl = document.getElementById('message');
const statusBar = document.getElementById('status-bar');

async function refreshStatus() {
  try {
    const res = await fetch('/status');
    const data = await res.json();
    statusBar.textContent = `Materials currently indexed: ${data.materials_indexed}`;
  } catch (e) {
    statusBar.textContent = 'Could not load status.';
  }
}
refreshStatus();

fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  if (file) {
    preview.src = URL.createObjectURL(file);
    preview.style.display = 'block';
  } else {
    preview.style.display = 'none';
  }
});

function setMessage(text, ok) {
  messageEl.textContent = text;
  messageEl.className = ok ? 'msg-ok' : 'msg-error';
}

searchBtn.addEventListener('click', async () => {
  const file = fileInput.files[0];
  if (!file) {
    setMessage('Please choose an image file first.', false);
    return;
  }
  setMessage('Searching...', true);
  resultsEl.innerHTML = '';
  searchBtn.disabled = true;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/search?top_k=5', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) {
      setMessage(data.detail || 'Search failed.', false);
      return;
    }

    if (!data.results || data.results.length === 0) {
      setMessage('No matches found. Try re-indexing or add more materials.', false);
      return;
    }

    setMessage(`Found ${data.results.length} match(es) for "${data.query_filename}".`, true);

    data.results.forEach((r, i) => {
      const card = document.createElement('div');
      card.className = 'result-card';
      card.innerHTML = `
        <img src="${r.image_url}" onerror="this.style.display='none'">
        <div class="result-body">
          <span class="rank">Match #${i + 1}</span>
          <div class="code">${r.material_code}</div>
          <div class="desc">${r.description}</div>
          <div class="meta">
            Category: ${r.category}<br>
            Unit: ${r.unit}<br>
            Manufacturer: ${r.manufacturer}
          </div>
          <div class="score">Similarity: ${r.similarity}</div>
        </div>
      `;
      resultsEl.appendChild(card);
    });
  } catch (e) {
    setMessage('Network or server error: ' + e, false);
  } finally {
    searchBtn.disabled = false;
  }
});

reindexBtn.addEventListener('click', async () => {
  setMessage('Re-indexing materials... this can take a little while.', true);
  reindexBtn.disabled = true;
  try {
    const res = await fetch('/reindex', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      setMessage(data.detail || 'Re-index failed.', false);
      return;
    }
    setMessage(`Re-index complete. Indexed ${data.indexed} / ${data.total_rows} rows.`, true);
    refreshStatus();
  } catch (e) {
    setMessage('Network or server error: ' + e, false);
  } finally {
    reindexBtn.disabled = false;
  }
});
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home():
    return FRONTEND_HTML
