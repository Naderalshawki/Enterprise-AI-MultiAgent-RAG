# 🧠 AI Business Intelligence & Orchestrator Platform

> ## 🎓 Graduation Project — Artificial Intelligence & Software Engineering

> **An AI-Agent-Based Business Intelligence Platform for Analyzing Databases and Documents**

منصة ذكاء أعمال متقدمة تعتمد على الذكاء الاصطناعي والوكلاء الأذكياء لتحويل البيانات وقواعد البيانات والمستندات إلى **تحليلات، رؤى، إجابات وتقارير ذكية** باستخدام معمارية برمجية منظمة وقابلة للتوسع.

---

# 🌟 Overview

**AI Business Intelligence Platform** هي منصة AI متكاملة تهدف إلى بناء طبقة ذكاء فوق مصادر البيانات المختلفة، بحيث يستطيع المستخدم التفاعل مع بيانات المؤسسة باستخدام **Natural Language** بدلًا من كتابة SQL يدويًا أو البحث داخل المستندات بشكل تقليدي.

تعمل المنصة كـ **AI Orchestrator** مركزي يقوم بفهم سؤال المستخدم، تحديد الأدوات المطلوبة، تنفيذ المهمة المناسبة، تحليل النتائج، ثم إنتاج إجابة أو تقرير مفهوم للمستخدم.

الفكرة الأساسية:

```text
User
  ↓
Natural Language Question
  ↓
AI Agent
  ↓
Planner / Tool Selection
  ↓
┌─────────────────────────────────────────────┐
│                                             │
│  Database Analysis        Document Analysis │
│        ↓                         ↓          │
│  Query Engine                  RAG           │
│        ↓                         ↓          │
│  Text-to-SQL               Retrieval        │
│        ↓                         ↓          │
│  PostgreSQL / Supabase      Documents       │
│                                             │
└─────────────────────────────────────────────┘
  ↓
Analysis / Reasoning
  ↓
AI Insights
  ↓
Report / Final Answer
```

---

# 🎯 Project Vision

يهدف المشروع إلى بناء **AI-Powered Business Intelligence Platform** يمكن تخصيصها لمؤسسات مختلفة مثل:

- 🏦 Banks
- 🏫 Universities
- 🏥 Hospitals
- 🏢 Enterprises
- 🏛️ Government Organizations

بدلًا من بناء نظام مختلف لكل مؤسسة، تعتمد المنصة على Architecture قابلة للتكوين **Configurable Architecture** تسمح بربط مصادر بيانات مختلفة مع نفس نواة الذكاء الاصطناعي.

---

# 🚀 Core Capabilities

## 1. 🗄️ AI Database Analysis

تمكين المستخدم من طرح أسئلة باللغة الطبيعية حول بيانات المؤسسة.

مثال:

```text
"ما إجمالي المبيعات خلال الربع الأخير؟"
```

أو:

```text
"اعرض أفضل 10 منتجات من حيث المبيعات."
```

أو:

```text
"كم عدد العملاء الجدد خلال هذا الشهر؟"
```

ويقوم النظام بتحويل السؤال إلى استعلام مناسب وتنفيذه على قاعدة البيانات.

---

# 2. 🔤 Text-to-SQL

إحدى الوظائف الأساسية في النظام.

```text
Natural Language
       ↓
Question Understanding
       ↓
Schema Understanding
       ↓
SQL Generation
       ↓
SQL Validation
       ↓
SQL Execution
       ↓
Query Result
       ↓
AI Analysis
```

الهدف هو تمكين المستخدم من التعامل مع قواعد البيانات باستخدام اللغة الطبيعية بدلًا من كتابة SQL يدويًا.

---

# 3. 🧬 Schema Intelligence

لا يستطيع نظام Text-to-SQL العمل بكفاءة بدون فهم بنية قاعدة البيانات.

لذلك تحتوي المنصة على **Schema Engine** مسؤول عن اكتشاف وفهم:

- Tables
- Columns
- Data Types
- Primary Keys
- Foreign Keys
- Relationships
- Constraints
- Database Metadata

