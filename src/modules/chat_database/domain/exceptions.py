from __future__ import annotations


# ==========================================================
# Base Exception
# ==========================================================

class ChatDatabaseError(Exception):
    """
    Base exception for the Chat Database module.
    """

    pass


# ==========================================================
# Question Errors
# ==========================================================

class InvalidQuestionError(ChatDatabaseError):
    """
    Raised when a user question is invalid.
    """

    pass


# ==========================================================
# SQL Generation Errors
# ==========================================================

class SQLGenerationError(ChatDatabaseError):
    """
    Raised when SQL generation fails.
    """

    pass


# ==========================================================
# SQL Validation Errors
# ==========================================================

class SQLValidationError(ChatDatabaseError):
    """
    Base exception for SQL validation failures.
    """

    pass


class UnsafeSQLQueryError(SQLValidationError):
    """
    Raised when an unsafe SQL statement is detected.
    """

    pass


class UnsupportedSQLDialectError(SQLValidationError):
    """
    Raised when the SQL dialect is not supported.
    """

    pass


# ==========================================================
# SQL Execution Errors
# ==========================================================

class SQLExecutionError(ChatDatabaseError):
    """
    Raised when SQL execution fails.
    """

    pass


class EmptyResultError(SQLExecutionError):
    """
    Raised when the executed query returns no rows.
    """

    pass


# ==========================================================
# Database Errors
# ==========================================================

class DatabaseConnectionError(ChatDatabaseError):
    """
    Raised when a database connection cannot be established.
    """

    pass


class DatabaseTimeoutError(DatabaseConnectionError):
    """
    Raised when a database operation times out.
    """

    pass


class UnsupportedDatabaseProviderError(DatabaseConnectionError):
    """
    Raised when the configured database provider is unsupported.
    """

    pass


# ==========================================================
# Result Formatting Errors
# ==========================================================

class ResultFormattingError(ChatDatabaseError):
    """
    Raised when formatting the SQL execution result fails.
    """

    pass


# ==========================================================
# Configuration Errors
# ==========================================================

class ConfigurationError(ChatDatabaseError):
    """
    Raised when the Chat Database configuration is invalid.
    """

    pass


# ==========================================================
# Service Errors
# ==========================================================

class ChatDatabaseServiceError(ChatDatabaseError):
    """
    Raised when the Chat Database service fails.
    """

    pass