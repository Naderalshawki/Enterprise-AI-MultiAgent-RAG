"""Text and Markdown document loader with multi-encoding fallback."""

from pathlib import Path
from typing import Any, Optional

from src.modules.rag.domain.entities import Document
from src.modules.rag.domain.exceptions import DocumentParsingException
from src.modules.rag.domain.value_objects import DocumentType
from src.modules.rag.infrastructure.loaders.base_loader import BaseDocumentLoader


class TextLoader(BaseDocumentLoader):
    """Extracts raw text from .txt, .md, and plaintext files."""

    supported_extensions = {"txt", "md", "markdown", "log", "json"}

    def load(
        self,
        file_path: str,
        tenant_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Document:
        path = self.validate_file(file_path)

        content = ""
        used_encoding = ""

        # Try common encodings, particularly UTF-8 and Arabic Windows (cp1256)
        for enc in ["utf-8-sig", "utf-8", "cp1256", "latin-1"]:
            try:
                with open(path, "r", encoding=enc) as f:
                    content = f.read()
                used_encoding = enc
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if not content and path.stat().st_size > 0:
            raise DocumentParsingException(
                f"تعذر قراءة ترميز ملف النص: {path.name}"
            )

        ext = path.suffix.lower().lstrip(".")
        doc_type = DocumentType.MARKDOWN if ext in {"md", "markdown"} else DocumentType.TXT

        metadata = {
            "encoding": used_encoding,
            "char_count": len(content),
            "lines_count": len(content.splitlines()),
        }

        return self.create_document(
            path=path,
            content=content,
            doc_type=doc_type,
            metadata=metadata,
            tenant_id=tenant_id,
        )
