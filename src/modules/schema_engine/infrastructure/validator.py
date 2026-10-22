
from __future__ import annotations

import logging
import re
from typing import Dict, Set, Tuple

from src.modules.schema_engine.domain.entities import (
    DatabaseSchemaEntity,
    TableEntity,
)
from src.modules.schema_engine.domain.interfaces import ISchemaValidator

logger = logging.getLogger(__name__)

_IDENTIFIER = r'(?:"(?:[^"]|"")+"|[A-Za-z_][A-Za-z0-9_$]*)'

_TABLE_INTRODUCER_RE = re.compile(
    rf'\b(?:FROM|JOIN|UPDATE|INTO)\s+'
    rf'(?P<name>{_IDENTIFIER}(?:\s*\.\s*{_IDENTIFIER})?)',
    re.IGNORECASE,
)

_ALIAS_RE = re.compile(
    rf'^\s*(?:AS\s+)?(?P<alias>{_IDENTIFIER})',
    re.IGNORECASE,
)

_QUALIFIED_COLUMN_RE = re.compile(
    rf'(?P<qualifier>{_IDENTIFIER})\s*\.\s*'
    rf'(?P<column>{_IDENTIFIER})'
)

_RESERVED_ALIAS_WORDS = {
    "where", "join", "left", "right", "inner", "outer",
    "full", "cross", "on", "using", "group", "order",
    "limit", "offset", "having", "union", "except",
    "intersect", "returning", "set", "window", "fetch",
    "for", "as", "when", "then", "else", "end",
}


def _unquote(identifier: str) -> str:
    value = identifier.strip()

    if value.startswith('"') and value.endswith('"'):
        return value[1:-1].replace('""', '"')

    return value


def _normalize_identifier(identifier: str) -> str:
    value = identifier.strip()

    if value.startswith('"') and value.endswith('"'):
        return _unquote(value)

    return value.lower()


