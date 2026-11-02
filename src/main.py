from contextlib import asynccontextmanager
from pathlib import Path
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.bootstrap import (
    close_database,
    create_query_engine,
)

from src.modules.llm.interfaces.router import (
    router as llm_router,
)

from src.modules.chat_database.interfaces.router import (
    router as chat_database_router,
)

from src.modules.multi_agent.interfaces.router import (
    router as bi_agent_router,
)

from src.modules.query_engine.interfaces.api_router import (
    create_query_engine_router,
)

from src.services.schools_service import (
    fetch_schools_data,
)

# ==========================================================
# RAG Imports (مشروعك)
# ==========================================================
from src.modules.rag.interfaces.router import rag_router
from src.modules.rag.config.settings import rag_settings


# ==========================================================
# Query Engine Router
# ==========================================================

query_engine_router = create_query_engine_router(
    create_query_engine()
)


# ==========================================================
# Application Lifespan
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    إدارة دورة حياة تطبيق FastAPI.
    """
    yield
    await close_database()


# ==========================================================
# FastAPI Application
# ==========================================================

app = FastAPI(
    title="AI Business Intelligence & RAG Platform",
    description=(
        "Enterprise-grade AI Orchestrator, "
        "Multi-Tenant BI Engine, and Document Intelligence"
    ),
    version="1.1.0",
    lifespan=lifespan,
)

# ==========================================================
# CORS Middleware
# ==========================================================

rag_origins = [o.strip() for o in rag_settings.allowed_origins.split(",") if o.strip()]
allowed_origins = ["*"] if not rag_origins else rag_origins + ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# Static Files & RAG UI
# ==========================================================

static_dir = Path(__file__).parent / "modules" / "rag" / "static"
if static_dir.exists():
    app.mount("/rag_static", StaticFiles(directory=str(static_dir)), name="rag_static")

@app.get("/rag_ui", tags=["RAG Documents"])
def rag_ui():
    """واجهة رفع الملفات والمستندات الخاصة بنظام RAG"""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"error": "RAG UI dashboard file not found. Ensure static files are in src/modules/rag/static/"}


# ==========================================================
# Routers
# ==========================================================

# ----------------------------------------------------------
# LLM
# ----------------------------------------------------------
app.include_router(llm_router)

# ----------------------------------------------------------
# Chat Database
# ----------------------------------------------------------
app.include_router(chat_database_router)

# ----------------------------------------------------------
# Query Engine
# ----------------------------------------------------------
app.include_router(query_engine_router)

# ----------------------------------------------------------
# Multi-Agent BI
# ----------------------------------------------------------
app.include_router(bi_agent_router)

# ----------------------------------------------------------
# Document Intelligence (RAG)
# ----------------------------------------------------------
app.include_router(
    rag_router, 
    tags=["RAG & Document Intelligence"]
)


# ==========================================================
# Proxy to Teammate's RAG Server (الربط مع سيرفر زميلك)
# ==========================================================

@app.api_route("/rag/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_to_rag(path: str, request: Request):
    """
    هذا الكود يربط مشروعك بمشروع زميلك.
    أي طلب يبدأ بـ /rag بيتم تحويله لسيرفر زميلك (بورت 8001).
    """
    
    # التعديل هنا: توجيه المسار لشكل زميلك
    if path == "upload":
        rag_url = "http://127.0.0.1:8001/api/v1/documents/upload"
    else:
        rag_url = f"http://127.0.0.1:8001/api/v1/{path}"
    
    body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None) 
    
    async with httpx.AsyncClient() as client:
        req = client.build_request(
            method=request.method,
            url=rag_url,
            headers=headers,
            content=body,
            params=request.query_params
        )
        response = await client.send(req)
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )


# ==========================================================
# Root Endpoint
# ==========================================================

@app.get(
    "/",
    tags=["System"],
)
async def root(request: Request):
    """
    نقطة الدخول الرئيسية للنظام.
    """
    return {
        "message": "AI BI Platform is running smoothly.",
        "status": "ok",
        "modules_loaded": [
            "LLM",
            "ChatDatabase",
            "QueryEngine",
            "Multi-Agent",
            "RAG (Document Intelligence)"
        ],
        "endpoints": {
            "docs": "/docs",
            "rag_ui": "/rag_ui"
        }
    }