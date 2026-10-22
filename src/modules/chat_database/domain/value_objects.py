# from __future__ import annotations

# from enum import Enum


# # ==========================================================
# # Database Provider
# # ==========================================================

# class DatabaseProvider(str, Enum):
#     """
#     Supported database providers.
#     """

#     POSTGRESQL = "postgresql"

#     SUPABASE = "supabase"


# # ==========================================================
# # SQL Dialect
# # ==========================================================

# class SQLDialect(str, Enum):
#     """
#     Supported SQL dialects.
#     """

#     POSTGRESQL = "postgresql"

#     MYSQL = "mysql"

#     SQLITE = "sqlite"


# # ==========================================================
# # LLM Provider
# # ==========================================================

# class LLMProvider(str, Enum):
#     """
#     Supported LLM providers.
#     """

#     OPENAI = "openai"

#     GEMINI = "gemini"

#     GEMINI = "gemini"

#     DEEPSEEK = "deepseek"

#     KIMI = "kimi"


# # ==========================================================
# # Query Type
# # ==========================================================

# class QueryType(str, Enum):
#     """
#     Supported SQL statement types.
#     """

#     SELECT = "select"

#     INSERT = "insert"

#     UPDATE = "update"

#     DELETE = "delete"

#     CREATE = "create"

#     ALTER = "alter"

#     DROP = "drop"

#     TRUNCATE = "truncate"

#     UNKNOWN = "unknown"


# # ==========================================================
# # Validation Status
# # ==========================================================

# class ValidationStatus(str, Enum):
#     """
#     SQL validation result.
#     """

#     VALID = "valid"

#     INVALID = "invalid"

#     BLOCKED = "blocked"


# # ==========================================================
# # SQL Safety Level
# # ==========================================================

# class SQLSafetyLevel(str, Enum):
#     """
#     SQL safety classification.
#     """

#     SAFE = "safe"

#     WARNING = "warning"

#     DANGEROUS = "dangerous"


# # ==========================================================
# # Execution Status
# # ==========================================================

# class ExecutionStatus(str, Enum):
#     """
#     SQL execution status.
#     """

#     SUCCESS = "success"

#     FAILED = "failed"


# # ==========================================================
# # Result Format
# # ==========================================================

# class ResultFormat(str, Enum):
#     """
#     Supported result formats.
#     """

#     TABLE = "table"

#     JSON = "json"

#     TEXT = "text"


# # ==========================================================
# # Chat Database Intent
# # ==========================================================

# class ChatDatabaseIntent(str, Enum):
#     """
#     Supported Chat Database intents.
#     """

#     SQL_QUERY = "sql_query"

#     DATABASE_INFO = "database_info"

#     SCHEMA_INFO = "schema_info"


# # ==========================================================
# # Sort Order
# # ==========================================================

# class SortOrder(str, Enum):
#     """
#     SQL sorting order.
#     """

#     ASC = "ASC"

#     DESC = "DESC"







from __future__ import annotations

from enum import Enum


# ==========================================================
# Database Provider
# ==========================================================

class DatabaseProvider(str, Enum):
    """
    Supported database providers.
    """

    POSTGRESQL = "postgresql"

    SUPABASE = "supabase"


# ==========================================================
# SQL Dialect
# ==========================================================

class SQLDialect(str, Enum):
    """
    Supported SQL dialects.
    """

    POSTGRESQL = "postgresql"

    MYSQL = "mysql"

    SQLITE = "sqlite"


# ==========================================================
# LLM Provider
# ==========================================================

class LLMProvider(str, Enum):
    """
    Supported LLM providers.
    """

    OPENAI = "openai"

    GEMINI = "gemini"

    gemini = "gemini"

    DEEPSEEK = "deepseek"

    KIMI = "kimi"


# ==========================================================
# Query Type
# ==========================================================

class QueryType(str, Enum):
    """
    Supported SQL statement types.
    """

    SELECT = "select"

    INSERT = "insert"

    UPDATE = "update"

    DELETE = "delete"

    CREATE = "create"

    ALTER = "alter"

    DROP = "drop"

    TRUNCATE = "truncate"

    UNKNOWN = "unknown"


# ==========================================================
# Validation Status
# ==========================================================

class ValidationStatus(str, Enum):
    """
    SQL validation result.
    """

    VALID = "valid"

    INVALID = "invalid"

    BLOCKED = "blocked"


# ==========================================================
# SQL Safety Level
# ==========================================================

class SQLSafetyLevel(str, Enum):
    """
    SQL safety classification.
    """

    SAFE = "safe"

    WARNING = "warning"

    DANGEROUS = "dangerous"


# ==========================================================
# Execution Status
# ==========================================================

class ExecutionStatus(str, Enum):
    """
    SQL execution status.
    """

    SUCCESS = "success"

    FAILED = "failed"


# ==========================================================
# Result Format
# ==========================================================

class ResultFormat(str, Enum):
    """
    Supported result formats.
    """

    TABLE = "table"

    JSON = "json"

    TEXT = "text"


# ==========================================================
# Chat Database Intent
# ==========================================================

class ChatDatabaseIntent(str, Enum):
    """
    Supported Chat Database intents.
    """

    SQL_QUERY = "sql_query"

    DATABASE_INFO = "database_info"

    SCHEMA_INFO = "schema_info"


# ==========================================================
# Sort Order
# ==========================================================

class SortOrder(str, Enum):
    """
    SQL sorting order.
    """

    ASC = "ASC"

    DESC = "DESC"