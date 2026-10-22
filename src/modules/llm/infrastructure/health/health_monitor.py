from __future__ import annotations

from dataclasses import dataclass
import logging

from src.modules.llm.domain.interfaces import LLMProvider
from src.modules.llm.domain.value_objects import ProviderStatus
from src.modules.llm.infrastructure.factory import ProviderFactory


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ProviderHealth:
    """
    Health information for a single LLM provider.
    """

    provider: str
    status: ProviderStatus
    error: str | None = None


class HealthMonitor:
    """
    Monitors the health status of all registered LLM providers.

    The monitor does not create providers itself.
    It uses the existing ProviderFactory and calls
    each provider's health_check() method.
    """

    def __init__(
        self,
        factory: ProviderFactory,
    ) -> None:
        self.factory = factory

    # ==========================================================
    # Single Provider
    # ==========================================================

    async def check_provider(
        self,
        provider: LLMProvider,
    ) -> ProviderHealth:

        provider_name = provider.provider_name

        try:
            is_healthy = await provider.health_check()

            if is_healthy:
                return ProviderHealth(
                    provider=provider_name,
                    status=ProviderStatus.ONLINE,
                )

            return ProviderHealth(
                provider=provider_name,
                status=ProviderStatus.OFFLINE,
            )

        except Exception as exc:
            logger.exception(
                "Health check failed for provider '%s'",
                provider_name,
            )

            return ProviderHealth(
                provider=provider_name,
                status=ProviderStatus.OFFLINE,
                error=str(exc),
            )

    # ==========================================================
    # All Providers
    # ==========================================================

    async def check_all(
        self,
    ) -> list[ProviderHealth]:

        providers = list(
            self.factory.providers.values()
        )

        results: list[ProviderHealth] = []

        for provider in providers:
            result = await self.check_provider(
                provider
            )

            results.append(result)

        return results

    # ==========================================================
    # Provider Status
    # ==========================================================

    async def get_status(
        self,
        provider_name: str,
    ) -> ProviderHealth:

        for provider in self.factory.providers.values():

            if provider.provider_name == provider_name:
                return await self.check_provider(
                    provider
                )

        return ProviderHealth(
            provider=provider_name,
            status=ProviderStatus.UNKNOWN,
            error="Provider is not registered.",
        )