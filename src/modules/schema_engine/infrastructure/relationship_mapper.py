from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.modules.schema_engine.domain.entities import (
    ColumnEntity,
    DatabaseSchemaEntity,
    TableEntity,
)

logger = logging.getLogger(__name__)


class RelationshipMapper:
    """Build a normalized relationship list from a loaded database schema.

    Compatible with the existing SchemaService contract:
        ``discover_relations(schema) -> list[dict[str, Any]]``

    The mapper supports both representations already used in the project:
    1. ``TableEntity.foreign_keys`` populated by ``PostgresSchemaLoader``.
    2. ``ColumnEntity.is_foreign_key`` / ``ColumnEntity.references`` for older
       loaders or manually assembled schemas.

    It only maps metadata already present in ``DatabaseSchemaEntity``; it does
    not query the database or infer relationships from matching column names.
    """

    def discover_relations(
        self, schema: DatabaseSchemaEntity
    ) -> List[Dict[str, Any]]:
        """Discover foreign-key relations and store them on ``schema.relations``.

        Each relation contains the legacy ``references`` field, plus explicit
        source/target fields useful for prompts, validation, and query planning.
        Composite foreign keys produce one relation per paired column.
        """
        if not isinstance(schema, DatabaseSchemaEntity):
            raise TypeError("schema must be a DatabaseSchemaEntity")

        relations_by_key: Dict[Tuple[str, str, str, str, str], Dict[str, Any]] = {}
        objects = self._all_objects(schema)

        # Preferred source: explicit constraint metadata, including composite FKs.
        for table_name, table in objects:
            for foreign_key in table.foreign_keys or []:
                if not isinstance(foreign_key, dict):
                    logger.debug(
                        "Ignoring malformed foreign key metadata on table %s: %r",
                        table_name,
                        foreign_key,
                    )
                    continue
                self._map_constraint(
                    relations_by_key=relations_by_key,
                    source_table=table_name,
                    source_schema=self._schema_name(schema),
                    foreign_key=foreign_key,
                    table=table,
                )

        # Backward-compatible fallback: column-level references from older schemas.
        for table_name, table in objects:
            for column_name, column in table.columns.items():
                if not column.is_foreign_key or not column.references:
                    continue
                target_table, target_column, target_schema = self._parse_reference(
                    column.references
                )
                if not target_table or not target_column:
                    logger.debug(
                        "Ignoring malformed reference %r on %s.%s",
                        column.references,
                        table_name,
                        column_name,
                    )
                    continue

                relation = self._make_relation(
                    source_schema=self._schema_name(schema),
                    source_table=table_name,
                    source_column=column_name,
                    target_schema=target_schema or self._schema_name(schema),
                    target_table=target_table,
                    target_column=target_column,
                    constraint_name=None,
                    key_position=1,
                )
                self._add_relation(relations_by_key, relation)

        relations = sorted(
            relations_by_key.values(),
            key=lambda item: (
                item["from_schema"],
                item["from_table"],
                item.get("constraint_name") or "",
                item.get("key_position") or 0,
                item["from_column"],
                item["to_schema"],
                item["to_table"],
                item["to_column"],
            ),
        )
        schema.relations = relations
        logger.info(
            "[Relationship Mapper] Discovered %d foreign-key column relation(s) across %d table/view object(s).",
            len(relations),
            len(objects),
        )
        return relations

    @staticmethod
    def _all_objects(
        schema: DatabaseSchemaEntity,
    ) -> List[Tuple[str, TableEntity]]:
        """Return tables and views while avoiding duplicate object entries."""
        objects: List[Tuple[str, TableEntity]] = []
        seen: set[Tuple[str, int]] = set()
        for collection in (schema.tables, schema.views):
            for name, table in collection.items():
                identity = (name, id(table))
                if identity in seen:
                    continue
                seen.add(identity)
                objects.append((name, table))
        return objects

    def _map_constraint(
        self,
        *,
        relations_by_key: Dict[Tuple[str, str, str, str, str], Dict[str, Any]],
        source_table: str,
        source_schema: str,
        foreign_key: Dict[str, Any],
        table: TableEntity,
    ) -> None:
        target_table = self._clean_optional(foreign_key.get("referenced_table"))
        target_schema = self._clean_optional(foreign_key.get("referenced_schema")) or source_schema
        constraint_name = self._clean_optional(foreign_key.get("name"))

        source_columns = self._as_string_list(foreign_key.get("columns"))
        target_columns = self._as_string_list(foreign_key.get("referenced_columns"))

        # Some integrations may already provide explicit column-pair records.
        column_pairs = foreign_key.get("column_pairs")
        if isinstance(column_pairs, list) and column_pairs:
            for position, pair in enumerate(column_pairs, start=1):
                if not isinstance(pair, dict):
                    continue
                from_column = self._clean_optional(
                    pair.get("from_column") or pair.get("column")
                )
                to_column = self._clean_optional(
                    pair.get("to_column") or pair.get("referenced_column")
                )
                if from_column and to_column and target_table:
                    self._add_relation(
                        relations_by_key,
                        self._make_relation(
                            source_schema=source_schema,
                            source_table=source_table,
                            source_column=from_column,
                            target_schema=target_schema,
                            target_table=target_table,
                            target_column=to_column,
                            constraint_name=constraint_name,
                            key_position=self._safe_int(pair.get("position")) or position,
                        ),
                    )
            return

        if not target_table or not source_columns or not target_columns:
            logger.debug(
                "Ignoring incomplete FK metadata on %s: %r", source_table, foreign_key
            )
            return

        if len(source_columns) != len(target_columns):
            logger.warning(
                "Skipping FK %s on %s: %d source columns but %d referenced columns.",
                constraint_name or "<unnamed>",
                source_table,
                len(source_columns),
                len(target_columns),
            )
            return

        for position, (source_column, target_column) in enumerate(
            zip(source_columns, target_columns), start=1
        ):
            if source_column not in table.columns:
                logger.debug(
                    "FK %s references missing source column %s.%s; skipping pair.",
                    constraint_name or "<unnamed>",
                    source_table,
                    source_column,
                )
                continue
            self._add_relation(
                relations_by_key,
                self._make_relation(
                    source_schema=source_schema,
                    source_table=source_table,
                    source_column=source_column,
                    target_schema=target_schema,
                    target_table=target_table,
                    target_column=target_column,
                    constraint_name=constraint_name,
                    key_position=position,
                ),
            )

    @staticmethod
    def _make_relation(
        *,
        source_schema: str,
        source_table: str,
        source_column: str,
        target_schema: str,
        target_table: str,
        target_column: str,
        constraint_name: Optional[str],
        key_position: int,
    ) -> Dict[str, Any]:
        # Keep `references` for compatibility with the original implementation.
        return {
            "from_schema": source_schema,
            "from_table": source_table,
            "from_column": source_column,
            "to_schema": target_schema,
            "to_table": target_table,
            "to_column": target_column,
            "references": f"{target_table}.{target_column}",
            "qualified_references": f"{target_schema}.{target_table}.{target_column}",
            "constraint_name": constraint_name,
            "key_position": key_position,
            "relationship_type": "foreign_key",
        }

    @staticmethod
    def _add_relation(
        relations_by_key: Dict[Tuple[str, str, str, str, str], Dict[str, Any]],
        relation: Dict[str, Any],
    ) -> None:
        key = (
            relation["from_schema"],
            relation["from_table"],
            relation["from_column"],
            relation["to_schema"],
            f"{relation['to_table']}.{relation['to_column']}",
        )
        existing = relations_by_key.get(key)
        if existing is None:
            relations_by_key[key] = relation
            return

        # Constraint metadata is preferred over the legacy column fallback.
        if existing.get("constraint_name") is None and relation.get("constraint_name"):
            relations_by_key[key] = relation

    @staticmethod
    def _parse_reference(reference: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse ``table.column`` or ``schema.table.column`` references."""
        parts = [part.strip().strip('"') for part in reference.strip().split(".")]
        if len(parts) == 2 and all(parts):
            return parts[0], parts[1], None
        if len(parts) == 3 and all(parts):
            return parts[1], parts[2], parts[0]
        return None, None, None

    @staticmethod
    def _as_string_list(value: Any) -> List[str]:
        if not isinstance(value, (list, tuple)):
            return []
        result: List[str] = []
        for item in value:
            cleaned = RelationshipMapper._clean_optional(item)
            if cleaned is not None:
                result.append(cleaned)
        return result

    @staticmethod
    def _clean_optional(value: Any) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _schema_name(schema: DatabaseSchemaEntity) -> str:
        metadata = schema.metadata if isinstance(schema.metadata, dict) else {}
        name = metadata.get("schema_name")
        return str(name).strip() if name and str(name).strip() else "public"
