"""Resolves candidate mention strings (from extraction.py) to real entity
records in the dataset, using the precomputed embedding index plus a fuzzy
string-match fallback. Anything below threshold is left unresolved rather
than guessed - this is what makes "no impact" possible.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from google.genai import types
from rapidfuzz import fuzz

from core.gemini_client import EMBEDDING_DIM, EMBEDDING_MODEL, get_client

INDEX_PATH = Path(__file__).parent.parent / "data" / "embeddings.npz"

EMBEDDING_THRESHOLD = 0.70
FUZZY_THRESHOLD = 85  # rapidfuzz partial_ratio, 0-100

_index = None


def _load_index():
    global _index
    if _index is None:
        data = np.load(INDEX_PATH, allow_pickle=True)
        _index = {
            "keys": data["keys"],
            "texts": data["texts"],
            "vectors": data["vectors"],
        }
    return _index


@dataclass
class Resolution:
    mention: str
    entity_key: str | None  # "type:id", e.g. "supplier:S1"
    score: float
    method: str  # "embedding" | "fuzzy" | "unresolved"


def _embed(text: str) -> np.ndarray:
    client = get_client()
    resp = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
    )
    return np.array(resp.embeddings[0].values, dtype=np.float32)


def resolve_mention(mention: str) -> Resolution:
    idx = _load_index()
    keys, texts, vectors = idx["keys"], idx["texts"], idx["vectors"]

    qv = _embed(mention)
    sims = vectors @ qv / (np.linalg.norm(vectors, axis=1) * np.linalg.norm(qv) + 1e-9)
    best_i = int(np.argmax(sims))
    best_sim = float(sims[best_i])

    if best_sim >= EMBEDDING_THRESHOLD:
        return Resolution(mention, str(keys[best_i]), best_sim, "embedding")

    # Fallback: fuzzy string match, catches short codes/names embeddings miss.
    fuzzy_scores = [fuzz.partial_ratio(mention.lower(), str(t).lower()) for t in texts]
    best_fi = int(np.argmax(fuzzy_scores))
    best_fscore = fuzzy_scores[best_fi]

    if best_fscore >= FUZZY_THRESHOLD:
        return Resolution(mention, str(keys[best_fi]), best_fscore / 100.0, "fuzzy")

    return Resolution(mention, None, max(best_sim, best_fscore / 100.0), "unresolved")


def resolve_mentions(mentions: list[str]) -> list[Resolution]:
    return [resolve_mention(m) for m in mentions]
