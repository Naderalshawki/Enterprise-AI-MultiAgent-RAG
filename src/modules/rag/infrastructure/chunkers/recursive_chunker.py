"""Smart recursive text chunker supporting multilingual punctuation and page awareness."""

from typing import List, Optional

from src.modules.rag.domain.entities import Chunk, Document
from src.modules.rag.infrastructure.chunkers.base_chunker import BaseChunker


class RecursiveChunker(BaseChunker):
    """Recursively splits text into semantically cohesive chunks using hierarchical separators."""

    DEFAULT_SEPARATORS = [
        "\n\n",   # فقرات كاملة
        "\n",     # أسطر
        ". ",     # جمل إنجليزية/لاتينية
        ".\n",
        "؟ ",     # علامات استفهام عربية
        "? ",
        "! ",     # علامات تعجب
        "؛ ",     # فاصلة منقوطة عربية
        "; ",
        "، ",     # فاصلة عربية
        ", ",     # فاصلة إنجليزية
        " ",      # مسافة بين الكلمات
        "",       # أحرف فردية كخيار أخير
    ]

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
    ):
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.separators = separators or self.DEFAULT_SEPARATORS

    def split(self, document: Document) -> List[Chunk]:
        """Split a document into sequential chunks, preserving page numbers if present."""
        chunks: List[Chunk] = []
        chunk_index = 0

        # Check if the document has page-level metadata (e.g. from PDFLoader)
        pages_metadata = document.metadata.get("pages")

        if pages_metadata and isinstance(pages_metadata, list):
            # Page-aware chunking: process each page individually to keep accurate citations
            for page_info in pages_metadata:
                page_number = page_info.get("page_number")
                page_text = page_info.get("text", "")
                if not page_text.strip():
                    continue

                page_splits = self._split_text(page_text, self.separators)
                for split_text in page_splits:
                    if split_text.strip():
                        chunks.append(
                            self.create_chunk(
                                document=document,
                                text=split_text,
                                chunk_index=chunk_index,
                                page_number=page_number,
                            )
                        )
                        chunk_index += 1
        else:
            # Document-level chunking
            raw_splits = self._split_text(document.text_content, self.separators)
            for split_text in raw_splits:
                if split_text.strip():
                    chunks.append(
                        self.create_chunk(
                            document=document,
                            text=split_text,
                            chunk_index=chunk_index,
                            page_number=None,
                        )
                    )
                    chunk_index += 1

        return chunks

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursive splitting helper function."""
        final_chunks: List[str] = []

        if not text:
            return final_chunks

        # Find the appropriate separator
        separator = separators[-1]
        new_separators: List[str] = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break

        # Split using the chosen separator
        splits = self._split_by_separator(text, separator)

        # Merge pieces into target chunk_size respecting chunk_overlap
        good_splits: List[str] = []
        current_doc: List[str] = []
        total_len = 0

        for s in splits:
            s_len = len(s)
            if total_len + s_len + (len(separator) if current_doc else 0) <= self.chunk_size:
                current_doc.append(s)
                total_len += s_len + (len(separator) if len(current_doc) > 1 else 0)
            else:
                if current_doc:
                    merged = separator.join(current_doc).strip()
                    if merged:
                        good_splits.append(merged)

                    # Handle overlap: keep trailing segments that fit within chunk_overlap
                    overlap_doc: List[str] = []
                    overlap_len = 0
                    for prev_s in reversed(current_doc):
                        prev_len = len(prev_s) + (len(separator) if overlap_doc else 0)
                        if overlap_len + prev_len <= self.chunk_overlap:
                            overlap_doc.insert(0, prev_s)
                            overlap_len += prev_len
                        else:
                            break

                    current_doc = overlap_doc
                    total_len = overlap_len

                # If a single piece is still larger than chunk_size, split it with next separator
                if s_len > self.chunk_size:
                    if new_separators:
                        sub_splits = self._split_text(s, new_separators)
                        good_splits.extend(sub_splits)
                    else:
                        # Hard character slice if no separators remain
                        for idx in range(0, s_len, self.chunk_size - self.chunk_overlap):
                            piece = s[idx : idx + self.chunk_size]
                            if piece.strip():
                                good_splits.append(piece.strip())
                else:
                    current_doc.append(s)
                    total_len += s_len + (len(separator) if len(current_doc) > 1 else 0)

        if current_doc:
            merged = separator.join(current_doc).strip()
            if merged:
                good_splits.append(merged)

        return good_splits

    def _split_by_separator(self, text: str, separator: str) -> List[str]:
        if separator:
            return [t for t in text.split(separator) if t]
        return list(text)
