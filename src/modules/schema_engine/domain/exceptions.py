from __future__ import annotations

class SchemaEngineError(Exception):
    """Base exception for all schema engine errors."""
    pass

class SchemaLoadError(SchemaEngineError):
    """Raised when loading schema from database fails."""
    pass

class SchemaValidationError(SchemaEngineError):
    """Raised when schema or SQL validation fails."""
    pass