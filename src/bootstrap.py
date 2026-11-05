from __future__ import annotations

import logging
import os
from dotenv import load_dotenv

# LLM Imports
from src.modules.llm.application.prompt_builder import PromptBuilder
from src.modules.llm.application.services import LLMService
from src.modules.llm.domain.value_objects import ProviderName
from src.modules.llm.infrastructure.config.provider_config import ProviderConfig
from src.modules.llm.infrastructure.factory import ProviderFactory
from src.modules.llm.infrastructure.health import HealthMonitor
from src.modules.llm.infrastructure.providers.provider_registry import PROVIDERS
from src.modules.llm.infrastructure.router import DefaultLLMRouter

# Schema Engine Imports
from src.modules.schema_engine.application.services import SchemaService
from src.modules.schema_engine.infrastructure.retriever import KeywordSchemaRetriever
from src.modules.schema_engine.infrastructure.relationship_mapper import RelationshipMapper
from src.modules.schema_engine.infrastructure.schema_cache import SchemaCache
from src.modules.schema_engine.infrastructure.schema_formatter import SchemaFormatter
from src.modules.schema_engine.infrastructure.schema_loader import PostgresSchemaLoader
from src.modules.schema_engine.infrastructure.validator import DefaultSchemaValidator

# Chat Database Imports
from src.modules.chat_database.application.prompt_builder import SQLPromptBuilder
from src.modules.chat_database.application.services import ChatDatabaseService
from src.modules.chat_database.config.providers import ProviderFactory as ChatDatabaseProviderFactory
from src.modules.chat_database.config.settings import ChatDatabaseSettings
from src.modules.chat_database.infrastructure.database import Database
from src.modules.chat_database.infrastructure.postgres_executor import PostgreSQLExecutor
from src.modules.chat_database.infrastructure.result_formatter import DefaultResultFormatter
from src.modules.chat_database.infrastructure.sql_validator import DefaultSQLValidator

# Memory Imports
from src.modules.memory.application.services import MemoryService
from src.modules.memory.infrastructure.memory_repository import (
    InMemoryRepository,
    SQLMemoryRepository,
    SemanticMemoryRepository,
)

# Query Engine Imports
from src.modules.query_engine.application.orchestrator import QueryEngineOrchestrator
from src.modules.query_engine.application.query_classifier import DefaultQueryClassifier
from src.modules.query_engine.application.query_context_builder import DefaultQueryContextBuilder
from src.modules.query_engine.application.query_router import QueryRouter
from src.modules.query_engine.domain.interfaces import QueryEngine
from src.modules.query_engine.infrastructure.chat_database_adapter import ChatDatabaseAdapter
from src.modules.query_engine.infrastructure.query_execution_manager import DefaultQueryExecutionManager
from src.modules.query_engine.infrastructure.query_logger import DefaultQueryLogger
from src.modules.query_engine.infrastructure.query_result_mapper import DefaultQueryResultMapper

# Multi-Agent Imports
from src.modules.multi_agent.application.agent_service import AgentService
from src.modules.multi_agent.agents.analyzer_agent import AnalyzerAgent
from src.modules.multi_agent.agents.reporter_agent import ReporterAgent
from src.modules.multi_agent.agents.result_validator import ResultValidatorAgent

# Environment
load_dotenv()
logger = logging.getLogger(__name__)

# Singleton Instances
_llm_service: LLMService | None = None
_database: Database | None = None
_schema_service: SchemaService | None = None
_chat_database_service: ChatDatabaseService | None = None
_memory_service: MemoryService | None = None
_query_engine: QueryEngine | None = None
_agent_service: AgentService | None = None

