from src.modules.chat_database.domain.value_objects import (
    DatabaseProvider,
    SQLDialect,
    LLMProvider,
)


# ==========================================================
# Database
# ==========================================================

DEFAULT_DATABASE_PROVIDER = (
    DatabaseProvider.POSTGRESQL
)

DEFAULT_SQL_DIALECT = (
    SQLDialect.POSTGRESQL
)


# ==========================================================
# LLM
# ==========================================================

DEFAULT_LLM_PROVIDER = (
    LLMProvider.OPENAI
)

DEFAULT_LLM_MODEL = "gpt-4.1"


# ==========================================================
# SQL
# ==========================================================

DEFAULT_MAX_ROWS = 100

DEFAULT_QUERY_TIMEOUT = 30


# ==========================================================
# Validation
# ==========================================================

DEFAULT_ENABLE_SQL_VALIDATION = True


# ==========================================================
# Formatter
# ==========================================================

DEFAULT_ENABLE_RESULT_FORMATTING = True


# ==========================================================
# Logging
# ==========================================================

DEFAULT_ENABLE_LOGGING = True