
from __future__ import annotations

import asyncio
import logging
from typing import List

from src.modules.schema_engine.domain.entities import (
    DatabaseSchemaEntity,
    TableEntity,
)
from src.modules.schema_engine.domain.interfaces import (
    ISchemaCache,
    ISchemaLoader,
    ISchemaSearcher,
    ISchemaValidator,
)

logger = logging.getLogger(__name__)


class SchemaService:
    """
    Application service responsible for loading, caching, retrieving,
    formatting, and validating database schema metadata.

    Compatible with the existing Schema Engine interfaces and
    ChatDatabaseService integration.
    """

    def __init__(
        self,
        loader: ISchemaLoader,
        cache: ISchemaCache,
        searcher: ISchemaSearcher,
        formatter,
        validator: ISchemaValidator,
        relationship_mapper,
    ) -> None:
        self.loader = loader
        self.cache = cache
        self.searcher = searcher
        self.formatter = formatter
        self.validator = validator
        self.relationship_mapper = relationship_mapper

        # Prevent duplicate concurrent schema loads.
        self._load_lock = asyncio.Lock()

    async def get_or_load_schema(
        self,
        force_reload: bool = False,
    ) -> DatabaseSchemaEntity:
        """
        Return the cached schema or load a fresh schema.

        A failed reload does not overwrite the cache with invalid data.
        """

        if not force_reload:
            cached_schema = self.cache.get()

            if cached_schema is not None:
                logger.debug(
                    "[Schema Service] Schema cache hit."
                )
                return cached_schema

        async with self._load_lock:
            # Another request may have populated the cache while
            # this request was waiting for the lock.
            if not force_reload:
                cached_schema = self.cache.get()

                if cached_schema is not None:
                    logger.debug(
                        "[Schema Service] Schema cache hit after lock."
                    )
                    return cached_schema

            logger.info(
                "[Schema Service] Loading schema from database."
            )

            try:
                schema = await self.loader.load_schema()

                if not isinstance(schema, DatabaseSchemaEntity):
                    raise TypeError(
                        "Schema loader must return "
                        "DatabaseSchemaEntity; received "
                        f"{type(schema).__name__}."
                    )

                # Discover database relationships after schema loading.
                relations = (
                    self.relationship_mapper.discover_relations(schema)
                )

                if relations is not None:
                    schema.relations = list(relations)

                if schema.relations is None:
                    schema.relations = []

                # Cache only after successful loading and relationship mapping.
                self.cache.set(schema)

                logger.info(
                    "[Schema Service] Schema loaded successfully: "
                    "%d tables, %d views, %d relations.",
                    len(schema.tables or {}),
                    len(schema.views or {}),
                    len(schema.relations or []),
                )

                return schema

            except Exception:
                logger.exception(
                    "[Schema Service] Failed to load database schema."
                )
                raise

    async def get_relevant_schema_prompt(
        self,
        question: str,
        top_k: int = 5,
    ) -> str:
        """
        Retrieve relevant tables and format their metadata
        into context for the SQL-generation LLM.
        """

        if not isinstance(question, str) or not question.strip():
            raise ValueError(
                "question must be a non-empty string."
            )

        if (
            not isinstance(top_k, int)
            or isinstance(top_k, bool)
            or top_k <= 0
        ):
            raise ValueError(
                "top_k must be a positive integer."
            )

        schema = await self.get_or_load_schema()

        relevant_tables: List[TableEntity] = (
            self.searcher.search_relevant_tables(
                question=question.strip(),
                schema=schema,
                top_k=top_k,
            )
        )

        if relevant_tables is None:
            relevant_tables = []

        prompt = self.formatter.format_tables_to_prompt(
            relevant_tables
        )

        if not isinstance(prompt, str):
            raise TypeError(
                "Schema formatter must return str; received "
                f"{type(prompt).__name__}."
            )

        logger.debug(
            "[Schema Service] Built schema prompt for question; "
            "selected %d schema objects.",
            len(relevant_tables),
        )

        return prompt

    async def validate_query_identifiers(
        self,
        sql_query: str,
    ) -> bool:
        """
        Validate SQL identifiers against the loaded schema.

        This method must be called explicitly by the query execution
        pipeline. It does not replace the dedicated SQL safety validator
        or PostgreSQL's read-only transaction.
        """

        if not isinstance(sql_query, str) or not sql_query.strip():
            return False

        schema = await self.get_or_load_schema()

        return bool(
            self.validator.validate_sql_identifiers(
                sql_query,
                schema,
            )
        )

    async def refresh_schema(self) -> DatabaseSchemaEntity:
        """
        Clear the cache and force a fresh schema load.

        If loading fails, the exception is propagated to the caller.
        """

        self.cache.clear()

        return await self.get_or_load_schema(
            force_reload=True
        )
