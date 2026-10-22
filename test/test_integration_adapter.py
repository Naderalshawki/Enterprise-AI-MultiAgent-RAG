"""Tests for integration adapters and universal RAG client."""

from src.modules.rag import (
    IngestionService,
    RAGToolAdapter,
    RetrievalService,
    rag_tool_instance,
)
from src.modules.rag.client import RAGClient
from src.modules.rag.infrastructure.vector_store.chroma_store import ChromaVectorStore


def test_rag_tool_adapter_in_process():
    # Setup isolated in-memory vector store
    test_store = ChromaVectorStore(collection_name="test_tool_adapter", in_memory=True)
    ingest_svc = IngestionService(vector_store=test_store)

    # Ingest dummy knowledge
    ingest_svc.ingest_text(
        text="ساعات الدوام الرسمي تبدأ من الساعة 8 صباحاً حتى 4 مساءً.",
        document_name="working_hours.txt",
        tenant_id="tenant_main",
    )

    retrieval_svc = RetrievalService(
        vector_store=test_store,
        bm25_searcher=ingest_svc.bm25_searcher,
    )

    adapter = RAGToolAdapter(retrieval_service=retrieval_svc)

    # Verify agent search output format
    res = adapter.search_knowledge(
        query="متى يبدأ الدوام؟",
        top_k=2,
        tenant_id="tenant_main",
    )

    assert "query" in res
    assert "context" in res
    assert "citations" in res
    assert "total_found" in res
    assert res["total_found"] >= 1
    assert "8 صباحاً" in res["context"]
    assert res["citations"][0]["document_name"] == "working_hours.txt"


def test_agent_tool_schema_definition():
    schema = RAGToolAdapter.get_tool_definition()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "search_knowledge_base"
    assert "query" in schema["function"]["parameters"]["properties"]
    assert "tenant_id" in schema["function"]["parameters"]["properties"]
