"""Base document loader class extending IDocumentLoader interface."""

from abc import ABC
from pathlib import Path
from typing import Set

from src.modules.rag.domain.entities import Document
from src.modules.rag.domain.exceptions import DocumentParsingException
from src.modules.rag.domain.interfaces import IDocumentLoader
from src.modules.rag.domain.value_objects import DocumentType


class BaseDocumentLoader(IDocumentLoader, ABC):
    """Common functionality for all specific document loaders."""

    supported_extensions: Set[str] = set()

    def can_handle(self, extension: str) -> bool:
        clean_ext = extension.lower().lstrip(".")
        return clean_ext in self.supported_extensions

    def validate_file(self, file_path: str) -> Path:
        path = Path(file_path)
        if not path.exists():
            raise DocumentParsingException(f"الملف غير موجود: {file_path}")
        if not path.is_file():
            raise DocumentParsingException(f"المسار ليس ملفاً صالحاً: {file_path}")
        return path

    def create_document(
        self,
        path: Path,
        content: str,
        doc_type: DocumentType,
        metadata: dict | None = None,
        tenant_id: str | None = None,
        file_name: str | None = None,
    ) -> Document:
        doc_name = file_name or (metadata.get("file_name") if metadata else None) or path.name
        meta = metadata or {}
        meta.setdefault("file_name", doc_name)
        meta.setdefault("file_size_bytes", path.stat().st_size)
        meta.setdefault("file_extension", path.suffix)

        return Document(
            name=doc_name,
            file_path=str(path.resolve()),
            doc_type=doc_type,
            text_content=content,
            metadata=meta,
            tenant_id=tenant_id,
        )
