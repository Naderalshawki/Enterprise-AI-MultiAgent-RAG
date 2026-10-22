from __future__ import annotations

import logging
import re

from src.modules.chat_database.domain.entities import SQLQuery
from src.modules.chat_database.domain.exceptions import SQLGenerationError
from src.modules.chat_database.domain.interfaces import SQLGenerator
from src.modules.chat_database.domain.value_objects import SQLDialect

from src.modules.llm.application.services import LLMService
from src.modules.llm.domain.entities import LLMMessage, LLMRequest
from src.modules.llm.domain.value_objects import ProviderName, Role

logger = logging.getLogger(__name__)


class LLMSQLGenerator(SQLGenerator):
    """Generate PostgreSQL SQL through the shared LLM service."""

    def __init__(
        self,
        *,
        llm_service: LLMService,
        provider: ProviderName,
        model: str,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> None:
        if not 0.0 <= temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        if max_tokens is not None and max_tokens < 1:
            raise ValueError("max_tokens must be a positive integer or None")
        if not model or not model.strip():
            raise ValueError("model must be a non-empty string")

        self._llm = llm_service
        self._provider = provider
        self._model = model.strip()
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def generate(self, prompt: str) -> SQLQuery:
        """Generate a SQLQuery from the supplied SQL prompt."""
        if not isinstance(prompt, str) or not prompt.strip():
            raise SQLGenerationError("SQL generation prompt is empty.")

        messages = [
            LLMMessage(role=Role.USER, content=prompt.strip())
        ]
        base_tokens = self._max_tokens or 1024
        request = LLMRequest(
            provider=self._provider,
            model=self._model,
            temperature=self._temperature,
            max_tokens=base_tokens,
            messages=messages,
            metadata={"task": "sql_generation"},
        )

        try:
            response = await self._llm.generate(request)
            content = getattr(response, "content", None)
            sql = self._clean(content if isinstance(content, str) else "")

            # A reasoning model may use the entire completion budget before it
            # emits the final SQL. Retry once with a larger budget. The provider
            # applies low reasoning effort only to this tagged SQL request.
            if not sql:
                retry_tokens = min(max(base_tokens * 2, 2048), 4096)
                if retry_tokens > base_tokens:
                    logger.warning(
                        "Empty SQL response; retrying once | provider=%s "
                        "model=%s max_tokens=%s retry_max_tokens=%s "
                        "finish_reason=%s completion_tokens=%s",
                        getattr(self._provider, "value", str(self._provider)),
                        self._model,
                        base_tokens,
                        retry_tokens,
                        getattr(response, "finish_reason", None),
                        getattr(getattr(response, "usage", None), "completion_tokens", None),
                    )
                    retry_request = LLMRequest(
                        provider=self._provider,
                        model=self._model,
                        temperature=self._temperature,
                        max_tokens=retry_tokens,
                        messages=messages,
                        metadata={"task": "sql_generation", "retry": True},
                    )
                    response = await self._llm.generate(retry_request)
                    content = getattr(response, "content", None)
                    sql = self._clean(content if isinstance(content, str) else "")

            if not sql:
                finish_reason = getattr(response, "finish_reason", None)
                usage = getattr(response, "usage", None)
                logger.error(
                    "SQL generation returned empty content | provider=%s "
                    "model=%s finish_reason=%s completion_tokens=%s max_tokens=%s",
                    getattr(self._provider, "value", str(self._provider)),
                    self._model,
                    finish_reason,
                    getattr(usage, "completion_tokens", None),
                    min(max(base_tokens * 2, 2048), 4096),
                )
                raise SQLGenerationError(
                    "The LLM returned empty SQL after one retry. "
                    "Check the server log for finish_reason and token usage."
                )

            provider_name = getattr(self._provider, "value", str(self._provider))
            return SQLQuery(
                query=sql,
                dialect=SQLDialect.POSTGRESQL,
                generated_by=provider_name,
                model=self._model,
                metadata={
                    "generator": self.__class__.__name__,
                    "provider": provider_name,
                    "dialect": SQLDialect.POSTGRESQL.value,
                    "temperature": self._temperature,
                    "max_tokens": getattr(request, "max_tokens", base_tokens),
                },
            )

        except SQLGenerationError:
            raise
        except Exception as exc:
            provider_name = getattr(self._provider, "value", str(self._provider))
            logger.exception(
                "SQL generation failed using provider=%s model=%s",
                provider_name,
                self._model,
            )
            raise SQLGenerationError(
                f"SQL generation failed with provider '{provider_name}'."
            ) from exc

    @staticmethod
    def _clean(content: str) -> str:
        """Remove surrounding Markdown fences without rewriting SQL."""
        sql = content.strip().lstrip("\ufeff")
        if not sql:
            return ""

        fence_match = re.search(
            r"```(?:sql|postgresql|postgres)?\s*\n?(.*?)\n?```",
            sql,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if fence_match:
            sql = fence_match.group(1).strip()

        sql = re.sub(
            r"^SQL\s*:\s*",
            "",
            sql,
            count=1,
            flags=re.IGNORECASE,
        )
        return sql.strip()
