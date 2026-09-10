"""
src/embed_and_retrieve.py
---------------------------
Wraps sentence-transformers (embeddings) + FAISS (vector search) into
reusable functions. This is the semantic similarity signal -- 40% of the
final hybrid score:

    final_score = 0.4 * semantic_similarity + 0.4 * attribute_match + 0.2 * fuzzy

It does two jobs:
  1. embed_texts()        -> turn descriptions into embedding vectors
  2. find_top_k_matches() -> given one new material, retrieve its k most
                              similar candidates from a larger set WITHOUT
                              comparing it against every single record
                              (that's what FAISS is for -- fast approximate
                              nearest-neighbor search instead of brute force)

The model loads ONCE per process (loading it repeatedly is slow) --
call get_model() and reuse the same instance across your pipeline.

Run this file directly to see it applied to your dataset:
    python src/embed_and_retrieve.py
"""

import numpy as np
import os
import hashlib
import json
import threading
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
import faiss

from normalize import normalize


# ---------------------------------------------------------------------------
# Model loading -- cached so we don't reload it on every call
# ---------------------------------------------------------------------------
_model = None
_index_lock = threading.Lock()


def get_model():
    """
    Load (or return the already-loaded) sentence-transformers model.
    First call downloads/loads the model (~90MB), subsequent calls are instant.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(os.getenv("MODEL_PATH", "all-MiniLM-L6-v2"))
    return _model


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------
def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Convert a list of (already-normalized) text strings into embedding
    vectors. Returns a numpy array of shape (len(texts), embedding_dim).

    normalize_embeddings=True makes each vector unit-length, which means
    cosine similarity == inner product -- this is what lets us use FAISS's
    IndexFlatIP (inner product index) as a cosine-similarity search.
    """
    model = get_model()
    return model.encode(texts, normalize_embeddings=True)


def semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Return a single 0.0-1.0 cosine similarity score between two
    ALREADY-NORMALIZED strings. Convenience wrapper for comparing just
    one pair (use embed_texts() + build_faiss_index() instead when you
    need to compare one item against MANY candidates -- much faster).
    """
    vecs = embed_texts([text_a, text_b])
    score = util.cos_sim(vecs[0], vecs[1])
    return float(score[0][0])


# ---------------------------------------------------------------------------
# FAISS retrieval
# ---------------------------------------------------------------------------
def _index_fingerprint(embeddings: np.ndarray) -> str:
    values = np.ascontiguousarray(embeddings, dtype="float32")
    return hashlib.sha256(values.tobytes()).hexdigest()


def build_faiss_index(embeddings: np.ndarray):
    """
    Build or reuse a persistent HNSW inner-product index. A content fingerprint
    prevents a stale index from being loaded for a different candidate corpus.
    """
    values = np.ascontiguousarray(embeddings, dtype="float32")
    dim = values.shape[1]
    fingerprint = _index_fingerprint(values)
    configured_path = os.getenv("FAISS_INDEX_PATH")
    index_path = Path(configured_path) if configured_path else None
    metadata_path = Path(f"{configured_path}.json") if configured_path else None
    expected_metadata = {
        "fingerprint": fingerprint, "dimension": dim, "vectors": len(values),
    }
    with _index_lock:
        if index_path and metadata_path and index_path.exists() and metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                if metadata == expected_metadata:
                    index = faiss.read_index(str(index_path))
                    if index.d != dim or index.ntotal != len(values):
                        raise ValueError("Persistent FAISS index metadata mismatch")
                    index.hnsw.efSearch = max(64, min(512, len(values)))
                    return index
            except (OSError, ValueError, json.JSONDecodeError, AttributeError):
                pass

        index = faiss.IndexHNSWFlat(dim, 32, faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efConstruction = 200
        index.hnsw.efSearch = max(64, min(512, len(values)))
        index.add(values)
        if index_path and metadata_path:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_index = Path(f"{index_path}.tmp")
            temporary_metadata = Path(f"{metadata_path}.tmp")
            faiss.write_index(index, str(temporary_index))
            temporary_metadata.write_text(
                json.dumps(expected_metadata), encoding="utf-8"
            )
            os.replace(temporary_index, index_path)
            os.replace(temporary_metadata, metadata_path)
        return index


def find_top_k_matches(
    query_text: str,
    candidate_texts: list[str],
    k: int = 5,
) -> list[tuple[int, float]]:
    """
    Given one normalized query description and a list of normalized
    candidate descriptions, return the top-k most semantically similar
    candidates.

    Returns a list of (candidate_index, similarity_score) tuples, sorted
    by similarity descending. candidate_index refers to the position in
    candidate_texts, so the caller can map it back to a material record.

    This is the "candidate retrieval" step from the SIH blueprint -- for
    a new/uploaded material, instead of comparing it against every single
    material in the national database (slow, O(n) per query), FAISS finds
    the closest matches almost instantly, even as the database grows.
    """
    if not candidate_texts:
        return []

    candidate_embeddings = embed_texts(candidate_texts)
    index = build_faiss_index(candidate_embeddings)

    query_embedding = embed_texts([query_text])
    query_vec = np.array(query_embedding, dtype="float32")

    k = min(k, len(candidate_texts))  # can't retrieve more than we have
    scores, indices = index.search(query_vec, k)

    return [(int(idx), float(score)) for idx, score in zip(indices[0], scores[0])]


# ---------------------------------------------------------------------------
# Standalone test -- run this file directly to see it applied to your dataset
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import csv
    import os

    print("Loading model (first run downloads ~90MB, please wait)...")
    get_model()
    print("Model loaded.\n")

    print("=== semantic_similarity() demo on hardcoded examples ===\n")
    pair_a = normalize("HEX BOLT M16 X 50 MM SS304")
    pair_b = normalize("Hexagonal Bolt M16*50 Stainless Steel 304")
    pair_c = normalize("HEX BOLT M20 X 75 MM SS304")  # genuinely different size

    print(f"  A: {pair_a}")
    print(f"  B: {pair_b}")
    print(f"  similarity(A, B) = {semantic_similarity(pair_a, pair_b):.4f}  (expect HIGH -- same bolt)\n")

    print(f"  A: {pair_a}")
    print(f"  C: {pair_c}")
    print(f"  similarity(A, C) = {semantic_similarity(pair_a, pair_c):.4f}  (expect LOWER -- different size)\n")

    # Apply to the real dataset if it exists
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "synthetic_materials.csv",
    )
    if os.path.exists(data_path):
        print("=== find_top_k_matches() applied to your synthetic dataset ===\n")
        with open(data_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        normalized_descs = [normalize(r["original_description"]) for r in rows]

        query_row = rows[0]
        query_text = normalized_descs[0]
        print(f"Query: [{query_row['cpse']}] {query_row['original_description']}")
        print(f"Normalized: {query_text}\n")

        # Search against everything EXCEPT the query itself
        candidates = normalized_descs[1:]
        candidate_rows = rows[1:]

        top_matches = find_top_k_matches(query_text, candidates, k=5)

        print("Top 5 matches:")
        for idx, score in top_matches:
            r = candidate_rows[idx]
            print(f"  {score:.4f}  [{r['cpse']}] {r['original_description']}")
    else:
        print(f"No dataset found at {data_path} -- run data/make_dataset.py first.")
