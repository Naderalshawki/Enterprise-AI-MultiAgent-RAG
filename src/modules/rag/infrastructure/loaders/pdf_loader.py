"""PDF document loader using PyMuPDF (fitz)."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.modules.rag.domain.entities import Document
from src.modules.rag.domain.exceptions import DocumentParsingException
from src.modules.rag.domain.value_objects import DocumentType
from src.modules.rag.infrastructure.loaders.base_loader import BaseDocumentLoader


class PDFLoader(BaseDocumentLoader):
    """Extracts text and page-level metadata from PDF files."""

    supported_extensions = {"pdf"}

    def load(
        self,
        file_path: str,
        tenant_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Document:
        path = self.validate_file(file_path)

        try:
            # pyrefly: ignore [missing-import]
            import fitz  # PyMuPDF
        except ImportError as e:
            raise DocumentParsingException(
                "حزمة PyMuPDF غير مثبتة. يرجى تثبيتها عبر: pip install pymupdf"
            ) from e

        try:
            doc = fitz.open(str(path))
            pages_text: List[Dict[str, Any]] = []
            full_text_parts: List[str] = []

            for page_idx in range(len(doc)):
                page = doc[page_idx]
                page_text = page.get_text() or ""
                cleaned = page_text.strip()
                if cleaned:
                    full_text_parts.append(cleaned)
                    pages_text.append({
                        "page_number": page_idx + 1,
                        "text": cleaned,
                        "char_count": len(cleaned),
                    })

            total_pages = len(doc)
            doc.close()

            metadata = {
                "total_pages": total_pages,
                "pages": pages_text,
            }

            full_content = "\n\n".join(full_text_parts)

            return self.create_document(
                path=path,
                content=full_content,
                doc_type=DocumentType.PDF,
                metadata=metadata,
                tenant_id=tenant_id,
            )
        except Exception as err:
            raise DocumentParsingException(f"فشل في معالجة ملف الـ PDF: {err}") from err
