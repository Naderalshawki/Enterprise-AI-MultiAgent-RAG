"""Universal RAG HTTP Client for cross-service and cross-platform communication.

This client can be imported or copied directly by:
- Person 1 (AI Core / multi_agent/tools/rag_tool.py)
- Person 3 (Backend Platform Services)
- Anyone needing to interact with the RAG microservice.

It uses zero mandatory external dependencies (pure standard-library urllib with requests fallback).
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.parse
import urllib.request


class RAGClient:
    """Client for interacting with Document Intelligence & RAG Service."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30, api_key: Optional[str] = None):
        # Read from environment or default to local service port 8000
        self.base_url = (base_url or os.getenv("RAG_SERVICE_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.timeout = timeout
        self.api_key = api_key or os.getenv("RAG_API_KEY", "")

    def _auth_headers(self) -> Dict[str, str]:
        return {"X-API-Key": self.api_key} if self.api_key else {}

    def _post_json(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                **self._auth_headers(),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"RAG Service error ({e.code}) at {endpoint}: {err_body}") from e
        except Exception as e:
            raise ConnectionError(f"Failed to connect to RAG Service at {url}: {e}") from e

    def _get_json(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        if params:
            clean_params = {k: v for k, v in params.items() if v is not None}
            if clean_params:
                url += "?" + urllib.parse.urlencode(clean_params)

        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", **self._auth_headers()},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            raise ConnectionError(f"Failed to call {url}: {e}") from e

    def _delete_json(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", **self._auth_headers()},
            method="DELETE",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            raise ConnectionError(f"Failed to delete {url}: {e}") from e

    def query(
        self,
        query: str,
        top_k: int = 5,
        tenant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        enable_hybrid: bool = True,
        enable_rerank: bool = True,
    ) -> Dict[str, Any]:
        """
        Query knowledge base using Hybrid Search + FlashRank Reranking.

        Returns:
            {
                "query": str,
                "context": str,           # Formatted context ready for prompt injection
                "citations": List[dict],  # [{document_name, page, score, snippet, chunk_id}]
                "total_retrieved": int
            }
        """
        payload = {
            "query": query,
            "top_k": top_k,
            "tenant_id": tenant_id,
            "filters": filters,
            "enable_hybrid": enable_hybrid,
            "enable_rerank": enable_rerank,
        }
        return self._post_json("/rag/query", payload)

    def ingest_text(
        self,
        text: str,
        document_name: str = "direct_note.txt",
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Directly index text snippet or raw document."""
        payload = {
            "text": text,
            "document_name": document_name,
            "tenant_id": tenant_id,
            "metadata": metadata or {},
        }
        return self._post_json("/rag/ingest-text", payload)

    def ingest_file(self, file_path: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Upload and index a file (PDF, Word, Excel, CSV, TXT)."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Multipart form data upload
        boundary = "----WebKitFormBoundaryRAGClientUpload7MA4YWxkTrZu0gW"
        lines = []

        if tenant_id:
            lines.extend([
                f"--{boundary}",
                'Content-Disposition: form-data; name="tenant_id"',
                "",
                tenant_id,
            ])

        with open(path, "rb") as f:
            file_bytes = f.read()

        lines.extend([
            f"--{boundary}",
            f'Content-Disposition: form-data; name="file"; filename="{path.name}"',
            "Content-Type: application/octet-stream",
            "",
            "",
        ])

        body_pre = "\r\n".join(lines).encode("utf-8")
        body_post = f"\r\n--{boundary}--\r\n".encode("utf-8")
        full_body = body_pre + file_bytes + body_post

        url = f"{self.base_url}/rag/upload"
        req = urllib.request.Request(
            url,
            data=full_body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Accept": "application/json",
                **self._auth_headers(),
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def list_documents(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all indexed documents."""
        params = {"tenant_id": tenant_id} if tenant_id else None
        res = self._get_json("/rag/documents", params=params)
        return res.get("documents", [])

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete document from vector store and BM25 index."""
        safe_id = urllib.parse.quote(document_id)
        return self._delete_json(f"/rag/document/{safe_id}")

    def health_check(self) -> Dict[str, Any]:
        """Check RAG engine status and indexed chunks count."""
        return self._get_json("/rag/health")