ويتم استخدام هذه المعلومات لتزويد الذكاء الاصطناعي بالسياق اللازم لإنشاء استعلامات أكثر دقة.

```text
Database
   ↓
Schema Discovery
   ↓
Schema Representation
   ↓
Schema Context
   ↓
LLM
   ↓
SQL Generation
```

---

# 4. 🤖 AI Agent Orchestration

المنصة لا تعتمد على Agent واحد لتنفيذ كل شيء.

بدلًا من ذلك، تعتمد على **AI Agent Orchestration Architecture** تسمح بتقسيم المهمة إلى مراحل وأدوات متخصصة.

```text
User Question
      ↓
   AI Agent
      ↓
    Planner
      ↓
 Tool Selection
      ↓
 ┌────┴──────────────┐
 ↓                   ↓
Database Tool      RAG Tool
 ↓                   ↓
Query Engine       Retrieval
 ↓                   ↓
Database           Documents
 └────────┬──────────┘
          ↓
       Analyzer
          ↓
       Reporter
          ↓
     Final Answer
```

---

# 5. 🧠 Multi-Agent Architecture

تتكون منظومة الوكلاء من عدة مكونات متخصصة.

### Planner Agent

مسؤول عن:

- فهم المهمة.
- تحديد الخطوات المطلوبة.
- اختيار الأدوات المناسبة.
- إنشاء Execution Plan.

### Data Agent

مسؤول عن:

- التعامل مع بيانات قواعد البيانات.
- تنفيذ مهام تحليل البيانات.
- الاستفادة من Query Engine.

### Analyzer Agent

مسؤول عن:

- تحليل النتائج.
- استخراج الأنماط.
- اكتشاف المؤشرات المهمة.
- توليد AI Insights.

### Reporter Agent

مسؤول عن:

- تحويل نتائج التحليل إلى إجابة واضحة.
- إنشاء ملخصات وتقارير.
- تنظيم المخرجات النهائية.

---

# 6. 📚 RAG — Retrieval-Augmented Generation

تدعم المنصة تحليل المستندات باستخدام **Retrieval-Augmented Generation (RAG)**.

المسار العام:

```text
Document
   ↓
Ingestion
   ↓
Parsing
   ↓
Chunking
   ↓
Embeddings
   ↓
Vector Database
   ↓
Retrieval
   ↓
Reranking
   ↓
Relevant Context
   ↓
LLM
   ↓
Answer
```

يدعم نظام RAG التعامل مع مصادر المستندات وإرجاع السياق الأكثر ارتباطًا بسؤال المستخدم.

> **RAG Implementation** يتم تطويرها كطبقة مستقلة، بينما يتم دمجها مع الـAI Agent من خلال أدوات النظام.

---

# 7. 🧠 Agent + RAG Integration

من أهم أجزاء المشروع هو دمج RAG مع الـAI Agent.

بدلًا من جعل RAG نظامًا منفصلًا، يستطيع الـAgent تحديد متى يحتاج إلى استخدامه.

مثال:

```text
User:
"ما هي سياسة الإجازات حسب دليل الموظفين؟"
```

يستطيع الـAgent تحديد أن السؤال يحتاج إلى:

```text
RAG Tool
   ↓
Document Retrieval
   ↓
Relevant Context
   ↓
LLM
   ↓
Answer
```

بينما سؤال مثل:

```text
"ما متوسط رواتب الموظفين في كل قسم؟"
```

يتم توجيهه إلى:

```text
Database Tool
   ↓
Query Engine
   ↓
Database
```

وهذا يجعل الـAgent مسؤولًا عن **اختيار الأداة المناسبة للمهمة**.

---

# 8. 💾 Memory

تحتوي المنصة على طبقة Memory مستقلة تسمح للنظام بالاحتفاظ بالسياق المفيد للمحادثات.

```text
User
 ↓
Conversation
 ↓
Memory Service
 ↓
Relevant Memories
 ↓
AI Agent
```

وتستخدم الذاكرة لتحسين استمرارية المحادثة وفهم السياق السابق عند الحاجة.

---

# 🏗️ Final System Architecture

المعمارية النهائية للمشروع:

