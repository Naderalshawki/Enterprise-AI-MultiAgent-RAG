from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
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
# RAG Imports
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

    Startup:
        تشغيل التطبيق وتجهيز البيئة.

    Shutdown:
        إغلاق موارد قاعدة البيانات بشكل آمن.
    """

    # ------------------------------------------------------
    # Startup
    # ------------------------------------------------------

    yield

    # ------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------

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
# CORS Middleware (للسماح باتصال الواجهة بالسيرفر)
# ==========================================================

# قراءة إعدادات RAG للـ Origins ودمجها مع السماح العام
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

# تجهيز مجلد الملفات الثابتة (Static) الخاص بواجهة الـ RAG
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
# دمج راوتر رفع الملفات والبحث (prefix يمنع تعارض المسارات)
# ----------------------------------------------------------
# Document Intelligence (RAG)
# ----------------------------------------------------------
app.include_router(
    rag_router, 
    tags=["RAG & Document Intelligence"]

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