def _mask_sql_literals_and_comments(sql: str) -> str:
    """
    Mask SQL string literals and comments while preserving offsets.
    This prevents identifiers inside strings/comments from being
    interpreted as actual SQL identifiers.
    """
    chars = list(sql)
    length = len(sql)
    i = 0

    def mask(start: int, end: int) -> None:
        for pos in range(start, end):
            if chars[pos] not in "\r\n":
                chars[pos] = " "

    while i < length:
        # Single-quoted string literals.
        if sql[i] == "'":
            start = i
            i += 1

            while i < length:
                if sql[i] == "'":
                    if i + 1 < length and sql[i + 1] == "'":
                        i += 2
                        continue

                    i += 1
                    break

                i += 1

            mask(start, i)
            continue

        # PostgreSQL dollar-quoted strings.
        if sql[i] == "$":
            dollar_match = re.match(r"\$[A-Za-z_0-9]*\$", sql[i:])

            if dollar_match:
                delimiter = dollar_match.group(0)
                start = i
                content_start = i + len(delimiter)
                end_pos = sql.find(delimiter, content_start)

                i = (
                    length
                    if end_pos == -1
                    else end_pos + len(delimiter)
                )

                mask(start, i)
                continue

        # Line comments.
        if sql.startswith("--", i):
            start = i
            newline = sql.find("\n", i + 2)
            i = length if newline == -1 else newline
            mask(start, i)
            continue

        # Block comments, including nested block comments.
        if sql.startswith("/*", i):
            start = i
            i += 2
            depth = 1

            while i < length and depth:
                if sql.startswith("/*", i):
                    depth += 1
                    i += 2
                elif sql.startswith("*/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1

            mask(start, i)
            continue

        i += 1

    return "".join(chars)


def _split_qualified_name(value: str) -> Tuple[str, ...]:
    parts = re.split(r"\s*\.\s*", value.strip())
    return tuple(_normalize_identifier(part) for part in parts)


class DefaultSchemaValidator(ISchemaValidator):
    """
    Validate referenced tables and qualified columns against the
    loaded schema.

    This is an identifier validator, not a complete SQL parser.
    SQL safety must also be enforced by the dedicated SQL validator
    and PostgreSQL read-only transaction.
    """

    def __init__(
        self,
        *,
        allow_ctes: bool = True,
        allow_unknown_unqualified_columns: bool = True,
    ) -> None:
        self.allow_ctes = allow_ctes
        self.allow_unknown_unqualified_columns = (
            allow_unknown_unqualified_columns
        )

    def validate_sql_identifiers(
        self,
        sql_query: str,
        schema: DatabaseSchemaEntity,
    ) -> bool:
        if not isinstance(sql_query, str) or not sql_query.strip():
            logger.warning("[Schema Validator] SQL query is empty.")
            return False

        if not isinstance(schema, DatabaseSchemaEntity):
            logger.warning("[Schema Validator] Invalid schema object.")
            return False

        all_tables: Dict[str, TableEntity] = {}

        for collection in (schema.tables or {}, schema.views or {}):
            for key, table in collection.items():
                if not isinstance(table, TableEntity):
                    continue

                all_tables.setdefault(
                    _normalize_identifier(str(key)), table
                )
                all_tables.setdefault(
                    _normalize_identifier(table.name), table
                )

        if not all_tables:
            logger.warning(
                "[Schema Validator] No tables or views are loaded."
            )
            return False

        masked_sql = _mask_sql_literals_and_comments(sql_query)
        stripped = masked_sql.lstrip()

        if not re.match(r"(?is)^(SELECT|WITH)\b", stripped):
            logger.warning(
                "[Schema Validator] Only SELECT/WITH queries "
                "are accepted."
            )
            return False

        cte_names: Set[str] = set()

        if self.allow_ctes:
            cte_header = re.match(
                r"(?is)^\s*WITH\s+(?:RECURSIVE\s+)?"
                r"(?P<body>.*?)(?=\bSELECT\b)",
                masked_sql,
            )

            if cte_header:
                pattern = (
                    rf'(?is)(?:^|,)\s*({_IDENTIFIER})\s*'
                    rf'(?:\([^)]*\))?\s+AS\s*\('
                )

                cte_names.update(
                    _normalize_identifier(match.group(1))
                    for match in re.finditer(
                        pattern, cte_header.group("body")
                    )
                )

        referenced_tables: Dict[str, TableEntity] = {}
        aliases: Dict[str, TableEntity] = {}

        for match in _TABLE_INTRODUCER_RE.finditer(masked_sql):
            raw_name = match.group("name")
            parts = _split_qualified_name(raw_name)
            table_name = parts[-1]

            if table_name in cte_names:
                continue

            table = all_tables.get(table_name)

            if table is None:
                logger.warning(
                    "[Schema Validator] Unknown table/view: %s",
                    raw_name,
                )
                return False

            referenced_tables[table_name] = table

            remainder = masked_sql[match.end():]
            alias_match = _ALIAS_RE.match(remainder)

            if alias_match:
                alias = _normalize_identifier(
                    alias_match.group("alias")
                )

                if alias not in _RESERVED_ALIAS_WORDS:
                    aliases[alias] = table

            aliases.setdefault(table_name, table)

        if not referenced_tables:
            logger.warning(
                "[Schema Validator] No known table reference found."
            )
            return False

        # Validate qualified columns such as s.department.
        for match in _QUALIFIED_COLUMN_RE.finditer(masked_sql):
            qualifier = _normalize_identifier(
                match.group("qualifier")
            )
            column_name = _normalize_identifier(
                match.group("column")
            )

            prefix = masked_sql[
                max(0, match.start() - 20):match.start()
            ].upper()

            # Skip schema.table tokens following FROM/JOIN.
            if re.search(
                r"\b(?:FROM|JOIN|UPDATE|INTO)\s*$", prefix
            ):
                continue

            table = aliases.get(qualifier)

            # Unknown qualifiers may be schema-qualified names or
            # expressions; PostgreSQL validates them during execution.
            if table is None:
                continue

            known_columns = {
                _normalize_identifier(str(key))
                for key in (table.columns or {}).keys()
            }

            known_columns.update(
                _normalize_identifier(column.name)
                for column in (table.columns or {}).values()
                if hasattr(column, "name")
            )

            if column_name not in known_columns:
                logger.warning(
                    "[Schema Validator] Unknown column %s.%s "
                    "in table %s.",
                    qualifier,
                    column_name,
                    table.name,
                )
                return False

        logger.debug(
            "[Schema Validator] Identifier validation passed "
            "for %d table(s).",
            len(referenced_tables),
        )

        return True