```text
                         ┌─────────────────┐
                         │      USER       │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │    FRONTEND     │
                         └────────┬────────┘
                                  │
                                  ▼
                  ┌────────────────────────────┐
                  │ Identity / Tenant /        │
                  │ Permissions / Security     │
                  └──────────────┬─────────────┘
                                 │
                                 ▼
                         ┌─────────────────┐
                         │    AI AGENT     │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │     PLANNER     │
                         │  Tool Selection │
                         └────────┬────────┘
                                  │
               ┌──────────────────┼──────────────────┐
               │                  │                  │
               ▼                  ▼                  ▼
       ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
       │ Database     │   │     RAG      │   │    Memory    │
       │ Tool         │   │     Tool     │   │    Service   │
       └──────┬───────┘   └──────┬───────┘   └──────────────┘
              │                  │
              ▼                  ▼
       ┌──────────────┐   ┌──────────────┐
       │ Query Engine │   │ Vector DB    │
       └──────┬───────┘   └──────┬───────┘
              │                  │
              ▼                  ▼
       ┌──────────────┐   ┌──────────────┐
       │ Chat         │   │ Documents    │
       │ Database     │   │              │
       └──────┬───────┘   └──────────────┘
              │
              ▼
       ┌────────────────────┐
       │ Supabase /         │
       │ PostgreSQL         │
       └─────────┬──────────┘
                 │
                 ▼
        ┌───────────────────┐
        │ Analysis /        │
        │ Insights          │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ AI Reporter       │
        │ / Final Response  │
        └───────────────────┘
```

---

# 🗄️ Final Database Architecture

القاعدة الأساسية النهائية للمشروع هي:

```text
Supabase
    ↓
PostgreSQL
```

وتستخدم المنصة PostgreSQL باعتبارها طبقة قاعدة البيانات الأساسية للـBusiness Intelligence.

```text
AI Agent
    ↓
Database Tool
    ↓
Query Engine
    ↓
Chat Database
    ↓
Schema Engine
    ↓
Text-to-SQL
    ↓
SQL Validation
    ↓
SQL Execution
    ↓
Supabase / PostgreSQL
```

> **MongoDB is NOT part of the final production architecture.**

---

# 🔌 Multi-Provider LLM Architecture

تم تصميم طبقة LLM بطريقة تسمح باستخدام أكثر من مزود للذكاء الاصطناعي.

المعمارية:

```text
                    LLM Service
                         │
                         ▼
                    LLM Router
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
        GEMINI          DeepSeek       Gemini
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
                    LLM Response
```

يمكن توسيع النظام مستقبلًا لإضافة مزودين آخرين دون تغيير منطق النظام الأساسي.

---

# 🧩 LLM Layer Responsibilities

طبقة LLM مسؤولة عن:

- Provider Management
- Provider Selection
- Model Configuration
- Prompt Execution
- Response Handling
- Error Handling
- Provider Routing
- Extensibility

وتفصل هذه الطبقة منطق التطبيق عن مزود النموذج المستخدم.

---

# 🔍 Query Engine

يعتبر **Query Engine** طبقة مستقلة بين الـAI Agent وقاعدة البيانات.

المسار:

```text
Question
   ↓
QueryRequest
   ↓
QueryContext
   ↓
Query Classification
   ↓
Query Routing
   ↓
Database Adapter
   ↓
Execution
   ↓
QueryResult
```

مسؤولياته:

- استقبال Query Requests.
- بناء Query Context.
- تصنيف نوع السؤال.
- تحديد مصدر البيانات.
- اختيار Adapter المناسب.
- إدارة Execution.
- التعامل مع الأخطاء.
- إعادة QueryResult موحد.

---

# 🗃️ Chat Database

طبقة Chat Database مسؤولة عن تنفيذ منطق التفاعل الذكي مع قواعد البيانات.

تشمل:

```text
Schema
   ↓
Schema Context
   ↓
Prompt Construction
   ↓
LLM SQL Generation
   ↓
SQL Validation
   ↓
SQL Execution
   ↓
Result Mapping
```

---

# 🧬 Schema Engine

محرك الـSchema يوفر طبقة معرفية لقاعدة البيانات.

وظائفه:

