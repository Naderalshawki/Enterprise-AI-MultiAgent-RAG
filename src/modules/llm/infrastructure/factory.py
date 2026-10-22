
from src.modules.llm.domain.interfaces import LLMProvider
from src.modules.llm.domain.value_objects import ProviderName


class ProviderFactory:
    """Registry for all LLM providers."""

    def __init__(
        self,
        default_provider: ProviderName | None = None,
    ) -> None:
        self._providers: dict[ProviderName, LLMProvider] = {}
        self._default_provider = default_provider

    def register(self, provider: LLMProvider) -> None:
        name = ProviderName(provider.provider_name)
        self._providers[name] = provider

    def get(self, provider: ProviderName) -> LLMProvider:
        name = ProviderName(provider)

        try:
            return self._providers[name]
        except KeyError:
            raise ValueError(
                f"Provider '{name.value}' is not registered."
            ) from None

    def get_default(self) -> LLMProvider:
        if self._default_provider is not None:
            return self.get(self._default_provider)

        if not self._providers:
            raise ValueError("No providers registered.")

        return next(iter(self._providers.values()))

    @property
    def providers(self) -> dict[ProviderName, LLMProvider]:
        return self._providers

    def exists(self, provider: ProviderName) -> bool:
        return ProviderName(provider) in self._providers
