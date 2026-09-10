"""
test_setup.py
--------------
Quick sanity check for the AI matching stack (SIH National Material Master MVP).

Run this once after `pip install -r requirements.txt` to confirm:
  1. sentence-transformers loads and can embed text
  2. FAISS can index + search those embeddings
  3. RapidFuzz can score text similarity

It uses the 4 real example records from the problem statement (the HEX BOLT
M16 x 50 SS304 case) so you can see real numbers, not toy data.
"""

from sentence_transformers import SentenceTransformer, util
from rapidfuzz import fuzz
import faiss
import numpy as np


# ---------------------------------------------------------------------------
# 1. Sample data — the 4 CPSE records from the problem statement
# ---------------------------------------------------------------------------
records = [
    {"cpse": "NTPC", "code": "NTPC-45821", "desc": "HEX BOLT M16 X 50 MM SS304"},
    {"cpse": "SAIL", "code": "SAIL-B9821", "desc": "Hexagonal Bolt M16*50 Stainless Steel 304"},
    {"cpse": "IOC",  "code": "IOC-7721",   "desc": "SS 304 HEX HEAD BOLT M16 X 50"},
    {"cpse": "NM",   "code": "NM-9281",    "desc": "HEX HEAD BOLT M16 50MM SS304"},
]

descriptions = [r["desc"] for r in records]


# ---------------------------------------------------------------------------
# 2. Load embedding model (downloads once, then cached locally)
# ---------------------------------------------------------------------------
print("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Model loaded OK.\n")


# ---------------------------------------------------------------------------
# 3. Generate embeddings
# ---------------------------------------------------------------------------
embeddings = model.encode(descriptions, normalize_embeddings=True)
print(f"Generated embeddings, shape = {embeddings.shape}\n")


# ---------------------------------------------------------------------------
# 4. Semantic similarity — pairwise cosine similarity (sentence-transformers util)
# ---------------------------------------------------------------------------
print("=== Semantic similarity matrix (cosine) ===")
sim_matrix = util.cos_sim(embeddings, embeddings)
for i, r in enumerate(records):
    print(f"{r['code']:>12}: " + " ".join(f"{sim_matrix[i][j]:.2f}" for j in range(len(records))))
print()


# ---------------------------------------------------------------------------
# 5. FAISS — build an index and retrieve top-k nearest neighbors for record 0
# ---------------------------------------------------------------------------
dim = embeddings.shape[1]
index = faiss.IndexFlatIP(dim)  # inner product == cosine similarity since vectors are normalized
index.add(np.array(embeddings, dtype="float32"))

query_vec = np.array([embeddings[0]], dtype="float32")  # query with the NTPC record
k = 3
scores, indices = index.search(query_vec, k)

print(f"=== FAISS top-{k} matches for '{records[0]['desc']}' ===")
for score, idx in zip(scores[0], indices[0]):
    print(f"  {score:.4f}  ->  {records[idx]['code']}: {records[idx]['desc']}")
print()


# ---------------------------------------------------------------------------
# 6. RapidFuzz — fuzzy text similarity for the same pair
# ---------------------------------------------------------------------------
print("=== RapidFuzz token_sort_ratio (record 0 vs others) ===")
for r in records[1:]:
    score = fuzz.token_sort_ratio(records[0]["desc"], r["desc"])
    print(f"  {records[0]['code']} vs {r['code']}: {score:.1f}")
print()

print("All checks passed. Environment is ready for the AI matching pipeline.")
