

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv


# ============================================================
# LLM Imports
# ============================================================

from src.modules.llm.application.prompt_builder import (
    PromptBuilder,
)

from src.modules.llm.application.services import (
    LLMService,
)

from src.modules.llm.domain.value_objects import (
    ProviderName,
)

from src.modules.llm.infrastructure.config.provider_config import (
    ProviderConfig,
)

from src.modules.llm.infrastructure.factory import (
    ProviderFactory,
)

from src.modules.llm.infrastructure.health import (
    HealthMonitor,
)

from src.modules.llm.infrastructure.providers.provider_registry import (
    PROVIDERS,
)

from src.modules.llm.infrastructure.router import (
    DefaultLLMRouter,
)


# ============================================================
# Schema Engine Imports
# ============================================================

from src.modules.schema_engine.application.services import (
    SchemaService,
)

from src.modules.schema_engine.infrastructure.retriever import (
    KeywordSchemaRetriever,
)

from src.modules.schema_engine.infrastructure.relationship_mapper import (
    RelationshipMapper,
)

from src.modules.schema_engine.infrastructure.schema_cache import (
    SchemaCache,
)

from src.modules.schema_engine.infrastructure.schema_formatter import (
    SchemaFormatter,
)

from src.modules.schema_engine.infrastructure.schema_loader import (
    PostgresSchemaLoader,
)

from src.modules.schema_engine.infrastructure.validator import (
    DefaultSchemaValidator,
)


# ============================================================
# Chat Database Imports
# ============================================================

from src.modules.chat_database.application.prompt_builder import (
    SQLPromptBuilder,
)

from src.modules.chat_database.application.services import (
    ChatDatabaseService,
)

from src.modules.chat_database.config.providers import (
    ProviderFactory as ChatDatabaseProviderFactory,
)

from src.modules.chat_database.config.settings import (
    ChatDatabaseSettings,
)

from src.modules.chat_database.infrastructure.database import (
    Database,
)

from src.modules.chat_database.infrastructure.postgres_executor import (
    PostgreSQLExecutor,
)

from src.modules.chat_database.infrastructure.result_formatter import (
    DefaultResultFormatter,
)

from src.modules.chat_database.infrastructure.sql_validator import (
    DefaultSQLValidator,
)


# ============================================================
# Memory Imports
# ============================================================

from src.modules.memory.application.services import (
    MemoryService,
)

from src.modules.memory.infrastructure.memory_repository import (
    InMemoryRepository,
)


# ============================================================
# Query Engine Imports
# ============================================================

from src.modules.query_engine.application.orchestrator import (
    QueryEngineOrchestrator,
)

from src.modules.query_engine.application.query_classifier import (
    DefaultQueryClassifier,
)

from src.modules.query_engine.application.query_context_builder import (
    DefaultQueryContextBuilder,
)

from src.modules.query_engine.application.query_router import (
    QueryRouter,
)

from src.modules.query_engine.domain.interfaces import (
    QueryEngine,
)

from src.modules.query_engine.infrastructure.chat_database_adapter import (
    ChatDatabaseAdapter,
)

from src.modules.query_engine.infrastructure.query_execution_manager import (
    DefaultQueryExecutionManager,
)

from src.modules.query_engine.infrastructure.query_logger import (
    DefaultQueryLogger,
)

from src.modules.query_engine.infrastructure.query_result_mapper import (
    DefaultQueryResultMapper,
)


# ============================================================
# Multi-Agent Imports
# ============================================================

from src.modules.multi_agent.application.agent_service import (
    AgentService,
)


# ============================================================
# Environment
# ============================================================

load_dotenv()


# ============================================================
# Logging
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# Singleton Instances
# ============================================================

_llm_service: LLMService | None = None

_database: Database | None = None

_schema_service: SchemaService | None = None

_chat_database_service: ChatDatabaseService | None = None

_memory_service: MemoryService | None = None

_query_engine: QueryEngine | None = None

