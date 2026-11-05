# # """Retrieval service providing hybrid search, reranking, and citation formatting."""

# # from typing import List, Optional

# # from src.modules.rag.application.dtos import CitationDTO, QueryInputDTO, QueryOutputDTO
# # from src.modules.rag.config.settings import rag_settings
# # from src.modules.rag.domain.entities import SearchResult
# # from src.modules.rag.domain.interfaces import IReranker, IVectorStore
# # from src.modules.rag.infrastructure.hybrid_search.bm25_searcher import BM25Searcher
# # from src.modules.rag.infrastructure.hybrid_search.rrf_ranker import RRFRanker
# # from src.modules.rag.infrastructure.reranker.flashrank_reranker import FlashRankReranker
# # from src.modules.rag.infrastructure.vector_store.chroma_store import ChromaVectorStore


# # class RetrievalService:
# #     """Orchestrates query retrieval: Dense Vector + BM25 Sparse -> RRF Fusion -> Rerank -> Prompt Context & Citations."""

# #     def __init__(
# #         self,
# #         vector_store: Optional[IVectorStore] = None,
# #         bm25_searcher: Optional[BM25Searcher] = None,
# #         rrf_ranker: Optional[RRFRanker] = None,
# #         reranker: Optional[IReranker] = None,
# #     ):
# #         self.vector_store = vector_store or ChromaVectorStore()
# #         self.bm25_searcher = bm25_searcher or BM25Searcher()
# #         self.rrf_ranker = rrf_ranker or RRFRanker()
# #         self.reranker = reranker or FlashRankReranker()

# #     def retrieve(self, dto: QueryInputDTO) -> QueryOutputDTO:
# #         """Execute full retrieval lifecycle and return formatted context and citations."""
# #         query = dto.query.strip()
# #         top_k = dto.top_k or rag_settings.top_k

# #         if not query:
# #             return QueryOutputDTO(query=query, context="", citations=[], total_retrieved=0)

# #         # Build filter dictionary if tenant_id or custom filters are specified
# #         filters = dict(dto.filters or {})
# #         if dto.tenant_id:
# #             filters["tenant_id"] = dto.tenant_id

# #         # 1. Dense vector search
# #         # Over-fetch slightly (2x top_k) for better reranker selection
# #         fetch_k = max(top_k * 2, 10)
# #         dense_candidates: List[SearchResult] = []
# #         try:
# #             if hasattr(self.vector_store, "search_by_text"):
# #                 dense_candidates = self.vector_store.search_by_text(
# #                     query_text=query,
# #                     top_k=fetch_k,
# #                     filters=filters if filters else None,
# #                 )
# #         except Exception:
# #             dense_candidates = []

# #         # 2. Sparse BM25 keyword search (if hybrid search is enabled)
# #         candidates: List[SearchResult] = dense_candidates
# #         if dto.enable_hybrid:
# #             sparse_candidates = self.bm25_searcher.search(
# #                 query=query,
# #                 top_k=fetch_k,
# #                 filters=filters if filters else None,
# #             )
# #             if sparse_candidates and dense_candidates:
# #                 # Merge using Reciprocal Rank Fusion
# #                 candidates = self.rrf_ranker.fuse(
# #                     dense_results=dense_candidates,
# #                     sparse_results=sparse_candidates,
# #                     top_k=fetch_k,
# #                 )
# #             elif sparse_candidates and not dense_candidates:
# #                 candidates = sparse_candidates

# #         # 3. Reranking using Cross-Encoder / FlashRank (only if enabled in settings and requested)
# #         if dto.enable_rerank and rag_settings.enable_reranking and candidates:
# #             candidates = self.reranker.rerank(
# #                 query=query,
# #                 candidates=candidates,
# #                 top_k=top_k,
# #             )
# #         else:
# #             candidates = candidates[:top_k]

# #         # 4. Format context for LLM prompt and assemble citations
# #         context_parts: List[str] = []
# #         citations: List[CitationDTO] = []

