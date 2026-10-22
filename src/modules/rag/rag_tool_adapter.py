import os
from typing import Any, Dict, List, Optional
from src.modules.rag.application.dtos import QueryInputDTO
from src.modules.rag.application.retrieval_service import RetrievalService
from src.modules.rag.client import RAGClient


class RAGToolAdapter:
    """
    Universal adapter designed specifically for Person 1 (AI Core / multi_agent/tools/rag_tool.py)
    and query_router.py.
    
    Operates in two modes automatically:
    1. In-Process Mode: Directly invokes local RetrievalService (fastest, zero network overhead).
    2. Microservice Mode: If RAG_SERVICE_URL is set, or if run as an external agent, calls via HTTP.
    """

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        remote_url: Optional[str] = None,
    ):
        self.remote_url = remote_url or os.getenv("RAG_SERVICE_URL")
        self.client = RAGClient(base_url=self.remote_url) if self.remote_url else None
        self._retrieval_service = retrieval_service

    @property
    def retrieval_service(self) -> RetrievalService:
        if self._retrieval_service is None:
            self._retrieval_service = RetrievalService()
        return self._retrieval_service

    def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        tenant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes hybrid search + rerank and returns a clean dictionary for Agents.

        Returns:
            {
                "query": str,
                "context": str,        # Clean text passages ready for prompt injection
                "citations": List[dict], # Source citations with document_name, page, snippet, score
                "total_found": int
            }
        """
        # If remote mode is active, call via HTTP
        if self.client:
            try:
                res = self.client.query(
                    query=query,
                    top_k=top_k,
                    tenant_id=tenant_id,
                    filters=filters,
                    enable_hybrid=True,
                    enable_rerank=True,
                )
                return {
                    "query": res.get("query", query),
                    "context": res.get("context", ""),
                    "citations": res.get("citations", []),
                    "total_found": res.get("total_retrieved", 0),
                }
            except Exception as exc:
                # Never bypass remote authentication and tenant policy by
                # silently switching to a local index in production.
                raise RuntimeError("RAG service unavailable; local fallback is disabled") from exc

        # In-process local execution
        dto = QueryInputDTO(
            query=query,
            top_k=top_k,
            tenant_id=tenant_id,
            filters=filters,
            enable_hybrid=True,
            enable_rerank=True,
        )

        output = self.retrieval_service.retrieve(dto)

        return {
            "query": output.query,
            "context": output.context,
            "citations": [
                {
                    "document_name": c.document_name,
                    "page": c.page,
                    "score": c.score,
                    "chunk_id": c.chunk_id,
                    "snippet": c.snippet,
                }
                for c in output.citations
            ],
            "total_found": output.total_retrieved,
        }

    @staticmethod
    def get_tool_definition() -> Dict[str, Any]:
        """
        Standard OpenAI / Gemini function-calling tool schema ready to pass to LLM agents.
        """
        return {
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "استرجاع المعلومات والسياسات والحقائق الموثقة من مستندات وملفات المؤسسة عبر البحث الهجين.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "السؤال أو الاستعلام باللغة الطبيعية عن المستندات أو السياسات.",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "عدد المقاطع الأكثر صلة المراد استرجاعها (افتراضياً 5).",
                            "default": 5,
                        },
                        "tenant_id": {
                            "type": "string",
                            "description": "معرف المؤسسة أو المستأجر لفلترة الوثائق الخاصة به فقط.",
                        },
                    },
                    "required": ["query"],
                },
            },
        }


# Global singleton instance for quick import
rag_tool_instance = RAGToolAdapter()
