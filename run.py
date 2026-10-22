"""Universal Native Python Entrypoint (No Docker Required).

Works directly on Windows, Linux, and macOS:
    python run.py
"""

import sys
from pathlib import Path

# Fix Windows console UTF-8 encoding for Arabic & emojis
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project root to sys.path automatically
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

import uvicorn

if __name__ == "__main__":
    print("==================================================================")
    print("🚀 محرك استيعاب وفهم المستندات والـ RAG يعمل محلياً بنظام Python النقي")
    print("🌐 واجهة المتصفح التفاعلية: http://127.0.0.1:8000/")
    print("📑 مستندات Swagger التفاعلية: http://127.0.0.1:8000/docs")
    print("==================================================================")
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)

