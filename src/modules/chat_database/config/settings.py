from __future__ import annotations

from dataclasses import dataclass

from src.modules.llm.domain.value_objects import (
    ProviderName,
)


@dataclass(slots=True, frozen=True)
class ChatDatabaseSettings:
    """
    Chat Database configuration.

    This class centralizes all configurable values used
    by the ChatDatabase module.
    """

    # ======================================================
    # LLM
    # ======================================================

    llm_provider: ProviderName = ProviderName.OPENAI

    llm_model: str = "gpt-4.1-mini"

    temperature: float = 0.0


    max_tokens: int = 512


    # ======================================================
    # Database
    # ======================================================

    database_url: str = ""

    query_timeout_seconds: int = 30

    max_returned_rows: int = 1000

    # ======================================================
    # Schema
    # ======================================================

    schema_cache_ttl: int = 3600

    # ======================================================
    # SQL Security
    # ======================================================

    allow_only_select: bool = True

    enable_sql_validation: bool = True

    inject_limit_if_missing: bool = False

    default_limit: int = 100

    # ======================================================
    # Logging
    # ======================================================

    enable_logging: bool = True

    enable_metrics: bool = True

    # ======================================================
    # Debug
    # ======================================================

    debug: bool = False