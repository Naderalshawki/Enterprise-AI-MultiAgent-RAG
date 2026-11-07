# Enterprise-AI-MultiAgent-RAG 🚀

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Microservices-009688.svg)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Search-orange.svg)](https://www.trychroma.com/)
[![Supabase](https://img.shields.io/badge/Supabase-Database-green.svg)](https://supabase.com/)

# 🧠 Enterprise-AI-MultiAgent-RAG
### An AI-Agent-Based Business Intelligence Platform for Analyzing Databases and Documents

<p align="center">

**The Intelligence Layer Behind an AI-Powered Business Intelligence Platform**

</p>

---

## 📌 Overview

The **AI Core** is the central intelligence layer of an AI-Agent-Based Business Intelligence Platform designed to transform natural language questions into structured analytical operations, actionable insights, and data-driven reports.

It coordinates multiple specialized AI agents, Large Language Models (LLMs), database query components, and external knowledge retrieval services to perform intelligent analysis across structured and unstructured data sources.

Rather than relying on a single LLM to handle every task, the system follows a **Multi-Agent Architecture**, where each agent has a dedicated responsibility within an orchestrated execution workflow.

The primary objective is to build a reliable, modular, and extensible intelligence layer capable of understanding user requests, planning execution steps, selecting appropriate tools, analyzing retrieved information, validating results, and generating structured responses.

## 🎯 My Development Scope

My contribution focuses on designing and developing the **AI Core and Multi-Agent Intelligence Layer**.

The main components under my responsibility include:

- **LLM Integration:** Unified integration with multiple language model providers.
- **Schema Engine:** Database schema discovery, understanding, and retrieval.
- **Chat Database:** Natural Language to SQL generation and database execution.
- **Query Engine:** Query classification, routing, orchestration, and execution management.
- **Multi-Agent System:** Coordination of specialized AI agents.
- **Planner:** Intelligent task understanding and execution planning.
- **Executor:** Tool selection and task execution.
- **Analyzer Agent:** Analytical reasoning and insight extraction.
- **Result Validator Agent:** Validation of generated results and analytical claims.
- **Reporter Agent:** Structured response and report generation.
- **Memory Management:** Context and memory management.
- **RAG Integration:** Connecting document retrieval capabilities with the AI Agent.

**Scope clarification:** My responsibility covers the AI Core intelligence components and their integration. The independent RAG Backend implementation, including document ingestion, parsing, chunking, embeddings, vector storage, retrieval, hybrid search, and reranking, is handled separately by another project contributor.

---

## 🏗️ System Architecture

The AI Core operates as the intelligence and orchestration layer between user requests and the available data sources.

```text
                  USER REQUEST
                       |
                       v
                  AI CORE
                       |
                       v
                 MULTI-AGENT
                  SYSTEM
                       |
                       v
                    PLANNER
                       |
                       v
                TOOL SELECTION
                       |
              +--------+--------+
              |                 |
              v                 v
        DATABASE PATH        DOCUMENT PATH
              |                 |
              v                 v
         QUERY ENGINE       RAG INTEGRATION
              |                 |
              v                 v
        CHAT DATABASE      RAG BACKEND
              |                 |
              +--------+--------+
                       |
                       v
                 ANALYZER AGENT
                       |
                       v
              RESULT VALIDATOR
                       |
                       v
                 REPORTER AGENT
                       |
                       v
                FINAL RESPONSE
```

### Architecture Principles

- **Modularity:** Each component has a clearly defined responsibility.
- **Agent Orchestration:** Specialized agents collaborate through a coordinated workflow.
- **Model Flexibility:** Different LLMs can be assigned to different tasks.
- **Data Grounding:** Analytical outputs should be based on retrieved or executed data.
- **Reliability:** Error handling, timeouts, and retries improve execution resilience.
- **Extensibility:** New tools, agents, and data sources can be integrated without redesigning the entire intelligence layer.

---

## 📂 Project Structure

The following structure represents the AI Core modules under development:

```text
src/
│
├── bootstrap.py
├── main.py
├── constants.py
├── run.bat
│
├── modules/
│   │
│   ├── llm/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   └── interfaces/
│   │
│   ├── schema_engine/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   └── interfaces/
│   │
│   ├── chat_database/
│   │   ├── application/
│   │   ├── config/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   ├── interfaces/
│   │   └── prompts/
│   │
│   ├── query_engine/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   └── interfaces/
│   │
│   ├── multi_agent/
│   │   ├── agents/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── tools/
│   │   └── interfaces/
│   │
│   ├── memory/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   └── interfaces/
│
└── services/
    └── schools_service.py
```

### Module Responsibilities

| Module | Description |
|---|---|
| `llm/` | Language model integration and provider management |
| `schema_engine/` | Database schema discovery and understanding |
| `chat_database/` | Natural language to SQL processing |
| `query_engine/` | Query classification and execution orchestration |
| `multi_agent/` | Intelligent agent coordination and execution |
| `memory/` | Context and memory management |
| `services/` | Additional domain-specific services |

---

## 🤖 Multi-Agent System

The Multi-Agent System is the central intelligence component of the AI Core.

It divides complex analytical tasks into smaller responsibilities handled by specialized agents.

### 1. Planner Agent

Responsible for understanding user requests and generating an execution plan.

Key responsibilities:

- Natural language request understanding.
- Task classification.
- Execution planning.
- Tool selection.
- Ambiguity detection and clarification.
- Error and timeout handling.

**Reliability improvements implemented:**

- Timeout mechanisms.
- Retry mechanisms.
- Error handling.
- Clarification for ambiguous requests.

### 2. Executor

Responsible for executing the tasks defined by the Planner.

It coordinates the required tools and components, including database operations and document retrieval integration.

### 3. Analyzer Agent

Responsible for analytical reasoning over retrieved information and executed database results.

Key responsibilities:

- Data analysis.
- Information extraction.
- Pattern identification.
- Analytical interpretation.
- Database-based analysis.
- RAG-based information analysis.

### 4. Result Validator Agent

A dedicated validation agent designed to improve the reliability of generated analytical outputs.

Key responsibilities:

- Reviewing analytical claims.
- Checking numerical consistency against available source results.
- Identifying unsupported information.
- Detecting potentially hallucinated claims.
- Rejecting or requesting correction of invalid outputs.

Its primary objective is to reduce LLM hallucinations and improve data-grounded response generation.

### 5. Reporter Agent

Responsible for transforming validated analytical results into structured and understandable responses.

Key responsibilities:

- Analytical report generation.
- Result summarization.
- Structured response formatting.
- Insight presentation.
- Database and document-based reporting.

---

## 🔌 LLM Integration & Multi-Model Strategy

The AI Core uses a flexible LLM integration layer to support different model providers and assign models according to task requirements.

### Model Allocation

| Component | Model | Purpose |
|---|---|---|
| Planner | Qwen 2.5 1.5B | Fast planning and task understanding |
| Analyzer | Qwen 2.5 1.5B | Analytical processing |
| Reporter | Qwen 2.5 Coder 7B / Gemini | Report generation |

### Supported Model Ecosystem

- Groq
- Google Gemini
- OpenRouter
- Ollama
- Qwen Models

The multi-model strategy aims to balance response quality, execution speed, resource consumption, and model availability.

---

## 🗄️ Schema Engine & Chat Database

### Schema Engine

The Schema Engine provides the AI Core with an understanding of the underlying database structure.

Its responsibilities include:

- Schema Discovery.
- Table and Column Metadata.
- Schema Loading.
- Schema Formatting.
- Schema Retrieval.
- Schema Validation.
- Schema Caching.

### Chat Database

The Chat Database enables users to interact with structured databases using natural language.

**Processing workflow:**

```text
Natural Language Question
          |
          v
    Schema Retrieval
          |
          v
     LLM SQL Generation
          |
          v
       SQL Validation
          |
          v
   PostgreSQL Execution
          |
          v
      Query Results
```

Core components:

- ChatDatabaseService.
- PromptBuilder.
- LLMSQLGenerator.
- SQLValidator.
- PostgresExecutor.
- CSV Ingestion.

**Database technology:** Supabase / PostgreSQL.

---

## 🔀 Query Engine

The Query Engine manages how database-related requests are classified, routed, and executed.

Its main components include:

- Query Classifier.
- Query Router.
- Orchestrator.
- Context Builder.
- Chat Database Adapter.
- Execution Manager.
- Logging.

It separates query orchestration from SQL generation and execution, improving modularity and maintainability.

---

## 🧠 Memory Management

The Memory module provides the foundation for maintaining relevant conversational context and retrieving information when needed.

Its internal components include:

- MemoryService.
- MemoryRepository.
- DTOs.
- Entities.
- Cache.
- Retriever.

The objective is to support contextual interactions and future memory-driven agent workflows.

---

## 📄 RAG Integration

The AI Core integrates with an independently developed RAG Backend to enable document-based intelligence.

My responsibility in this area focuses on connecting the retrieval capabilities to the Multi-Agent System.

The integration allows the AI Core to:

- Route document-related requests to the RAG service.
- Receive retrieved document information.
- Pass retrieved context to the Analyzer.
- Use document-based information in report generation.
- Support document-only analytical requests.
- Combine database and document information when required.

The AI Core also includes a Proxy integration mechanism that routes RAG requests to the external RAG Backend.

**Important:** The internal RAG processing pipeline is developed separately and is not part of my individual implementation scope.

---

## 🛡️ Reliability & Result Contracts

### Planner Resilience

The Planner includes reliability mechanisms designed to handle temporary LLM failures and delayed responses.

Implemented mechanisms:

- Timeout.
- Retry.
- Error Handling.

### Clarification Handling

Ambiguous user requests are handled through clarification instead of generating unsupported assumptions.

### Unified ToolResult Contract

The system uses a unified result structure to standardize communication between internal tools and the consuming application.

Core fields:

| Field | Description |
|---|---|
| `status` | Execution status |
| `answer` | Generated answer |
| `chart` | Chart-related data |
| `trace` | Execution trace |
| `warnings` | Warnings and execution notes |

This contract improves consistency across the AI Core execution workflow.

---

## 🔄 Execution Workflow

A typical analytical request follows this process:

1. **Request Reception:** The AI Core receives a natural language question.
2. **Planning:** The Planner understands the request and creates an execution plan.
3. **Tool Selection:** The appropriate tools are selected.
4. **Data Retrieval:** The system retrieves information through the database query path, RAG integration, or both.
5. **Analysis:** The Analyzer processes the retrieved information.
6. **Validation:** The Result Validator checks the analytical outputs.
7. **Reporting:** The Reporter generates the final structured response.
8. **Result Delivery:** The final result is returned through the standardized result contract.

---

## 🧰 Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| AI Framework / API Layer | FastAPI |
| LLM Integration | Groq, Gemini, OpenRouter, Ollama |
| Language Models | Qwen 2.5 |
| Database | Supabase / PostgreSQL |
| Query Language | SQL |
| Architecture | Modular Architecture |
| AI Design | Multi-Agent Systems |
| Retrieval Integration | RAG |
| Execution Management | Timeout, Retry, Error Handling |

---

## 🚧 Current Development Status

The AI Core has progressed through the development of its main intelligence components and the integration of its execution workflow.

### Implemented Development Areas

- Modular AI Core architecture.
- LLM provider integration.
- Multi-model allocation strategy.
- Planner resilience mechanisms.
- Ambiguity detection and clarification.
- Multi-Agent architecture.
- Analyzer and Reporter agents.
- Independent Result Validator agent.
- Unified ToolResult contract.
- Schema Engine structure.
- Natural Language to SQL processing components.
- Query Engine architecture.
- Memory module structure.
- RAG integration and request routing.
- Backend service coordination.

### Current Focus

The current development focus is on:

- End-to-end workflow validation.
- Database query accuracy.
- Agent coordination and execution consistency.
- Result validation reliability.
- Database and document integration testing.
- Memory behavior validation.
- Error handling and execution stability.

---

## 🔮 Future Development

The next development objectives for the AI Core include:

1. Further improving multi-agent coordination.
2. Strengthening SQL generation and validation.
3. Improving database schema understanding.
4. Enhancing analytical reasoning and insight generation.
5. Improving result validation and source grounding.
6. Expanding contextual memory capabilities.
7. Strengthening database and RAG combined workflows.
8. Conducting comprehensive integration and performance testing.

---

## 🌍 Project Vision

The long-term vision is to provide a configurable AI-powered Business Intelligence intelligence layer that can be integrated into different organizational environments.

Potential application domains include:

- Universities and Educational Institutions.
- Banking and Financial Institutions.
- Hospitals and Healthcare Organizations.
- Enterprises and Business Organizations.

The AI Core is designed to provide the intelligent reasoning, orchestration, and analytical capabilities that make natural language-driven business intelligence possible.

---

## 👨‍💻 Individual Contribution

**Developer:** Nader Al Shawky

**Primary Focus:** AI Core & Multi-Agent Intelligence Development

**Main Areas of Responsibility:**

- LLM Integration.
- Schema Engine.
- Chat Database.
- Query Engine.
- Multi-Agent Orchestration.
- AI Planning and Execution.
- Analytical Reasoning.
- Result Validation.
- Report Generation.
- Memory Management.
- RAG Integration.

---

<p align="center">

**Building the Intelligence Behind Data-Driven Decisions.**

*AI Core — From Natural Language to Intelligent Analysis.*

</p>

 (PowerShell):
.\venv\Scripts\Activate
