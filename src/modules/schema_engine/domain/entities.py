
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ColumnEntity:
    """Metadata for a single database column."""

    name: str
    data_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: Optional[str] = None
    description: Optional[str] = None
    default_value: Optional[str] = None
    max_length: Optional[int] = None

    # Representative values retrieved from the actual database.
    # These values help the LLM generate accurate SQL filters.
    sample_values: List[str] = field(default_factory=list)


@dataclass
class TableEntity:
    """Metadata for a PostgreSQL table or view."""

    name: str
    columns: Dict[str, ColumnEntity] = field(default_factory=dict)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, Any]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    row_count_estimate: Optional[int] = None
    description: Optional[str] = None


@dataclass
class DatabaseSchemaEntity:
    """Complete schema metadata used by the Schema Engine."""

    tables: Dict[str, TableEntity] = field(default_factory=dict)
    views: Dict[str, TableEntity] = field(default_factory=dict)
    relations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
