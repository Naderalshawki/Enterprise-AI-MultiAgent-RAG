from dataclasses import dataclass, field


from src.modules.llm.domain.value_objects import (
    ProviderName,
)


@dataclass(slots=True)
class ProviderConfig:
    """
    Configuration for an AI Provider.
    """

    provider: ProviderName

    api_key: str

    default_model: str

    base_url: str | None = None

    timeout: float = 60.0

    organization: str | None = None

    extra_headers: dict[str, str] = field(
        default_factory=dict,
    )