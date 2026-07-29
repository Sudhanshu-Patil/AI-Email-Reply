"""Sentence embeddings with a graceful, explicit fallback.

``all-MiniLM-L6-v2`` runs locally and needs no API key, which keeps the whole evaluation
pipeline free and offline. If the model genuinely cannot be loaded (no cache, no network)
we fall back to TF-IDF rather than crashing — but we say so loudly, because semantic
similarity computed from TF-IDF is a materially weaker signal and any report produced that
way should be read with that in mind.
"""

from __future__ import annotations

import threading
from functools import lru_cache

import numpy as np

DEFAULT_MODEL = "all-MiniLM-L6-v2"


class Embedder:
    """Encodes text to unit-norm vectors. Thread-safe, caches per process."""

    def __init__(self, model_name: str = DEFAULT_MODEL, allow_fallback: bool = True):
        self.model_name = model_name
        self.allow_fallback = allow_fallback
        self.backend = "uninitialised"
        self._model = None
        self._tfidf = None
        self._lock = threading.Lock()

    # -- loading ------------------------------------------------------------------

    def _ensure(self) -> None:
        if self.backend != "uninitialised":
            return
        with self._lock:
            if self.backend != "uninitialised":
                return
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
                self.backend = "sentence-transformers"
            except Exception as exc:  # noqa: BLE001
                if not self.allow_fallback:
                    raise
                print(
                    f"  [warn] could not load '{self.model_name}' ({type(exc).__name__}); "
                    f"falling back to TF-IDF. Semantic scores will be weaker."
                )
                from sklearn.feature_extraction.text import TfidfVectorizer

                self._tfidf = TfidfVectorizer(
                    sublinear_tf=True, ngram_range=(1, 2), min_df=1, stop_words="english"
                )
                self.backend = "tfidf-fallback"

    @property
    def is_semantic(self) -> bool:
        """False when running on the TF-IDF fallback — reports surface this."""
        self._ensure()
        return self.backend == "sentence-transformers"

    # -- encoding -----------------------------------------------------------------

    def encode(self, texts: list[str]) -> np.ndarray:
        self._ensure()
        if not texts:
            return np.zeros((0, 384), dtype=np.float32)

        if self.backend == "sentence-transformers":
            vecs = self._model.encode(
                texts, convert_to_numpy=True, normalize_embeddings=True,
                show_progress_bar=False,
            )
            return vecs.astype(np.float32)

        # TF-IDF fallback: fit lazily on whatever it has seen so far.
        try:
            mat = self._tfidf.transform(texts)
        except Exception:  # not fitted yet
            mat = self._tfidf.fit_transform(texts)
        arr = np.asarray(mat.todense(), dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        return arr / np.clip(norms, 1e-9, None)

    def fit_background(self, corpus: list[str]) -> None:
        """Give the TF-IDF fallback a vocabulary. No-op for the real model."""
        self._ensure()
        if self.backend == "tfidf-fallback" and corpus:
            self._tfidf.fit(corpus)

    # -- similarity ---------------------------------------------------------------

    def similarity_matrix(self, a: list[str], b: list[str]) -> np.ndarray:
        """Cosine similarity between every item in ``a`` and every item in ``b``."""
        if not a or not b:
            return np.zeros((len(a), len(b)), dtype=np.float32)
        if self.backend == "tfidf-fallback" or (
            self.backend == "uninitialised" and not self.is_semantic
        ):
            both = self.encode(list(a) + list(b))
            va, vb = both[: len(a)], both[len(a) :]
        else:
            va, vb = self.encode(list(a)), self.encode(list(b))
        return np.clip(va @ vb.T, -1.0, 1.0)

    def similarity(self, a: str, b: str) -> float:
        return float(self.similarity_matrix([a], [b])[0][0])


@lru_cache(maxsize=4)
def get_embedder(model_name: str = DEFAULT_MODEL) -> Embedder:
    """Process-wide singleton — loading the model repeatedly is the slowest thing here."""
    return Embedder(model_name)
