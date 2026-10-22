"""Value objects for the RAG domain."""

from dataclasses import dataclass
from enum import Enum


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "md"
    CSV = "csv"
    EXCEL = "xlsx"
    UNKNOWN = "unknown"

    @classmethod
    def from_extension(cls, ext: str) -> "DocumentType":
        clean_ext = ext.lower().lstrip(".")
        mapping = {
            "pdf": cls.PDF,
            "docx": cls.DOCX,
            "doc": cls.DOCX,
            "txt": cls.TXT,
            "md": cls.MARKDOWN,
            "markdown": cls.MARKDOWN,
            "csv": cls.CSV,
            "xlsx": cls.EXCEL,
            "xls": cls.EXCEL,
        }
        return mapping.get(clean_ext, cls.UNKNOWN)


@dataclass(frozen=True)
class Citation:
    """Represents a verifiable source citation for retrieved context."""
    document_id: str
    document_name: str
    chunk_id: str
    page: int | None = None
    score: float = 0.0
    snippet: str = ""