```text
Database
   ↓
Schema Discovery
   ↓
Tables
Columns
Relationships
Constraints
Metadata
   ↓
Schema Representation
   ↓
AI Context
```

وهذا يسمح للـLLM بفهم بنية البيانات قبل إنشاء الاستعلام.

---

# 🛡️ Security & Tenant Architecture

المنصة مصممة لدعم بيئات المؤسسات متعددة المستخدمين والعملاء.

الطبقة الأمنية:

```text
User
 ↓
Identity
 ↓
Authentication
 ↓
Tenant
 ↓
Roles
 ↓
Permissions
 ↓
Access Control
 ↓
AI Platform
```

وتبقى مسؤوليات:

- Authentication
- Authorization
- Users
- Roles
- Permissions
- Tenant Management
- Access Control

ضمن طبقة الـIdentity/Security الخاصة بالمنصة.

---

# 🏢 Multi-Tenant Vision

المنصة مصممة لتكون قابلة للتخصيص حسب المؤسسة.

مثال:

```text
                 AI BI Platform
                        │
       ┌────────────────┼────────────────┐
       │                │                │
       ▼                ▼                ▼
     Bank           University        Hospital
       │                │                │
       ▼                ▼                ▼
   Banking DB       Academic DB      Medical DB
```

نفس نواة الذكاء الاصطناعي يمكن استخدامها مع اختلاف:

- Schema
- Data Sources
- Documents
- Business Rules
- Users
- Permissions
- Tenant Configuration

---

# 📂 Project Structure

```text
Enterprise_AI_BI_Platform/
│
├── .agents/
│   └── # AI-assisted development resources
│
├── test/
│   └── # Tests for LLMs, providers, tools and services
│
├── src/
│   │
│   ├── main.py
│   │   # FastAPI application entry point
│   │
│   ├── bootstrap.py
│   │   # Application composition and dependency initialization
│   │
│   ├── constants.py
│   │   # Shared application constants
│   │
│   ├── services/
│   │   # Application-specific external/business services
│   │
│   └── modules/
│       │
│       ├── llm/
│       │   # Multi-provider LLM infrastructure
│       │
│       ├── chat_database/
│       │   # Text-to-SQL and database interaction
│       │
│       ├── schema_engine/
│       │   # Database schema discovery and intelligence
│       │
│       ├── query_engine/
│       │   # Query classification, routing and execution
│       │
│       ├── multi_agent/
│       │   # Planner, Agents, Executor and orchestration
│       │
│       ├── memory/
│       │   # Conversation and contextual memory
│       │
│       └── rag/
│           # Retrieval-Augmented Generation integration
│
├── .env
│   # Local environment variables and secrets
│   # NEVER commit this file
│
├── .gitignore
│
├── requirements.txt
│
└── README.md
```

---

# 🧱 Clean Architecture

تم تصميم المشروع وفق مبادئ:

### Clean Architecture

```text
Presentation
     ↓
Application
     ↓
Domain
     ↓
Infrastructure
```

مع فصل واضح بين:

- Domain Logic
- Application Logic
- Infrastructure
- Interfaces
- External Services

---

# 🔄 Separation of Concerns

كل Module لديه مسؤولية واضحة.

```text
LLM
 │
 └── Language Model Communication

Schema Engine
 │
 └── Database Schema Intelligence

Chat Database
 │
 └── Text-to-SQL Database Interaction

Query Engine
 │
 └── Query Classification & Routing

Multi-Agent
 │
 └── AI Orchestration

RAG
 │
 └── Document Retrieval

Memory
 │
 └── Context Persistence
```

وهذا يجعل النظام:

- Maintainable
- Testable
- Scalable
- Extensible
- Modular

---

# 🔁 End-to-End AI Workflow

عند إرسال سؤال للمستخدم:

```text
1. User submits a question
              ↓
2. Frontend sends request
              ↓
3. Identity / Tenant validation
              ↓
4. AI Agent receives question
              ↓
5. Memory Context is loaded
              ↓
6. Planner analyzes the task
              ↓
7. Planner selects required tools
              ↓
8. Database Tool and/or RAG Tool
              ↓
9. Query Engine / Retrieval
              ↓
10. Data or Document Context
              ↓
11. Analyzer processes results
              ↓
12. Reporter generates final response
              ↓
13. Memory is updated
              ↓
14. Final Answer returned to user
```

