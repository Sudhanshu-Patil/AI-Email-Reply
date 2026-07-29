"""Finding the past emails most worth showing the model.

Hybrid of dense embeddings and TF-IDF, because the two fail differently. Embeddings catch
"our sync stopped overnight" ≈ "the connector hasn't run since 2am" where no words are
shared. TF-IDF catches the exact identifiers and product nouns — "EG-400", "reverse
charge", "RMA" — that embeddings smooth away precisely because they are rare.

A same-category bonus is applied on top. Category is a strong prior for *which reply
template applies*, and cheap: a billing question retrieving a support exemplar is a worse
prompt than a slightly-less-similar billing one.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .embeddings import Embedder, get_embedder


@dataclass
class Retrieved:
    record: dict
    score: float
    dense: float
    sparse: float
    category_bonus: float

    @property
    def id(self) -> str:
        return self.record["id"]


def email_text(record: dict) -> str:
    """The representation we match on: subject plus body of the *incoming* email."""
    inc = record["incoming"]
    ctx = record.get("thread_context") or ""
    return f"{inc['subject']}\n{inc['body']}\n{ctx}".strip()


class Retriever:
    """Ranks a training pool against a new incoming email.

    Args:
        pool: training records to retrieve from.
        alpha: weight on the dense score; ``1 - alpha`` goes to TF-IDF.
        category_bonus: added to the blended score when categories match.
    """

    def __init__(
        self,
        pool: list[dict],
        embedder: Embedder | None = None,
        alpha: float = 0.65,
        category_bonus: float = 0.08,
    ):
        if not pool:
            raise ValueError("Retriever needs a non-empty pool.")
        self.pool = pool
        self.alpha = alpha
        self.category_bonus = category_bonus
        self.embedder = embedder or get_embedder()

        self.texts = [email_text(r) for r in pool]

        # Char n-grams alongside words: robust to "EG-400" vs "EG400" and to typos, which
        # is most of what identifier matching in real mail runs into.
        self._word_vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2),
                                         min_df=1, stop_words="english")
        self._char_vec = TfidfVectorizer(sublinear_tf=True, analyzer="char_wb",
                                         ngram_range=(3, 5), min_df=1)
        self._word_mat = self._word_vec.fit_transform(self.texts)
        self._char_mat = self._char_vec.fit_transform(self.texts)

        self.embedder.fit_background(self.texts)
        self._dense = self.embedder.encode(self.texts)

    def _sparse_scores(self, query: str) -> np.ndarray:
        qw = self._word_vec.transform([query])
        qc = self._char_vec.transform([query])
        word = np.asarray((self._word_mat @ qw.T).todense()).ravel()
        char = np.asarray((self._char_mat @ qc.T).todense()).ravel()
        return 0.6 * word + 0.4 * char

    def _dense_scores(self, query: str) -> np.ndarray:
        qv = self.embedder.encode([query])
        if qv.shape[1] != self._dense.shape[1]:  # TF-IDF fallback refit mid-flight
            return np.zeros(len(self.pool), dtype=np.float32)
        return (self._dense @ qv.T).ravel()

    def retrieve(self, incoming: dict, k: int = 3, category: str | None = None,
                 exclude_ids: set[str] | None = None) -> list[Retrieved]:
        query = f"{incoming.get('subject','')}\n{incoming.get('body','')}".strip()
        dense = self._dense_scores(query)
        sparse = self._sparse_scores(query)

        # Min-max each channel before blending: raw cosine and raw TF-IDF live on different
        # scales, so a fixed alpha over unnormalised scores would silently favour one.
        blended = self.alpha * _minmax(dense) + (1 - self.alpha) * _minmax(sparse)

        bonus = np.zeros(len(self.pool), dtype=np.float32)
        if category:
            for i, rec in enumerate(self.pool):
                if rec["category"] == category:
                    bonus[i] = self.category_bonus
        total = blended + bonus

        exclude = exclude_ids or set()
        order = np.argsort(-total)
        out: list[Retrieved] = []
        for i in order:
            rec = self.pool[int(i)]
            if rec["id"] in exclude:
                continue
            out.append(Retrieved(rec, float(total[i]), float(dense[i]),
                                 float(sparse[i]), float(bonus[i])))
            if len(out) >= k:
                break
        return out


def _minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = float(x.min()), float(x.max())
    if hi - lo < 1e-9:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)
