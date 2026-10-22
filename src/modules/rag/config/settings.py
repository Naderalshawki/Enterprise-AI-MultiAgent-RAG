"""Configuration settings for the RAG module."""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Determine project root dynamically across OS (Windows, Linux, macOS, Docker)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Load .env file from project root or current working dir if available
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


class RAGSettings(BaseModel):
    """Configuration options for chunking, vector store, and search."""

    # Paths (Cross-platform and docker-ready)
    base_data_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("RAG_DATA_DIR", str(PROJECT_ROOT / "data")))
    )
    upload_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("RAG_UPLOAD_DIR", str(PROJECT_ROOT / "data" / "uploads")))
    )
    chroma_persist_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("RAG_CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "data" / "vector_storage")))
    )

    # Chunking parameters
    chunk_size: int = Field(default=int(os.getenv("RAG_CHUNK_SIZE", "500")), description="Character count per chunk")
    chunk_overlap: int = Field(default=int(os.getenv("RAG_CHUNK_OVERLAP", "50")), description="Overlap characters between chunks")

    # Retrieval parameters
    top_k: int = Field(default=int(os.getenv("RAG_TOP_K", "5")), description="Number of results to retrieve")
    enable_hybrid_search: bool = Field(default=os.getenv("RAG_ENABLE_HYBRID_SEARCH", "true").lower() in ("true", "1"), description="Combine vector & BM25 search")
    enable_reranking: bool = Field(default=os.getenv("RAG_ENABLE_RERANKING", "true").lower() in ("true", "1"), description="Rerank candidates with cross-encoder")
    chroma_collection_name: str = os.getenv("RAG_COLLECTION_NAME", "document_intelligence")
    max_upload_bytes: int = Field(default=int(os.getenv("RAG_MAX_UPLOAD_BYTES", str(100 * 1024 * 1024))))
    api_key: str = os.getenv("RAG_API_KEY", "")
    allowed_origins: str = os.getenv("RAG_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    embedding_model: str = os.getenv("RAG_EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
    rerank_model: str = os.getenv("RAG_RERANK_MODEL", "ms-marco-TinyBERT-L-2-v2")
    require_trusted_context: bool = Field(
        default=os.getenv("RAG_REQUIRE_TRUSTED_CONTEXT", "false").lower() in ("true", "1", "yes")
    )


# Global singleton settings instance
rag_settings = RAGSettings()
