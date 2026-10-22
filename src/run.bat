@echo off
echo ===================================================
echo 🚀 Starting AI Business Intelligence Platform 🚀
echo ===================================================

echo Starting Backend (FastAPI)...
:: يشغل الباك إند في نافذة مخفية أو منفصلة
start cmd /k "uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Frontend (Streamlit)...
:: ينتظر ثانيتين حتى يشتغل الباك إند ثم يشغل الواجهة
timeout /t 2 /nobreak > NUL
start cmd /k "streamlit run app.py"

echo Done! The browser will open automatically.
exit