_agent_service: AgentService | None = None

_health_monitor: HealthMonitor | None = None


# ============================================================
# Provider Configuration
# ============================================================

PROVIDER_CONFIG = {
    ProviderName.OPENAI: {
        "env": "OPENAI_API_KEY",
        "model_env": "OPENAI_MODEL",
        "default_model": "gpt-4.1-mini",
        "requires_api_key": True,
    },

    ProviderName.GROQ: {
        "env": "GROQ_API_KEY",
        "model_env": "GROQ_MODEL",
        "default_model": "llama3-70b-8192",
        "requires_api_key": True,
    },

    ProviderName.DEEPSEEK: {
        "env": "DEEPSEEK_API_KEY",
        "model_env": "DEEPSEEK_MODEL",
        "default_model": "deepseek-chat",
        "requires_api_key": True,
    },

    ProviderName.KIMI: {
        "env": "MOONSHOT_API_KEY",
        "model_env": "KIMI_MODEL",
        "default_model": "kimi-k3",
        "requires_api_key": True,
    },


    ProviderName.GEMINI: {
    "env": "GEMINI_API_KEY",
    "model_env": "GEMINI_MODEL",
    "default_model": "gemini-3.6-flash",
    "requires_api_key": True,
    },

    ProviderName.OPENROUTER: {
        "env": "OPENROUTER_API_KEY",
        "model_env": "OPENROUTER_MODEL_NAME",
        "default_model": "openrouter/free",
        "requires_api_key": True,
    },

    ProviderName.OLLAMA: {
        "env": "OLLAMA_API_KEY",
        "model_env": "OLLAMA_MODEL",
        "default_model": "qwen2.5-coder:7b",
        "requires_api_key": False,
    },
}


# ============================================================
# Environment Helpers
# ============================================================

def _get_database_url() -> str:
    """
    الحصول على DATABASE_URL.

    قاعدة البيانات النهائية للمشروع هي PostgreSQL
    المستضافة على Supabase.
    """

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is missing."
        )

    return database_url.strip()


def _get_env_model(
    provider: ProviderName,
    default_model: str,
) -> str:
    """
    الحصول على اسم الموديل من Environment.
    """

    provider_config = PROVIDER_CONFIG.get(
        provider,
        {},
    )

    model_env = provider_config.get(
        "model_env"
    )

    if model_env:
        model = os.getenv(model_env)

        if model:
            return model.strip()

    return default_model


def _get_configured_llm_provider() -> ProviderName:
    """
    تحديد LLM Provider الأساسي.

    الأولوية:

        MODEL_PROVIDER
              ↓
        LLM_PROVIDER
              ↓
        Provider متوفر تلقائيًا
    """

    configured = (
        os.getenv("MODEL_PROVIDER")
        or os.getenv("LLM_PROVIDER")
    )

    if configured:
        normalized = (
            configured
            .strip()
            .lower()
        )

        for provider in ProviderName:

            if provider.value.lower() == normalized:
                return provider

            if provider.name.lower() == normalized:
                return provider

        raise RuntimeError(
            "Unsupported model provider: "
            f"{configured}"
        )

    fallback_order = [
        ProviderName.OPENROUTER,
        ProviderName.GEMINI,
        ProviderName.OPENAI,
        ProviderName.GROQ,
        ProviderName.DEEPSEEK,
        ProviderName.KIMI,
        ProviderName.OLLAMA,
    ]

    for provider in fallback_order:

        config = PROVIDER_CONFIG.get(
            provider,
            {},
        )

        env_name = config.get("env")

        requires_api_key = config.get(
            "requires_api_key",
            True,
        )

        if not requires_api_key:
            return provider

        if (
            env_name
            and os.getenv(env_name)
        ):
            return provider

    raise RuntimeError(
        "No configured LLM provider found."
    )


# ============================================================
# LLM Factory Builder
# ============================================================

