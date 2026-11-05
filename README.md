# Enterprise-AI-MultiAgent-RAG 🚀

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Microservices-009688.svg)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Search-orange.svg)](https://www.trychroma.com/)
[![Supabase](https://img.shields.io/badge/Supabase-Database-green.svg)](https://supabase.com/)

نظام ذكاء اصطناعي متكامل ومعماري مبني على هيكلية **الخدمات المصغرة (Microservices Architecture)** ومنظومة وكلاء متعددة (**Multi-Agent System**) مدعومة بالبحث الهجين الذكي (**Hybrid RAG**) وقواعد البيانات الهيكلية (Supabase) لتوفير نظام ذكاء أعمال (BI) متطور للغاية ومطابق لمعايير سوق العمل ومشاريع التخرج المتقدمة.

---

## 🏗️ المعمارية التقنية (System Architecture)

ينقسم النظام إلى خدمتين رئيسيتين تتخاطبان عبر واجهات برمجية (`HTTP REST API` باستخدام `httpx`):

1. **خدمة الـ RAG المستقلة (RAG Service - Port 8001):**
   - مسؤولة عن استلام المستندات وتقسيمها (Chunking).
   - توفر بحثاً هجيناً ذكياً يدمج بين **Dense Vector Search** (عبر `ChromaDB` و `SentenceTransformers`) و **Sparse BM25 Search** مع تقنية الدمج `RRF (Reciprocal Rank Fusion)`.
   - توفر خطة طوارئ ذكية (Global Fallback) لضمان عدم ضياع أي سياق.

2. **منظومة الوكلاء المتعددة (Multi-Agent BI Service - Port 10000):**
   - **المنسق / المخطط (Planner Agent):** يحلل استعلام المستخدم ويضع خطة تنفيذية دقيقة.
   - **المنفذ (Executor Agent):** ينفذ المهام عبر اختيار الأداة المناسبة (سواء أداة الـ RAG عبر الـ API أو أداة قاعدة البيانات).
   - **المدقق الذاتي (Result Validator Agent):** وكيل رقابي متطور يفحص الإجابات والتقارير لضمان مطابقتها للبيانات الأصلية ومنع الهلوسة (Hallucination) مع دعم الاستنتاج الذكي.

---

## 🛠️ التقنيات المستخدمة (Tech Stack)

* **Backend Framework:** FastAPI, Uvicorn
* **AI & LLM Integration:** Ollama (Qwen2.5-Coder / Llama), Sentence-Transformers
* **Vector Database:** ChromaDB
* **Structured Database:** Supabase (PostgreSQL)
* **API Communication:** HTTPX (Asynchronous Client)
* **Document Processing:** PyMuPDF (Fitz)

---

## ⚙️ طريقة التثبيت والتشغيل المحليه (Installation & Quick Start)

### 1. استنساخ المستودع وتجهيز البيئة الافتراضية
```bash
git clone [https://github.com/YOUR_USERNAME/Enterprise-AI-MultiAgent-RAG.git](https://github.com/YOUR_USERNAME/Enterprise-AI-MultiAgent-RAG.git)
cd Enterprise-AI-MultiAgent-RAG
python -m venv venv
# لتفعيل البيئة على ويندوز (PowerShell):
.\venv\Scripts\Activate