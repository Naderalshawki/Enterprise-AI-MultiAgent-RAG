"""BM25 keyword search with Arabic normalization and metadata filtering."""

import re
from typing import Any, Dict, List, Optional
from rank_bm25 import BM25Okapi

from src.modules.rag.domain.entities import Chunk, SearchResult


class BM25Searcher:
    """Keyword search engine supporting Arabic normalization and tenant isolation."""

    def __init__(self):
        self.chunks: List[Chunk] = []
        self.bm25: Optional[BM25Okapi] = None

    def fit(self, chunks: List[Chunk]) -> None:
        """Index a list of chunks for BM25 keyword matching."""
        self.chunks = chunks
        if not chunks:
            self.bm25 = None
            return

        tokenized_corpus = [self._tokenize(chunk.text) for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search indexed chunks for keyword relevance."""
        if not self.bm25 or not self.chunks:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        raw_scores = self.bm25.get_scores(tokens)

        allowed = [
            i for i, chunk in enumerate(self.chunks)
            if self._matches_filters(chunk, filters)
        ]
        ranked_indices = sorted(
            allowed,
            key=lambda i: raw_scores[i],
            reverse=True,
        )

        results: List[SearchResult] = []
        positive_scores = [raw_scores[i] for i in ranked_indices if raw_scores[i] > 0]
        max_score = max(positive_scores) if positive_scores else 1.0

        for idx in ranked_indices[:top_k]:
            score = raw_scores[idx]
            if score <= 0:
                continue

            # Normalize score to 0..1 scale
            normalized_score = round(float(score / max_score), 4)

            results.append(
                SearchResult(
                    chunk=self.chunks[idx],
                    score=normalized_score,
                    retrieval_method="sparse_bm25",
                )
            )

        return results

    @staticmethod
    def _matches_filters(chunk: Chunk, filters: Optional[Dict[str, Any]]) -> bool:
        if not filters:
            return True
        values = chunk.to_metadata()
        values.update(chunk.metadata or {})
        for key, expected in filters.items():
            if expected is None or expected == "":
                continue
            if values.get(key) != expected:
                return False
        return True

    def _tokenize(self, text: str) -> List[str]:
        """Normalize and tokenize text into words, removing punctuation."""
        if not text:
            return []

        # Normalize Arabic characters (أ, إ, آ -> ا)
        normalized = re.sub(r"[إأآا]", "ا", text)
        normalized = re.sub(r"[ةۀ]", "ه", normalized)
        normalized = re.sub(r"[ىی]", "ي", normalized)
        normalized = re.sub(r"[ؤئ]", "ء", normalized)
        # Remove Arabic diacritics (تنوين، حركات)
        normalized = re.sub(r"[\u064B-\u065F\u0670]", "", normalized)
        normalized = re.sub(r"ـ", "", normalized)

        # Split on whitespace and non-alphanumeric punctuation
        words = re.findall(r"\w+", normalized.lower())
        return words
