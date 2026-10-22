"""Tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
import pytest

from src.main import app

client = TestClient(app, headers={
    "X-Tenant-ID": "test_org",
    "X-User-ID": "test_user",
    "X-Roles": "admin",
})


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


def test_health_endpoint():
    response = client.get("/rag/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "total_indexed_chunks" in data


def test_query_endpoint():
    payload = {
        "query": "ما هي سياسة الإجازات السنوية؟",
        "top_k": 3,
        "enable_hybrid": True,
        "enable_rerank": True,
    }
    response = client.post("/rag/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "context" in data
    assert "citations" in data
    assert data["query"] == payload["query"]


def test_api_ingest_text_and_document_lifecycle():
    # 1. Ingest text
    ingest_payload = {
        "text": "سياسة العمل المرن تتيح للموظف العمل من المنزل يومين بالأسبوع.",
        "document_name": "api_test_doc.txt",
        "tenant_id": "test_org",
    }
    res = client.post("/rag/ingest-text", json=ingest_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    doc_id = data["document_id"]
    assert doc_id != ""

    # 2. List documents
    docs_res = client.get("/rag/documents")
    assert docs_res.status_code == 200
    docs_data = docs_res.json()
    assert docs_data["total_documents"] >= 1
    assert any(d["document_name"] == "api_test_doc.txt" for d in docs_data["documents"])

    # 3. Get document chunks
    chunks_res = client.get(f"/rag/document/{doc_id}/chunks")
    assert chunks_res.status_code == 200
    chunks_data = chunks_res.json()
    assert len(chunks_data) >= 1
    assert chunks_data[0]["document_id"] == doc_id

    # 4. Delete document
    del_res = client.delete(f"/rag/document/{doc_id}")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "success"


def test_api_upload_file():
    import io
    file_content = "سياسة الأمان الداخلي للمؤسسة وتنظيم الدخول والخروج.".encode("utf-8")
    files = {"file": ("uploaded_policy.txt", io.BytesIO(file_content), "text/plain")}
    response = client.post("/rag/upload", files=files, data={"tenant_id": "test_org"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["document_name"] == "uploaded_policy.txt"
    assert data["chunks_count"] >= 1

    # Cleanup
    client.delete(f"/rag/document/{data['document_id']}")


if __name__ == "__main__":
    pytest.main([__file__])