def _build_factory() -> ProviderFactory:
    """
    إنشاء وتسجيل LLM Providers المتاحة.
    """

    factory = ProviderFactory()

    for provider, config in PROVIDER_CONFIG.items():

        requires_api_key = config.get(
            "requires_api_key",
            True,
        )

        env_name = config.get("env")

        api_key = (
            os.getenv(env_name)
            if env_name
            else None
        )

        # ----------------------------------------------------
        # Skip unavailable provider
        # ----------------------------------------------------

        if (
            requires_api_key
            and not api_key
        ):
            continue

        # ----------------------------------------------------
        # Provider Registry
        # ----------------------------------------------------

        provider_info = PROVIDERS.get(
            provider.value
        )

        if provider_info is None:
            continue

        provider_class = provider_info.get(
            "provider"
        )

        if provider_class is None:
            continue

        base_url = provider_info.get(
            "base_url"
        )

        model = _get_env_model(
            provider=provider,
            default_model=config[
                "default_model"
            ],
        )

        provider_instance = provider_class(
            ProviderConfig(
                provider=provider,
                api_key=(
                    api_key
                    or "ollama-local-placeholder"
                ),
                base_url=base_url,
                default_model=model,
            )
        )

        factory.register(
            provider_instance
        )

    return factory


# ============================================================
# LLM Service
# ============================================================

def create_llm_service() -> LLMService:
    """
    إنشاء أو إرجاع LLMService Singleton.
    """

    global _llm_service

    if _llm_service is not None:
        return _llm_service

    factory = _build_factory()

    if not factory.providers:
        raise RuntimeError(
            "No LLM providers are configured."
        )

    router = DefaultLLMRouter(
        factory
    )

    _llm_service = LLMService(
        router=router,
        prompt_builder=PromptBuilder(),
    )

    return _llm_service


# ============================================================
# PostgreSQL / Supabase Database
# ============================================================

def create_database() -> Database:
    """
    إنشاء PostgreSQL Database.

    قاعدة البيانات النهائية:
        Supabase PostgreSQL

    لا يوجد MongoDB في هذه المعمارية.
    """

    global _database

    if _database is not None:
        return _database

    database_url = _get_database_url()

    debug = (
        os.getenv(
            "DEBUG",
            "false",
        )
        .strip()
        .lower()
        == "true"
    )

    _database = Database(
        database_url=database_url,
        echo=debug,
    )

    logger.info(
        "[Bootstrap] Supabase PostgreSQL database configured."
    )

    return _database


# ============================================================
# Schema Service
# ============================================================

def create_schema_service() -> SchemaService:
    """
    إنشاء SchemaService.

    المصدر:
        PostgreSQL / Supabase
    """

    global _schema_service

    if _schema_service is not None:
        return _schema_service

    database = create_database()

    loader = PostgresSchemaLoader(
        database=database,
    )

    cache = SchemaCache()

    searcher = KeywordSchemaRetriever()

    formatter = SchemaFormatter()

    validator = DefaultSchemaValidator()

    relationship_mapper = RelationshipMapper()

    _schema_service = SchemaService(
        loader=loader,
        cache=cache,
        searcher=searcher,
        formatter=formatter,
        validator=validator,
        relationship_mapper=relationship_mapper,
    )

    return _schema_service


# ============================================================
# Chat Database Service
# ============================================================