# Provider Configuration
PROVIDER_CONFIG = {
    ProviderName.OPENAI: {
        "env": "OPENAI_API_KEY",
        "model_env": "OPENAI_MODEL",
        "default_model": "gpt-4.1-mini",
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
    ProviderName.GEMINI: {
        "env": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL",
        "default_model": "gemini-3.8-flash",
        "requires_api_key": True,
    },
}

def _get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is missing.")
    return database_url.strip()

def _get_env_model(provider: ProviderName, default_model: str) -> str:
    provider_config = PROVIDER_CONFIG.get(provider, {})
    model_env = provider_config.get("model_env")
    if model_env:
        model = os.getenv(model_env)
        if model:
            return model.strip()
    return default_model

def _get_configured_llm_provider() -> ProviderName:
    configured = os.getenv("MODEL_PROVIDER") or os.getenv("LLM_PROVIDER")
    if configured:
        normalized = configured.strip().lower()
        for provider in ProviderName:
            if provider.value.lower() == normalized or provider.name.lower() == normalized:
                return provider
        raise RuntimeError(f"Unsupported model provider: {configured}")

    fallback_order = [
        ProviderName.OLLAMA,
        ProviderName.OPENROUTER,
        ProviderName.OPENAI,
        ProviderName.DEEPSEEK,
        ProviderName.KIMI,
        ProviderName.GEMINI,
    ]

    for provider in fallback_order:
        config = PROVIDER_CONFIG.get(provider, {})
        env_name = config.get("env")
        requires_api_key = config.get("requires_api_key", True)

        if not requires_api_key:
            return provider
        if env_name and os.getenv(env_name):
            return provider

    raise RuntimeError("No configured LLM provider found.")

def _build_factory() -> ProviderFactory:
    factory = ProviderFactory()
    for provider, config in PROVIDER_CONFIG.items():
        requires_api_key = config.get("requires_api_key", True)
        env_name = config.get("env")
        api_key = os.getenv(env_name) if env_name else None

        if requires_api_key and not api_key:
            continue

        provider_info = PROVIDERS.get(provider.value)
        if provider_info is None:
            continue

        provider_class = provider_info.get("provider")
        if provider_class is None:
            continue

        base_url = provider_info.get("base_url")
        model = _get_env_model(provider=provider, default_model=config["default_model"])

        provider_instance = provider_class(
            ProviderConfig(
                provider=provider,
                api_key=(api_key or "ollama-local-placeholder"),
                base_url=base_url,
                default_model=model,
            )
        )
        factory.register(provider_instance)
    return factory

def create_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is not None:
        return _llm_service

    factory = _build_factory()
    if not factory.providers:
        raise RuntimeError("No LLM providers are configured.")

    router = DefaultLLMRouter(factory)
    _llm_service = LLMService(router=router, prompt_builder=PromptBuilder())
    return _llm_service

def create_database() -> Database:
    global _database
    if _database is not None:
        return _database

    database_url = _get_database_url()
    debug = os.getenv("DEBUG", "false").strip().lower() == "true"
    
    # 🔥 التعديل هنا: إضافة pool_pre_ping و pool_recycle
    _database = Database(
        database_url=database_url,
        echo=debug,
        pool_pre_ping=True,  # يتحقق من الاتصال قبل كل استعلام
        pool_recycle=300,    # يعيد تدوير الاتصال كل 5 دقايق
    )
    logger.info("[Bootstrap] Supabase PostgreSQL database configured with pool_pre_ping=True.")
    return _database

def create_schema_service() -> SchemaService:
    global _schema_service
    if _schema_service is not None:
        return _schema_service

    database = create_database()
    _schema_service = SchemaService(
        loader=PostgresSchemaLoader(database=database),
        cache=SchemaCache(),
        searcher=KeywordSchemaRetriever(),
        formatter=SchemaFormatter(),
        validator=DefaultSchemaValidator(),
        relationship_mapper=RelationshipMapper(),
    )
    return _schema_service

def create_chat_database_service() -> ChatDatabaseService:
    global _chat_database_service
    if _chat_database_service is not None:
        return _chat_database_service

    database_url = _get_database_url()
    llm_service = create_llm_service()
    schema_service = create_schema_service()
    configured_provider = _get_configured_llm_provider()
    default_settings = ChatDatabaseSettings(database_url=database_url)

    settings = ChatDatabaseSettings(
        database_url=database_url,
        llm_provider=configured_provider,
        llm_model=_get_env_model(
            provider=configured_provider,
            default_model=PROVIDER_CONFIG[configured_provider]["default_model"],
        ),
        temperature=default_settings.temperature,
        max_tokens=default_settings.max_tokens,
        query_timeout_seconds=default_settings.query_timeout_seconds,
        max_returned_rows=default_settings.max_returned_rows,
        schema_cache_ttl=default_settings.schema_cache_ttl,
        allow_only_select=default_settings.allow_only_select,
        enable_sql_validation=default_settings.enable_sql_validation,
        inject_limit_if_missing=default_settings.inject_limit_if_missing,
        default_limit=default_settings.default_limit,
        enable_logging=default_settings.enable_logging,
        enable_metrics=default_settings.enable_metrics,
        debug=default_settings.debug,
    )

    provider_factory = ChatDatabaseProviderFactory(settings=settings, llm_service=llm_service)
    sql_generator = provider_factory.create_sql_generator()

    _chat_database_service = ChatDatabaseService(
        schema_service=schema_service,
        prompt_builder=SQLPromptBuilder(),
        sql_generator=sql_generator,
        sql_validator=DefaultSQLValidator(),
        sql_executor=PostgreSQLExecutor(database=create_database(), max_rows=settings.max_returned_rows),
        result_formatter=DefaultResultFormatter(),
    )
    logger.info("[Bootstrap] ChatDatabaseService created using Supabase PostgreSQL.")
    return _chat_database_service

def create_memory_service() -> MemoryService:
    global _memory_service
    if _memory_service is not None:
        return _memory_service

    repository = InMemoryRepository()
    _memory_service = MemoryService(repository=repository)
    logger.info("[Bootstrap] In-Memory Repository initialized for stability.")
    return _memory_service

def create_agent_service() -> AgentService:
    global _agent_service
    if _agent_service is not None:
        return _agent_service

    llm_service = create_llm_service()
    query_engine = create_query_engine()
    memory_service = create_memory_service()

    validator = ResultValidatorAgent(llm_service=llm_service)

    _agent_service = AgentService(
        llm_service=llm_service,
        query_engine=query_engine,
        memory_service=memory_service,
        rag_service="integrated",
        validator_agent=validator,
    )
    logger.info("[Bootstrap] AgentService created successfully with DB & RAG & Validator & Memory.")
    return _agent_service

def create_query_engine() -> QueryEngine:
    global _query_engine
    if _query_engine is not None:
        return _query_engine

    logger.info("[Bootstrap] Creating QueryEngine (Routing Hub).")

    result_mapper = DefaultQueryResultMapper()
    query_classifier = DefaultQueryClassifier()
    context_builder = DefaultQueryContextBuilder()
    execution_manager = DefaultQueryExecutionManager()
    query_logger = DefaultQueryLogger()

    chat_database_service = create_chat_database_service()
    chat_database_adapter = ChatDatabaseAdapter(
        chat_database_service=chat_database_service,
        result_mapper=result_mapper,
    )

    adapters = {
        chat_database_adapter.source_name: chat_database_adapter,
    }

    query_router = QueryRouter(adapters=adapters)

    _query_engine = QueryEngineOrchestrator(
        router=query_router,
        classifier=query_classifier,
        context_builder=context_builder,
        execution_manager=execution_manager,
        query_logger=query_logger,
    )

    logger.info("[Bootstrap] QueryEngine created successfully.")
    return _query_engine

async def close_database() -> None:
    global _database
    if _database is None:
        return
    try:
        await _database.dispose()
        logger.info("[Bootstrap] Supabase PostgreSQL connection pool disposed.")
    except Exception:
        logger.exception("[Bootstrap] Failed to dispose Supabase PostgreSQL connection pool.")
    finally:
        _database = None