# #         for i, res in enumerate(candidates, start=1):
# #             chunk = res.chunk
# #             page_str = f" | صفحة: {chunk.page_number}" if chunk.page_number else ""
# #             header = f"[مصدر {i}: {chunk.document_name}{page_str}]"
# #             context_parts.append(f"{header}\n{chunk.text}")

# #             citations.append(
# #                 CitationDTO(
# #                     document_id=chunk.document_id,
# #                     document_name=chunk.document_name,
# #                     chunk_id=chunk.id,
# #                     page=chunk.page_number,
# #                     score=res.score,
# #                     snippet=chunk.text[:200] + ("..." if len(chunk.text) > 200 else ""),
# #                 )
# #             )

# #         full_context = "\n\n---\n\n".join(context_parts)

# #         return QueryOutputDTO(
# #             query=query,
# #             context=full_context,
# #             citations=citations,
# #             total_retrieved=len(candidates),
# #         )













# """Retrieval service providing hybrid search, reranking, and citation formatting."""

# import logging
# from typing import List, Optional

# from src.modules.rag.application.dtos import CitationDTO, QueryInputDTO, QueryOutputDTO
# from src.modules.rag.config.settings import rag_settings
# from src.modules.rag.domain.entities import SearchResult
# from src.modules.rag.domain.interfaces import IReranker, IVectorStore
# from src.modules.rag.infrastructure.hybrid_search.bm25_searcher import BM25Searcher
# from src.modules.rag.infrastructure.hybrid_search.rrf_ranker import RRFRanker
# from src.modules.rag.infrastructure.reranker.flashrank_reranker import FlashRankReranker
# from src.modules.rag.infrastructure.vector_store.chroma_store import ChromaVectorStore

# logger = logging.getLogger(__name__)


# class RetrievalService:
#     def __init__(
#         self,
#         vector_store: Optional[IVectorStore] = None,
#         bm25_searcher: Optional[BM25Searcher] = None,
#         rrf_ranker: Optional[RRFRanker] = None,
#         reranker: Optional[IReranker] = None,
#     ):
#         self.vector_store = vector_store or ChromaVectorStore()
#         self.bm25_searcher = bm25_searcher or BM25Searcher()
#         self.rrf_ranker = rrf_ranker or RRFRanker()
#         self.reranker = reranker or FlashRankReranker()

#     def retrieve(self, dto: QueryInputDTO) -> QueryOutputDTO:
#         query = dto.query.strip()
#         top_k = dto.top_k or rag_settings.top_k

#         if not query:
#             return QueryOutputDTO(query=query, context="", citations=[], total_retrieved=0)

#         filters = dict(dto.filters or {})
#         if dto.tenant_id:
#             filters["tenant_id"] = dto.tenant_id

#         fetch_k = max(top_k * 2, 10)
#         candidates: List[SearchResult] = []

#         # 1. المحاولة الأولى: البحث المفتاحي (BM25)
#         try:
#             candidates = self.bm25_searcher.search(
#                 query=query,
#                 top_k=fetch_k,
#                 filters=filters if filters else None,
#             )
#             logger.info(f"[RetrievalService] BM25 search found {len(candidates)} candidates.")
#         except Exception as exc:
#             logger.warning(f"[RetrievalService] BM25 search failed: {exc}.")

#         # 2. خطة الإنقاذ (إذا فشل BM25، نجبر النظام على سحب كل الملفات من ChromaDB)
#         if not candidates:
#             logger.warning("[RetrievalService] BM25 returned 0. Forcing fallback to fetch ALL chunks from DB.")
#             try:
#                 if hasattr(self.vector_store, "get_all_chunks"):
#                     all_chunks = self.vector_store.get_all_chunks(tenant_id=dto.tenant_id)
#                     candidates = [
#                         SearchResult(chunk=chunk, score=1.0, retrieval_method="forced_fallback")
#                         for chunk in all_chunks
#                     ]
#                     logger.info(f"[RetrievalService] Forced fallback retrieved {len(candidates)} chunks.")
#             except Exception as exc:
#                 logger.error(f"[RetrievalService] Fallback failed: {exc}")