def create_chat_database_service() -> ChatDatabaseService:
    """
    إنشاء ChatDatabaseService.

    هذا هو المسار الرسمي والوحيد
    للوصول إلى قاعدة بيانات المشروع.

    Database:
        PostgreSQL / Supabase
    """

    global _chat_database_service

    if _chat_database_service is not None:
        return _chat_database_service

    database_url = _get_database_url()

    llm_service = create_llm_service()

    schema_service = create_schema_service()

    configured_provider = (
        _get_configured_llm_provider()
    )

    default_settings = ChatDatabaseSettings(
        database_url=database_url,
    )

    settings = ChatDatabaseSettings(
        database_url=database_url,

        llm_provider=configured_provider,

        llm_model=_get_env_model(
            provider=configured_provider,
            default_model=default_settings.llm_model,
        ),

        temperature=default_settings.temperature,

        max_tokens=default_settings.max_tokens,

        query_timeout_seconds=(
            default_settings.query_timeout_seconds
        ),

        max_returned_rows=(
            default_settings.max_returned_rows
        ),

        schema_cache_ttl=(
            default_settings.schema_cache_ttl
        ),

        allow_only_select=(
            default_settings.allow_only_select
        ),

        enable_sql_validation=(
            default_settings.enable_sql_validation
        ),

        inject_limit_if_missing=(
            default_settings.inject_limit_if_missing
        ),

        default_limit=(
            default_settings.default_limit
        ),

        enable_logging=(
            default_settings.enable_logging
        ),

        enable_metrics=(
            default_settings.enable_metrics
        ),

        debug=default_settings.debug,
    )

    # ========================================================
    # SQL Generator
    # ========================================================

    provider_factory = ChatDatabaseProviderFactory(
        settings=settings,
        llm_service=llm_service,
    )

    sql_generator = (
        provider_factory
        .create_sql_generator()
    )

    # ========================================================
    # SQL Pipeline
    # ========================================================

    prompt_builder = SQLPromptBuilder()

    sql_validator = DefaultSQLValidator()

    sql_executor = PostgreSQLExecutor(
        database=create_database(),
        max_rows=settings.max_returned_rows,
    )

    result_formatter = DefaultResultFormatter()

    # ========================================================
    # Final Service
    # ========================================================

    _chat_database_service = ChatDatabaseService(
        schema_service=schema_service,
        prompt_builder=prompt_builder,
        sql_generator=sql_generator,
        sql_validator=sql_validator,
        sql_executor=sql_executor,
        result_formatter=result_formatter,
    )

    logger.info(
        "[Bootstrap] ChatDatabaseService created "
        "using Supabase PostgreSQL."
    )

    return _chat_database_service


# ============================================================
# Query Engine
# ============================================================

def create_query_engine() -> QueryEngine:
    """
    إنشاء Query Engine النهائي.

    Architecture:

        QueryRequest
              ↓
        QueryContextBuilder
              ↓
        QueryClassifier
              ↓
        QueryExecutionManager
              ↓
        QueryRouter
              ↓
        ChatDatabaseAdapter
              ↓
        ChatDatabaseService
              ↓
        SchemaService
              ↓
        SQL Generator
              ↓
        SQL Validator
              ↓
        PostgreSQL / Supabase
              ↓
        QueryResult

    لا يوجد MongoDB.
    لا يوجد مصدر اختبار منفصل.

    Query Engine يستخدم نفس قاعدة البيانات
    النهائية الخاصة بالمشروع.
    """

    global _query_engine

    if _query_engine is not None:
        return _query_engine

    logger.info(
        "[Bootstrap] Creating QueryEngine "
        "using Chat Database / Supabase."
    )

    # ========================================================
    # Query Result Mapper
    # ========================================================

    result_mapper = DefaultQueryResultMapper()

    # ========================================================
    # Query Classifier
    # ========================================================

    query_classifier = DefaultQueryClassifier()

    # ========================================================
    # Context Builder
    # ========================================================

    context_builder = DefaultQueryContextBuilder()

    # ========================================================
    # Execution Manager
    # ========================================================

    execution_manager = (
        DefaultQueryExecutionManager()
    )

    # ========================================================
    # Query Logger
    # ========================================================

    query_logger = DefaultQueryLogger()

    # ========================================================
    # Chat Database
    # ========================================================

    chat_database_service = (
        create_chat_database_service()
    )

    # ========================================================
    # Chat Database Adapter
    # ========================================================

    chat_database_adapter = ChatDatabaseAdapter(
        chat_database_service=chat_database_service,
        result_mapper=result_mapper,
    )

    # ========================================================
    # Adapter Registry
    # ========================================================

    adapters = {
        chat_database_adapter.source_name:
            chat_database_adapter
    }

    logger.info(
        "[Bootstrap] ChatDatabase adapter registered."
    )

    # ========================================================
    # Query Router
    # ========================================================

    # QueryRouter يستقبل adapters فقط.
    #
    # لا نمرر:
    #
    #     classifier=
    #     context_builder=
    #
    # لأن Orchestrator مسؤول عنهما.

    query_router = QueryRouter(
        adapters=adapters,
    )

    # ========================================================
    # Final Query Engine
    # ========================================================

    _query_engine = QueryEngineOrchestrator(
        router=query_router,
        classifier=query_classifier,
        context_builder=context_builder,
        execution_manager=execution_manager,
        query_logger=query_logger,
    )

    logger.info(
        "[Bootstrap] QueryEngine created successfully."
    )

    return _query_engine


