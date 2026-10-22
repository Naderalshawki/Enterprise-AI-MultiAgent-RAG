from __future__ import annotations

from src.modules.chat_database.config.settings import (
    ChatDatabaseSettings,
)

from src.modules.chat_database.infrastructure.llm_sql_generator import (
    LLMSQLGenerator,
)

from src.modules.llm.application.services import (
    LLMService,
)

from src.modules.llm.domain.value_objects import (
    ProviderName,
)


class ProviderFactory:
    """
    Creates provider-dependent infrastructure components.

    Responsibilities
    ----------------
    - Resolve the configured LLM provider.
    - Create SQL Generator instances.
    - Hide provider-specific configuration from the application layer.
    """

    def __init__(
        self,
        settings: ChatDatabaseSettings,
        llm_service: LLMService,
    ):
        self._settings = settings
        self._llm_service = llm_service

    # ======================================================
    # Public API
    # ======================================================

    def create_sql_generator(
        self,
    ) -> LLMSQLGenerator:
        """
        Create an LLM-backed SQL generator.
        """

        return LLMSQLGenerator(
            llm_service=self._llm_service,
            provider=self.provider,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    # ======================================================
    # Configuration Accessors
    # ======================================================

    @property
    def provider(
        self,
    ) -> ProviderName:
        return self._settings.llm_provider

    @property
    def model(
        self,
    ) -> str:
        return self._settings.llm_model

    @property
    def temperature(
        self,
    ) -> float:
        return self._settings.temperature

    @property
    def max_tokens(
        self,
    ) -> int:
        return self._settings.max_tokens