#         # 3. الترتيب النهائي
#         if dto.enable_rerank and rag_settings.enable_reranking and candidates:
#             try:
#                 candidates = self.reranker.rerank(query=query, candidates=candidates, top_k=top_k)
#             except Exception:
#                 candidates = candidates[:top_k]
#         else:
#             candidates = candidates[:top_k]

#         # 4. التجهيز للعقل
#         context_parts: List[str] = []
#         citations: List[CitationDTO] = []

#         for i, res in enumerate(candidates, start=1):
#             chunk = res.chunk
#             page_str = f" | صفحة: {chunk.page_number}" if chunk.page_number else ""
#             header = f"[مصدر {i}: {chunk.document_name}{page_str}]"
#             context_parts.append(f"{header}\n{chunk.text}")

#             citations.append(
#                 CitationDTO(
#                     document_id=chunk.document_id,
#                     document_name=chunk.document_name,
#                     chunk_id=chunk.id,
#                     page=chunk.page_number,
#                     score=res.score,
#                     snippet=chunk.text[:200] + ("..." if len(chunk.text) > 200 else ""),
#                 )
#             )

#         full_context = "\n\n---\n\n".join(context_parts)

#         return QueryOutputDTO(
#             query=query,
#             context=full_context,
#             citations=citations,
#             total_retrieved=len(candidates),
#         )










"""Retrieval service providing robust hybrid search (Dense Vector + Sparse BM25), reranking, and citation formatting."""

import logging
from typing import List, Optional, Dict, Any

