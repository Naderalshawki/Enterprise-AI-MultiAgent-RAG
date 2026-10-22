from __future__ import annotations

from abc import ABC, abstractmethod

from .entities import (
    Question,
    SQLQuery,
    SQLResult,
    ChatDatabaseResponse,
)


# ==========================================================
# SQL Generator
# ==========================================================

class SQLGenerator(ABC):
    """
    Generates SQL from a prepared prompt.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
    ) -> SQLQuery:
        """
        Generate SQL from the prepared prompt.
        """
        raise NotImplementedError


# ==========================================================
# SQL Validator
# ==========================================================

class SQLValidator(ABC):
    """
    Validates generated SQL before execution.
    """

    @abstractmethod
    async def validate(
        self,
        query: SQLQuery,
    ) -> SQLQuery:
        """
        Validate SQL query.
        """
        raise NotImplementedError


# ==========================================================
# SQL Executor
# ==========================================================

class SQLExecutor(ABC):
    """
    Executes validated SQL against the database.
    """

    @abstractmethod
    async def execute(
        self,
        query: SQLQuery,
    ) -> SQLResult:
        """
        Execute SQL query.
        """
        raise NotImplementedError


# ==========================================================
# Result Formatter
# ==========================================================

class ResultFormatter(ABC):
    """
    Formats SQL execution results into a unified response.
    """

    @abstractmethod
    async def format(
        self,
        question: Question,
        query: SQLQuery,
        result: SQLResult,
    ) -> ChatDatabaseResponse:
        """
        Format SQL execution result.
        """
        raise NotImplementedError


# ==========================================================
# Database Health Checker
# ==========================================================

class DatabaseHealthChecker(ABC):
    """
    Checks database connectivity and availability.
    """

    @abstractmethod
    async def health_check(
        self,
    ) -> bool:
        """
        Return True if the database is healthy.
        """
        raise NotImplementedError