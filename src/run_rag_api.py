import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.modules.rag.interfaces.router import rag_router
from src.modules.rag.config.settings import rag_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 RAG API starting on port 8001")
    yield
    logger.info("🛑 RAG API shutting down")

app = FastAPI(title="RAG API", version="1.0.0", lifespan=lifespan)

origins = [o.strip() for o in rag_settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware, 
    allow_origins=origins or ["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# 🔥 التعديل هنا: نضيف prefix="/api/v1" عشان يطابق اللي الرياكت بتبعته
app.include_router(rag_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "rag"}

if __name__ == "__main__":
    uvicorn.run("src.run_rag_api:app", host="127.0.0.1", port=8001, reload=True)