---

# 🧠 Example: Database Question

```text
User:
"ما إجمالي المبيعات لكل فرع؟"
```

System:

```text
User Question
      ↓
AI Agent
      ↓
Planner
      ↓
Database Tool
      ↓
Query Engine
      ↓
Schema Engine
      ↓
Text-to-SQL
      ↓
SQL Validation
      ↓
Supabase / PostgreSQL
      ↓
Query Result
      ↓
Analyzer
      ↓
Reporter
      ↓
Final Business Insight
```

---

# 📚 Example: Document Question

```text
User:
"ما شروط الحصول على الإجازة السنوية؟"
```

System:

```text
User Question
      ↓
AI Agent
      ↓
Planner
      ↓
RAG Tool
      ↓
Retriever
      ↓
Relevant Documents
      ↓
Context
      ↓
LLM
      ↓
Final Answer
```

---

# 🔀 Example: Hybrid Question

يمكن للسؤال أن يحتاج إلى أكثر من مصدر.

```text
User:
"قارن أداء المبيعات الحالي مع السياسة الموجودة في دليل الشركة."
```

الـAgent يمكنه إنشاء خطة تحتوي على:

```text
Planner
   │
   ├── Database Tool
   │       ↓
   │   Query Engine
   │       ↓
   │   PostgreSQL
   │
   └── RAG Tool
           ↓
       Documents
```

ثم:

```text
Database Results
        +
Document Context
        ↓
      Analyzer
        ↓
      Reporter
        ↓
    Final Insight
```

---

# 🛠️ Technology Stack

## Backend

- Python
- FastAPI
- Uvicorn

## AI / LLM

- Large Language Models
- Multi-Provider LLM Architecture
- Prompt Engineering
- AI Agents
- Multi-Agent Orchestration

## Database

- PostgreSQL
- Supabase

## Database Intelligence

- Text-to-SQL
- Schema Discovery
- SQL Validation
- Query Execution
- Query Result Mapping

## Document Intelligence

- RAG
- Embeddings
- Vector Database
- Retrieval
- Hybrid Search
- Reranking

## Architecture

- Clean Architecture
- Modular Architecture
- Separation of Concerns
- Dependency Injection
- Service-Oriented Design

---

# 🧪 Testing Strategy

يتم اختبار النظام على عدة مستويات:

```text
Unit Tests
    ↓
Component Tests
    ↓
Integration Tests
    ↓
AI Workflow Tests
    ↓
End-to-End Tests
```

تشمل الاختبارات:

- LLM Providers
- Query Engine
- Schema Engine
- Text-to-SQL
- Database Tools
- Agent Planning
- RAG Integration
- Memory
- API Endpoints

---

# ⚙️ Configuration

يتم الاعتماد على Environment Variables لتخزين الإعدادات الحساسة.

مثال:

```env
APP_ENV=development

DATABASE_URL=your_supabase_postgresql_url

LLM_PROVIDER=gemini

GEMINI_API_KEY=your_api_key

DEEPSEEK_API_KEY=your_api_key

GEMINI_API_KEY=your_api_key
```

> ⚠️ لا تقم أبدًا برفع مفاتيح API الحقيقية إلى GitHub.

---

# ▶️ Running the Project

بعد تثبيت المتطلبات:

```bash
pip install -r requirements.txt
```

ثم تشغيل الخادم:

```bash
python -m uvicorn src.main:app --reload
```

أو:

```bash
py -m uvicorn src.main:app --reload
```

بعد التشغيل:

```text
http://127.0.0.1:8000
```

Swagger API Documentation:

```text
http://127.0.0.1:8000/docs
```

OpenAPI:

```text
http://127.0.0.1:8000/openapi.json
```

---

# 🔐 Environment & Secrets

الملف:

```text
.env
```

يستخدم للإعدادات المحلية والمفاتيح السرية.

يجب أن يكون ضمن:

