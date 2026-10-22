"""Unit tests for RecursiveChunker."""

import pytest
from src.modules.rag.domain.entities import Document
from src.modules.rag.domain.value_objects import DocumentType
from src.modules.rag.infrastructure.chunkers.recursive_chunker import RecursiveChunker


def test_chunker_basic_split():
    text = (
        "الذكاء الاصطناعي هو فرع من فروع علوم الحاسوب.\n\n"
        "يهدف إلى تطوير أنظمة قادرة على محاكاة القدرات الذهنية البشرية.\n\n"
        "من أهم مجالاته معالجة اللغات الطبيعية وتعلم الآلة والرؤية الحاسوبية."
    )
    doc = Document(
        name="ai_intro.txt",
        text_content=text,
        doc_type=DocumentType.TXT,
    )

    chunker = RecursiveChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.split(doc)

    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk.text) <= 120  # Allows slight margin for sentence boundary
        assert chunk.document_id == doc.id
        assert chunk.document_name == doc.name


def test_chunker_page_aware():
    pages = [
        {"page_number": 1, "text": "هذه نصوص الصفحة الأولى من التقرير السنوي."},
        {"page_number": 2, "text": "هذه نصوص الصفحة الثانية وتتضمن الجداول المالية والمؤشرات."},
    ]
    doc = Document(
        name="annual_report.pdf",
        text_content="...",
        doc_type=DocumentType.PDF,
        metadata={"pages": pages},
    )

    chunker = RecursiveChunker(chunk_size=150, chunk_overlap=20)
    chunks = chunker.split(doc)

    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert "الصفحة الأولى" in chunks[0].text
    assert chunks[1].page_number == 2
    assert "الصفحة الثانية" in chunks[1].text


if __name__ == "__main__":
    pytest.main([__file__])
