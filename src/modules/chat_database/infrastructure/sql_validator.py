from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from src.modules.chat_database.domain.entities import SQLQuery
from src.modules.chat_database.domain.exceptions import (
    SQLValidationError,
    UnsafeSQLQueryError,
    UnsupportedSQLDialectError,
)
from src.modules.chat_database.domain.value_objects import SQLDialect

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _ScanResult:
    masked: str
    has_comment: bool
    semicolons: tuple[int, ...]


class DefaultSQLValidator:
    """
    Conservative lexical validation for read-only PostgreSQL queries.
    """

    BLOCKED_KEYWORDS = frozenset({
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
        "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL",
        "MERGE", "COPY", "VACUUM", "ANALYZE", "REFRESH", "REINDEX",
        "CLUSTER", "DO", "PREPARE", "DEALLOCATE", "DISCARD", "LOCK",
        "SET", "RESET", "COMMENT", "LISTEN", "UNLISTEN", "NOTIFY",
        "LOAD", "DECLARE", "FETCH", "MOVE", "CLOSE",
    })

    BLOCKED_FUNCTIONS = frozenset({
        "PG_TERMINATE_BACKEND",
        "PG_CANCEL_BACKEND",
        "PG_RELOAD_CONF",
        "PG_ROTATE_LOGFILE",
        "PG_PROMOTE",
        "PG_SWITCH_WAL",
        "PG_CREATE_RESTORE_POINT",
        "PG_LOGICAL_EMIT_MESSAGE",
        "LO_IMPORT",
        "LO_EXPORT",
        "DBLINK_EXEC",
        "DBLINK_EXECUTE",
    })

    def __init__(self, *, allow_comments: bool = False) -> None:
        self.allow_comments = allow_comments

    async def validate(self, query: SQLQuery) -> SQLQuery:
        """Validate the SQLQuery and return the same object if accepted."""

        if not hasattr(query, "query") or getattr(query, "query") is None:
            raise SQLValidationError("Expected an SQLQuery object containing a query string.")

        sql = query.query

        if not isinstance(sql, str) or not sql.strip():
            raise SQLValidationError("Generated SQL is empty.")

        # =====================================================================
        # خوارزمية التنظيف الذكية (النسخة النهائية الصارمة)
        # =====================================================================
        match = re.search(r"```(?:sql|postgresql|)\s*(.*?)\s*```", sql, re.IGNORECASE | re.DOTALL)
        if match:
            sql = match.group(1).strip()
        else:
            # قص أي كلام يسبق SELECT أو WITH
            match_start = re.search(r"(?i)\b(SELECT|WITH)\b", sql)
            if match_start:
                sql = sql[match_start.start():]
            
            # قص أي ثرثرة تأتي بعد الفاصلة المنقوطة
            semicolon_idx = sql.find(';')
            if semicolon_idx != -1:
                sql = sql[:semicolon_idx + 1]
                
        sql = sql.strip()
        
        try:
            query.query = sql
        except Exception:
            # في حال كان الكائن frozen
            object.__setattr__(query, "query", sql)
        # =====================================================================

        if not self._is_postgresql(getattr(query, "dialect", SQLDialect.POSTGRESQL)):
            raise UnsupportedSQLDialectError(
                "Only PostgreSQL SQL dialect is supported."
            )

        scan = self._scan(sql)
        masked = scan.masked.strip()

        if not masked:
            raise SQLValidationError(
                "SQL contains no executable statement."
            )

        if scan.has_comment and not self.allow_comments:
            raise UnsafeSQLQueryError(
                "SQL comments are not allowed."
            )

        if scan.semicolons:
            if len(scan.semicolons) != 1:
                raise UnsafeSQLQueryError(
                    "Multiple SQL statements are not allowed."
                )

            final_position = len(scan.masked.rstrip()) - 1
            if scan.semicolons[0] != final_position:
                raise UnsafeSQLQueryError(
                    "A semicolon is allowed only at the end of the query."
                )

        if not re.match(r"(?is)^(SELECT|WITH)\b", masked):
            raise UnsafeSQLQueryError(
                "Only SELECT and WITH queries are allowed."
            )

        tokens = {
            match.group(0).upper()
            for match in re.finditer(
                r"\b[A-Za-z_][A-Za-z_0-9$]*\b", masked
            )
        }

        blocked = sorted(tokens & self.BLOCKED_KEYWORDS)
        if blocked:
            raise UnsafeSQLQueryError(
                "Forbidden SQL keyword: " + ", ".join(blocked)
            )

        if re.search(r"\bSELECT\b[\s\S]*?\bINTO\b", masked, re.I):
            raise UnsafeSQLQueryError(
                "SELECT INTO is not allowed."
            )

        if re.search(
            r"\bFOR\s+(?:NO\s+KEY\s+UPDATE|KEY\s+SHARE|UPDATE|SHARE)\b",
            masked,
            re.I,
        ):
            raise UnsafeSQLQueryError(
                "Row-locking SELECT clauses are not allowed."
            )

        blocked_calls = sorted(
            name
            for name in self.BLOCKED_FUNCTIONS
            if re.search(
                rf"\b{re.escape(name)}\s*\(", masked, re.I
            )
        )

        if blocked_calls:
            raise UnsafeSQLQueryError(
                "Potentially unsafe database function: "
                + ", ".join(blocked_calls)
            )

        logger.debug(
            "[SQL Validator] Accepted query (%d characters).",
            len(sql),
        )
        return query

    @staticmethod
    def _is_postgresql(dialect: object) -> bool:
        if dialect == SQLDialect.POSTGRESQL:
            return True

        value = getattr(dialect, "value", dialect)
        return (
            isinstance(value, str)
            and value.strip().lower()
            in {"postgresql", "postgres", "postgre_sql"}
        )

    @staticmethod
    def _scan(sql: str) -> _ScanResult:
        chars = list(sql)
        length = len(sql)
        i = 0
        has_comment = False
        semicolons: list[int] = []

        def mask(start: int, end: int) -> None:
            for position in range(start, end):
                if chars[position] not in "\r\n":
                    chars[position] = " "

        while i < length:
            char = sql[i]

            if char == "'":
                start = i
                i += 1
                while i < length:
                    if sql[i] == "'":
                        if i + 1 < length and sql[i + 1] == "'":
                            i += 2
                            continue
                        i += 1
                        break
                    if sql[i] == "\\" and i + 1 < length:
                        i += 2
                    else:
                        i += 1
                else:
                    raise SQLValidationError("Unterminated SQL string literal.")
                mask(start, i)
                continue

            if char == '"':
                start = i
                i += 1
                while i < length:
                    if sql[i] == '"':
                        if i + 1 < length and sql[i + 1] == '"':
                            i += 2
                            continue
                        i += 1
                        break
                    i += 1
                else:
                    raise SQLValidationError("Unterminated quoted SQL identifier.")
                mask(start, i)
                continue

            if char == "$":
                match = re.match(r"\$[A-Za-z_0-9]*\$", sql[i:])
                if match:
                    delimiter = match.group(0)
                    start = i
                    content_start = i + len(delimiter)
                    end = sql.find(delimiter, content_start)

                    if end < 0:
                        raise SQLValidationError("Unterminated dollar-quoted string.")

                    i = end + len(delimiter)
                    mask(start, i)
                    continue

            if sql.startswith("--", i):
                has_comment = True
                start = i
                newline = sql.find("\n", i + 2)
                i = length if newline < 0 else newline
                mask(start, i)
                continue

            if sql.startswith("/*", i):
                has_comment = True
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

                if depth:
                    raise SQLValidationError("Unterminated SQL block comment.")

                mask(start, i)
                continue

            if char == ";":
                semicolons.append(i)

            i += 1

        return _ScanResult(
            masked="".join(chars),
            has_comment=has_comment,
            semicolons=tuple(semicolons),
        )