"""Composite document loader that auto-routes files to their respective loaders."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.modules.rag.domain.entities import Document
from src.modules.rag.domain.exceptions import UnsupportedDocumentException
from src.modules.rag.domain.interfaces import IDocumentLoader
from src.modules.rag.infrastructure.loaders.docx_loader import DocxLoader
from src.modules.rag.infrastructure.loaders.excel_loader import ExcelLoader
from src.modules.rag.infrastructure.loaders.pdf_loader import PDFLoader
from src.modules.rag.infrastructure.loaders.text_loader import TextLoader


class CompositeDocumentLoader(IDocumentLoader):
    """Factory and registry that automatically selects the appropriate loader based on file extension."""

    def __init__(self, loaders: Optional[List[IDocumentLoader]] = None):
        self.loaders: List[IDocumentLoader] = loaders or [
            PDFLoader(),
            DocxLoader(),
            ExcelLoader(),
            TextLoader(),
        ]

    def can_handle(self, extension: str) -> bool:
        clean_ext = extension.lower().lstrip(".")
        return any(loader.can_handle(clean_ext) for loader in self.loaders)

    def load(
        self,
        file_path: str,
        tenant_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Document:
        ext = Path(file_path).suffix.lower().lstrip(".")

        for loader in self.loaders:
            if loader.can_handle(ext):
                return loader.load(file_path, tenant_id=tenant_id, **kwargs)

        raise UnsupportedDocumentException(
            f"صيغة الملف غير مدعومة: '{ext}'. الصيغ المدعومة هي: pdf, docx, txt, md, csv, xlsx"
        )
