from src.modules.llm.domain.interfaces import (
    LLMProvider,
    LLMRouter,
)

from src.modules.llm.domain.value_objects import (
    ProviderName,
)

from src.modules.llm.infrastructure.factory import (
    ProviderFactory,
)


class DefaultLLMRouter(LLMRouter):
    """
    Default implementation of the LLM Router.
    """

    def __init__(
        self,
        factory: ProviderFactory,
    ):
        self.factory = factory

    # ==========================================================
    # Provider
    # ==========================================================

    def get_provider(
        self,
        provider: ProviderName,
    ) -> LLMProvider:

        return self.factory.get(provider)

    # ==========================================================
    # Default
    # ==========================================================

    def get_default_provider(
        self,
    ) -> LLMProvider:

        return self.factory.get_default()

    # ==========================================================
    # All Providers
    # ==========================================================

    def get_all_providers(
        self,
    ) -> list[LLMProvider]:

        return list(
            self.factory.providers.values()
        )