```text
.gitignore
```

ولا يجب رفعه إلى GitHub.

---

# 📈 Scalability

المعمارية مصممة لتسمح بإضافة:

```text
New LLM Provider
        ↓
LLM Provider Interface
        ↓
LLM Router
```

أو:

```text
New Database
        ↓
Database Adapter
        ↓
Query Engine
```

أو:

```text
New AI Tool
        ↓
Tool Interface
        ↓
AI Agent
```

دون إعادة بناء النظام بالكامل.

---

# 🔌 Extensible Architecture

يمكن مستقبلًا إضافة:

- MySQL
- SQL Server
- SQLite
- Additional PostgreSQL Sources
- Additional Vector Databases
- Additional LLM Providers
- BI Dashboard Generation
- Automated Reports
- Data Visualization
- Forecasting
- Anomaly Detection
- Advanced Analytics

مع الحفاظ على النواة الأساسية للنظام.

---

# 📊 AI Business Intelligence

المنصة لا تكتفي بإرجاع البيانات.

الهدف النهائي هو الانتقال من:

```text
Raw Data
```

إلى:

```text
Data
  ↓
Information
  ↓
Analysis
  ↓
Insights
  ↓
Business Intelligence
  ↓
Decision Support
```

---

# 🧠 From Chatbot to AI Business Intelligence

المشروع ليس مجرد Chatbot.

```text
Traditional Chatbot
       ↓
Question
       ↓
Answer
```

بينما منصتنا:

```text
Business Question
       ↓
AI Agent
       ↓
Planning
       ↓
Tool Selection
       ↓
Database / Documents
       ↓
Retrieval / Querying
       ↓
Analysis
       ↓
Reasoning
       ↓
Insights
       ↓
Report
       ↓
Decision Support
```

وهذه هي الفكرة الأساسية التي تجعل النظام **AI Business Intelligence Platform** وليس مجرد واجهة محادثة.

---

# 👥 Development Responsibilities

## AI Core / Intelligence

يشمل:

- LLM Layer
- LLM Router
- Text-to-SQL
- Schema Engine
- Query Engine
- AI Agent
- Multi-Agent Orchestration
- AI Analysis
- AI Insights
- AI Reports
- Memory
- RAG + Agent Integration

## RAG Engineering

تشمل:

- Document Ingestion
- Parsing
- Chunking
- Embeddings
- Vector Database
- Retrieval
- Hybrid Search
- Reranking

## Platform / Backend / Frontend

تشمل:

- Backend APIs
- Frontend
- Authentication
- Identity
- Tenant Management
- Users
- Roles
- Permissions
- Security
- Platform Database

---

# 🏆 Project Objectives

يهدف المشروع إلى تحقيق:

### 1. Intelligent Data Access

جعل البيانات قابلة للوصول باستخدام اللغة الطبيعية.

### 2. Automated Data Analysis

تقليل الحاجة إلى كتابة الاستعلامات وتحليل البيانات يدويًا.

### 3. Document Intelligence

تمكين المستخدم من طرح الأسئلة على المستندات.

### 4. AI-Orchestrated Workflows

استخدام Agent ذكي لتحديد الأدوات والخطوات المناسبة.

### 5. Enterprise Scalability

دعم بيئات المؤسسات المختلفة.

### 6. Modular Architecture

إمكانية تطوير كل مكون بشكل مستقل.

---

# 📌 Design Principles

المشروع يعتمد على مجموعة من المبادئ:

```text
Clean Architecture
        +
SOLID Principles
        +
Separation of Concerns
        +
Dependency Injection
        +
Modular Design
        +
Interface-Based Design
        +
Extensibility
        +
Testability
```

---

# 🧭 Project Roadmap

## Phase 1 — AI Foundation

- [x] LLM Abstraction
- [x] Multi-Provider Architecture
- [x] Prompt Infrastructure
- [x] LLM Routing

## Phase 2 — Database Intelligence

- [x] Schema Engine
- [x] Query Engine
- [x] Query Classification
- [x] Query Routing
- [x] Database Tool
- [ ] Final Supabase/PostgreSQL Integration
- [ ] Advanced Text-to-SQL

