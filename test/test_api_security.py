"""API-level authorization regression tests."""
from fastapi.testclient import TestClient
from src.main import app
from src.modules.rag.config.settings import rag_settings


client = TestClient(app)


def test_institutional_mode_requires_trusted_tenant_context(monkeypatch):
    monkeypatch.setattr(rag_settings, "require_trusted_context", True)
    assert client.get("/rag/documents").status_code == 403
    assert client.post("/rag/query", json={"query": "اختبار"}).status_code == 403


def test_user_cannot_override_trusted_tenant_context(monkeypatch):
    monkeypatch.setattr(rag_settings, "require_trusted_context", True)
    headers = {"X-Tenant-ID": "org_a", "X-User-ID": "user_a", "X-Roles": "admin"}
    response = client.post(
        "/rag/query",
        headers=headers,
        json={"query": "اختبار", "tenant_id": "org_b"},
    )
    assert response.status_code == 403