# ============================================================
# Memory Service
# ============================================================

def create_memory_service() -> MemoryService:
    """
    إنشاء MemoryService.

    التخزين الحالي:
        InMemoryRepository

    الذاكرة مؤقتة أثناء تشغيل التطبيق.
    ويمكن لاحقًا ربطها بقاعدة البيانات النهائية
    إذا قرر الفريق ذلك.
    """

    global _memory_service

    if _memory_service is not None:
        return _memory_service

    repository = InMemoryRepository()

    _memory_service = MemoryService(
        repository=repository,
    )

    return _memory_service


# ============================================================
# Agent Service
# ============================================================

def create_agent_service() -> AgentService:
    """
    إنشاء Multi-Agent Service.

    Architecture:

        User
          ↓
        AgentService
          ↓
        Memory
          ↓
        Planner
          ↓
        TaskExecutor
          ↓
        DatabaseTool
          ↓
        QueryEngine
          ↓
        ChatDatabase
          ↓
        Supabase PostgreSQL

    RAG:
        يتم حقنه لاحقًا عندما تصل خدمة RAG
        الحقيقية من زميل المشروع.
    """

    global _agent_service

    if _agent_service is not None:
        return _agent_service

    # ========================================================
    # LLM
    # ========================================================

    llm_service = create_llm_service()

    # ========================================================
    # Query Engine
    # ========================================================

    query_engine = create_query_engine()

    # ========================================================
    # Memory
    # ========================================================

    memory_service = create_memory_service()

    # ========================================================
    # RAG Integration Point (temporarily disabled)
    # ========================================================

    # لا ننشئ Mock لخدمة RAG، ولا نمرر خدمة غير جاهزة.
    # تبقى نقطة الحقن هذه جاهزة لدمج تنفيذ زميل المشروع لاحقًا.
    # عند توفر الخدمة الحقيقي، استبدل None بكائن الخدمة الفعلي.
    # AgentService مسؤول عن عدم تسجيل RAGTool عندما تكون الخدمة None.

    rag_service = None

    logger.info(
        "[Bootstrap] RAG is disabled; waiting for the real RAG service."
    )

    # ========================================================
    # Agent Service
    # ========================================================

    _agent_service = AgentService(
        llm_service=llm_service,
        query_engine=query_engine,
        memory_service=memory_service,
        rag_service=rag_service,
    )

    logger.info(
        "[Bootstrap] AgentService created successfully."
    )

    return _agent_service


# ============================================================
# Close Database
# ============================================================

async def close_database() -> None:
    """
    إغلاق PostgreSQL / Supabase
    عند إيقاف التطبيق.
    """

    global _database

    if _database is None:
        return

    try:
        # Database exposes dispose(), not close(). This disposes the
        # SQLAlchemy AsyncEngine connection pool cleanly.
        await _database.dispose()
        logger.info(
            "[Bootstrap] Supabase PostgreSQL connection pool disposed."
        )

    except Exception:
        logger.exception(
            "[Bootstrap] Failed to dispose "
            "Supabase PostgreSQL connection pool."
        )

    finally:
        _database = None