## Phase 3 — Multi-Agent

- [x] Planner
- [x] Task Executor
- [x] Analyzer Agent
- [x] Reporter Agent
- [x] Database Tool
- [ ] Full Agent + RAG Workflow

## Phase 4 — RAG

- [ ] Document Ingestion
- [ ] Parsing
- [ ] Chunking
- [ ] Embeddings
- [ ] Vector Database
- [ ] Retrieval
- [ ] Hybrid Search
- [ ] Reranking
- [ ] Agent Integration

## Phase 5 — Memory

- [x] Memory Domain
- [x] Memory Service
- [x] Session Memory
- [x] User Memory
- [ ] Production Persistence

## Phase 6 — Enterprise Platform

- [ ] Authentication
- [ ] Authorization
- [ ] Multi-Tenancy
- [ ] Role-Based Access Control
- [ ] Security Layer
- [ ] Frontend Dashboard

## Phase 7 — Business Intelligence

- [ ] Advanced Analytics
- [ ] AI Insights
- [ ] Automated Reports
- [ ] Data Visualization
- [ ] Decision Support

---

# 📜 Academic Project Statement

> **An AI-Agent-Based Business Intelligence Platform for Analyzing Databases and Documents**

The proposed system is an intelligent Business Intelligence platform that combines Large Language Models, Text-to-SQL, Retrieval-Augmented Generation, Multi-Agent Systems, Schema Intelligence, and Memory to provide natural-language access to enterprise data and documents.

The system introduces an AI orchestration layer capable of understanding user requests, planning required operations, selecting appropriate tools, retrieving or querying relevant information, analyzing results, and generating meaningful business insights and reports.

The architecture follows Clean Architecture and Separation of Concerns principles to ensure modularity, maintainability, scalability, and extensibility.

---

# 🔥 Core Architecture Summary

```text
                         AI BI PLATFORM
                              │
                              ▼
                           USER
                              │
                              ▼
                          FRONTEND
                              │
                              ▼
                  IDENTITY / TENANT / SECURITY
                              │
                              ▼
                         AI AGENT
                              │
                              ▼
                          PLANNER
                              │
                 ┌────────────┼────────────┐
                 │            │            │
                 ▼            ▼            ▼
            DATABASE         RAG         MEMORY
               TOOL          TOOL         SERVICE
                 │            │
                 ▼            ▼
           QUERY ENGINE    RETRIEVAL
                 │            │
                 ▼            ▼
          CHAT DATABASE    DOCUMENTS
                 │
                 ▼
        SCHEMA + TEXT-to-SQL
                 │
                 ▼
          SUPABASE / POSTGRESQL
                 │
                 └────────────┐
                              │
                              ▼
                           ANALYZER
                              │
                              ▼
                           REPORTER
                              │
                              ▼
                     AI INSIGHTS / REPORT
```

---

# 💡 Final Vision

الهدف النهائي من المشروع هو بناء منصة تجعل التعامل مع بيانات المؤسسات والمستندات أكثر ذكاءً وبساطة.

بدلًا من أن يحتاج المستخدم إلى معرفة:

```text
SQL
Database Schema
Search Syntax
Document Structure
Analytics Tools
```

يستطيع ببساطة طرح سؤال باللغة الطبيعية:

```text
"حلل أداء المبيعات هذا الشهر وقارنه بالشهر السابق،
واشرح لي أهم أسباب التغير."
```

وتتولى المنصة:

```text
Understand
   ↓
Plan
   ↓
Select Tools
   ↓
Query / Retrieve
   ↓
Analyze
   ↓
Reason
   ↓
Generate Insights
   ↓
Report
```

ليصبح النظام طبقة ذكاء اصطناعي فوق البيانات تساعد المؤسسات على:

> **Understand Data → Discover Insights → Support Decisions**

---

# 👨‍💻 Project

**AI Business Intelligence & Orchestrator Platform**

### Graduation Project

**Artificial Intelligence & Software Engineering**

> Building an intelligent, modular and extensible AI Business Intelligence platform capable of understanding databases, analyzing documents, orchestrating AI agents, and transforming enterprise data into actionable insights.