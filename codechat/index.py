"""Embed chunks and store/search them with plain numpy (no vector DB needed)."""
import json
from pathlib import Path

import numpy as np

from . import config
from .ingest import Chunk

_model = None


def get_embedder():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(config.EMBED_MODEL)
    return _model


def embed(texts, batch_size=64):
    vecs = get_embedder().encode(
        texts, batch_size=batch_size, show_progress_bar=len(texts) > 100,
        normalize_embeddings=True,
    )
    return np.asarray(vecs, dtype=np.float32)


def _embed_text(c: Chunk) -> str:
    # Prefixing the path helps queries like "where is auth handled?"
    return f"File: {c.path}\n{c.text}"


class Index:
    def __init__(self, chunks, vectors):
        self.chunks = chunks
        self.vectors = vectors

    @classmethod
    def build(cls, chunks):
        vectors = embed([_embed_text(c) for c in chunks])
        return cls(chunks, vectors)

    def save(self, directory=config.INDEX_DIR):
        d = Path(directory)
        d.mkdir(parents=True, exist_ok=True)
        np.save(d / "vectors.npy", self.vectors)
        (d / "chunks.json").write_text(json.dumps([c.to_dict() for c in self.chunks]))

    @classmethod
    def load(cls, directory=config.INDEX_DIR):
        d = Path(directory)
        if not (d / "vectors.npy").exists():
            raise FileNotFoundError(f"No index in {d}. Run `index` first.")
        chunks = [Chunk(**c) for c in json.loads((d / "chunks.json").read_text())]
        return cls(chunks, np.load(d / "vectors.npy"))

    def search(self, query, k=config.TOP_K):
        q = embed([query])[0]
        scores = self.vectors @ q  # cosine similarity (vectors are normalized)
        # Small keyword boost: exact identifiers matter a lot in code
        terms = [t.lower() for t in query.split() if len(t) > 3]
        if terms:
            boost = np.array([
                sum(t in (c.text.lower() + c.path.lower()) for t in terms)
                for c in self.chunks
            ], dtype=np.float32)
            scores = scores + 0.03 * boost
        top = np.argsort(-scores)[:k]
        return [(self.chunks[i], float(scores[i])) for i in top]
