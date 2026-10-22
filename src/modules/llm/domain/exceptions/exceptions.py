class LLMEngineError(Exception):
    """Base exception for LLM Engine."""


class ProviderError(LLMEngineError):
    """Base provider exception."""


class ProviderAuthenticationError(ProviderError):
    """Authentication failed."""


class ProviderRateLimitError(ProviderError):
    """Rate limit exceeded."""


class ProviderTimeoutError(ProviderError):
    """Provider timeout."""


class ProviderUnavailableError(ProviderError):
    """Provider unavailable."""


class ProviderQuotaExceededError(ProviderError):
    """Provider quota exceeded."""


class FeatureNotSupportedError(ProviderError):
    """Feature not supported by provider."""


class InvalidRequestError(LLMEngineError):
    """Invalid request."""