from src.modules.rag.application.dtos import CitationDTO, QueryInputDTO, QueryOutputDTO
from src.modules.rag.config.settings import rag_settings
from src.modules.rag.domain.entities import SearchResult
from src.modules.rag.domain.interfaces import IReranker, IVectorStore
from src.modules.rag.infrastructure.hybrid_search.bm25_searcher import BM25Searcher
from src.modules.rag.infrastructure.hybrid_search.rrf_ranker import RRFRanker
from src.modules.rag.infrastructure.reranker.flashrank_reranker import FlashRankReranker
from src.modules.rag.infrastructure.vector_store.chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Orchestrates robust query retrieval for Enterprise BI:
    Dense Vector (Semantic) + BM25 Sparse (Keyword) -> RRF Fusion -> Rerank -> Prompt Context.
    """

    def __init__(
        self,
        vector_store: Optional[IVectorStore] = None,
        bm25_searcher: Optional[BM25Searcher] = None,
        rrf_ranker: Optional[RRFRanker] = None,
        reranker: Optional[IReranker] = None,
    ):
        self.vector_store = vector_store or ChromaVectorStore()
        self.bm25_searcher = bm25_searcher or BM25Searcher()
        self.rrf_ranker = rrf_ranker or RRFRanker()
        self.reranker = reranker or FlashRankReranker()

    def retrieve(self, dto: QueryInputDTO) -> QueryOutputDTO:
        """Execute hybrid retrieval lifecycle and return formatted context and citations."""
        query = dto.query.strip()
        top_k = dto.top_k or rag_settings.top_k

        if not query:
            return QueryOutputDTO(query=query, context="", citations=[], total_retrieved=0)

        # تجهيز الفلاتر (مثل tenant_id)
        filters: Dict[str, Any] = dict(dto.filters or {})
        if dto.tenant_id:
            filters["tenant_id"] = dto.tenant_id

        fetch_k = max(top_k * 2, 10)
        dense_candidates: List[SearchResult] = []
        sparse_candidates: List[SearchResult] = []

        # -----------------------------------------------------------
        # 1. البحث الدلالي الذكي (Dense Vector Search)
        # -----------------------------------------------------------
        try:
            if hasattr(self.vector_store, "search_by_text"):
                dense_candidates = self.vector_store.search_by_text(
                    query_text=query,
                    top_k=fetch_k,
                    filters=filters if filters else None,
                )
                logger.info(f"[RetrievalService] Vector search found {len(dense_candidates)} candidates.")
        except Exception as exc:
            logger.warning(f"[RetrievalService] Vector search failed: {exc}")

        # -----------------------------------------------------------
        # 2. البحث المفتاحي الدقيق (Sparse BM25 Search)
        # -----------------------------------------------------------
        if dto.enable_hybrid:
            try:
                sparse_candidates = self.bm25_searcher.search(
                    query=query,
                    top_k=fetch_k,
                    filters=filters if filters else None,
                )
                logger.info(f"[RetrievalService] BM25 search found {len(sparse_candidates)} candidates.")
            except Exception as exc:
                logger.warning(f"[RetrievalService] BM25 search failed: {exc}")

        # -----------------------------------------------------------
        # 3. الدمج الذكي (Hybrid Fusion)
        # -----------------------------------------------------------
        candidates: List[SearchResult] = dense_candidates

        if sparse_candidates and dense_candidates:
            logger.info("[RetrievalService] Merging Vector and BM25 results using RRF Fusion.")
            try:
                candidates = self.rrf_ranker.fuse(
                    dense_results=dense_candidates,
                    sparse_results=sparse_candidates,
                    top_k=fetch_k,
                )
            except Exception as exc:
                logger.warning(f"[RetrievalService] RRF Fusion failed, defaulting to dense candidates: {exc}")
                candidates = dense_candidates
        elif sparse_candidates and not dense_candidates:
            candidates = sparse_candidates

        # -----------------------------------------------------------
        # 4. خطة الإنقاذ الشاملة (Global Fallback) - إذا لم نجد أي شيء!
        # -----------------------------------------------------------
        if not candidates:
            logger.warning("[RetrievalService] Search returned 0 candidates. Forcing global fallback to fetch ALL chunks.")
            try:
                if hasattr(self.vector_store, "get_all_chunks"):
                    all_chunks = self.vector_store.get_all_chunks(tenant_id=dto.tenant_id)
                    candidates = [
                        SearchResult(chunk=chunk, score=1.0, retrieval_method="forced_fallback")
                        for chunk in all_chunks
                    ]
                    logger.info(f"[RetrievalService] Forced fallback retrieved {len(candidates)} chunks.")
            except Exception as exc:
                logger.error(f"[RetrievalService] Global Fallback failed: {exc}")

        # -----------------------------------------------------------
        # 5. إعادة الترتيب (Reranking) لضمان الدقة العالية
        # -----------------------------------------------------------
        if dto.enable_rerank and rag_settings.enable_reranking and candidates:
            try:
                candidates = self.reranker.rerank(query=query, candidates=candidates, top_k=top_k)
            except Exception as exc:
                logger.warning(f"[RetrievalService] Reranking failed, using original order: {exc}")
                candidates = candidates[:top_k]
        else:
            candidates = candidates[:top_k]

        # -----------------------------------------------------------
        # 6. التجهيز النهائي للإرسال إلى الـ LLM وتنسيق المصادر
        # -----------------------------------------------------------
        context_parts: List[str] = []
        citations: List[CitationDTO] = []

        for i, res in enumerate(candidates, start=1):
            chunk = res.chunk
            page_str = f" | صفحة: {chunk.page_number}" if chunk.page_number else ""
            header = f"[مصدر {i}: {chunk.document_name}{page_str}]"
            context_parts.append(f"{header}\n{chunk.text}")

            citations.append(
                CitationDTO(
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    chunk_id=chunk.id,
                    page=chunk.page_number,
                    score=res.score,
                    snippet=chunk.text[:200] + ("..." if len(chunk.text) > 200 else ""),
                )
            )

        full_context = "\n\n---\n\n".join(context_parts)

        return QueryOutputDTO(
            query=query,
            context=full_context,
            citations=citations,
            total_retrieved=len(candidates),
        )







