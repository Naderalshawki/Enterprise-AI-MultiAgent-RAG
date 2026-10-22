
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.modules.chat_database.domain.exceptions import (
    DatabaseConnectionError,
)

logger = logging.getLogger(__name__)


class Database:
    """Manage asynchronous PostgreSQL/Supabase connections and sessions."""

    def __init__(
        self,
        database_url: str,
        *,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 5,
        pool_timeout: float = 30.0,
        pool_recycle: int = 1800,
        pool_pre_ping: bool = True,
        application_name: str = "ai-bi-platform",
    ) -> None:
        if not isinstance(database_url, str) or not database_url.strip():
            raise ValueError("database_url must be a non-empty string")

        if (
            isinstance(pool_size, bool)
            or not isinstance(pool_size, int)
            or pool_size < 1
        ):
            raise ValueError("pool_size must be a positive integer")

        if (
            isinstance(max_overflow, bool)
            or not isinstance(max_overflow, int)
            or max_overflow < 0
        ):
            raise ValueError("max_overflow must be a non-negative integer")

        if pool_timeout <= 0:
            raise ValueError("pool_timeout must be greater than zero")

        if pool_recycle < 1:
            raise ValueError("pool_recycle must be a positive integer")

        try:
            url = make_url(database_url.strip())
        except Exception as exc:
            raise ValueError(
                "database_url is not a valid SQLAlchemy URL"
            ) from exc

        if url.drivername not in {
            "postgresql+asyncpg",
            "postgresql+psycopg",
        }:
            raise ValueError(
                "Database requires an async PostgreSQL URL, "
                "such as postgresql+asyncpg://..."
            )

        connect_args: dict[str, object] = {}

        if application_name.strip():
            connect_args["server_settings"] = {
                "application_name": application_name.strip()
            }

        try:
            self.engine: AsyncEngine = create_async_engine(
                url,
                echo=echo,
                pool_pre_ping=pool_pre_ping,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
                connect_args=connect_args,
            )
        except Exception as exc:
            raise DatabaseConnectionError(
                "Could not initialize the PostgreSQL connection pool. "
                "Check the database URL and installed async driver."
            ) from exc

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        self._disposed = False

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Commit on success, rollback on failure, and always close."""
        if self._disposed:
            raise DatabaseConnectionError(
                "Database engine has been disposed; "
                "create a new Database instance."
            )

        session = self.session_factory()

        try:
            yield session
            await session.commit()

        except Exception:
            try:
                await session.rollback()
            except Exception:
                logger.exception(
                    "Failed to roll back the database session."
                )
            raise

        finally:
            await session.close()

    async def health_check(self) -> bool:
        """Check whether PostgreSQL responds to a simple query."""
        try:
            async with self.session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar_one() == 1

        except SQLAlchemyError as exc:
            logger.warning(
                "PostgreSQL health check failed: %s",
                exc,
            )
            raise DatabaseConnectionError(
                "Unable to connect to PostgreSQL/Supabase. "
                "Check connectivity and database configuration."
            ) from exc

        except DatabaseConnectionError:
            raise

        except Exception as exc:
            logger.exception(
                "Unexpected PostgreSQL health-check failure."
            )
            raise DatabaseConnectionError(
                "Unexpected failure while checking the database connection."
            ) from exc

    async def dispose(self) -> None:
        """Close pooled connections and prevent further sessions."""
        if self._disposed:
            return

        try:
            await self.engine.dispose()
            self._disposed = True
            logger.info("PostgreSQL connection pool disposed.")

        except SQLAlchemyError as exc:
            logger.exception(
                "Failed to dispose the PostgreSQL connection pool."
            )
            raise DatabaseConnectionError(
                "Failed to close the PostgreSQL connection pool."
            ) from exc
