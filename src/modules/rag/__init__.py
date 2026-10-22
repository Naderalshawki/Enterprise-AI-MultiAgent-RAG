"""RAG & Document Intelligence Module (Track 2)."""

from src.modules.rag.application.dtos import (
    CitationDTO,
    IngestDocumentDTO,
    IngestResultDTO,
    QueryInputDTO,
    QueryOutputDTO,
)
from src.modules.rag.application.ingestion_service import IngestionService
from src.modules.rag.application.retrieval_service import RetrievalService
from src.modules.rag.client import RAGClient
from src.modules.rag.config.settings import rag_settings
from src.modules.rag.rag_tool_adapter import RAGToolAdapter, rag_tool_instance

__all__ = [
    "IngestionService",
    "RetrievalService",
    "RAGToolAdapter",
    "rag_tool_instance",
    "RAGClient",
    "rag_settings",
    "IngestDocumentDTO",
    "IngestResultDTO",
    "QueryInputDTO",
    "QueryOutputDTO",
    "CitationDTO",
]

