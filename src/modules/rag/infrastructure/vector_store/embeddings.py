"""Embedding generators with multilingual Arabic-first defaults."""

import os
from typing import List
import chromadb.utils.embedding_functions as ef

from src.modules.rag.domain.interfaces import IEmbeddingGenerator


class OfflineFastEmbeddingFunction:
    """Zero-download deterministic embedding function for 100% offline local testing."""

    def __init__(self, dim: int = 384):
        self.dim = dim

    def __call__(self, input: List[str]) -> List[List[float]]:
        import hashlib
        import numpy as np

        vectors = []
        for text in input:
            vec = np.zeros(self.dim, dtype=np.float32)
            words = (text or "").split()
            if not words:
                vectors.append(vec.tolist())
                continue
            for word in words:
                h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
                idx = h % self.dim
                sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
                vec[idx] += sign
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec.tolist())
        return vectors


class ChromaDefaultEmbeddingGenerator(IEmbeddingGenerator):
    """Local multilingual embeddings with an ultra-safe offline fallback."""

    def __init__(self):
        from src.modules.rag.config.settings import rag_settings

        model_name = getattr(rag_settings, "embedding_model", None) or os.getenv(
            "RAG_EMBEDDING_MODEL", "intfloat/multilingual-e5-small"
        )
        try:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

            self._func = SentenceTransformerEmbeddingFunction(model_name=model_name)
            self.model_name = model_name
        except Exception:
            try:
                self._func = ef.DefaultEmbeddingFunction()
                self.model_name = "chroma-default-fallback"
            except Exception:
                # 100% offline fallback when no internet is available
                self._func = OfflineFastEmbeddingFunction()
                self.model_name = "offline-local-generator"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = self._func(texts)
        # Convert numpy or raw array to list of floats
        return [list(map(float, vec)) for vec in embeddings]

    def embed_query(self, query: str) -> List[float]:
        results = self._func([query])
        return list(map(float, results[0]))


class ExternalEmbeddingGenerator(IEmbeddingGenerator):
    """Bridge generator to use external embeddings (such as colleague's LLM module or custom APIs)."""

    def __init__(self, embed_func):
        self._embed_func = embed_func

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed_func(texts)

    def embed_query(self, query: str) -> List[float]:
        return self._embed_func([query])[0]
