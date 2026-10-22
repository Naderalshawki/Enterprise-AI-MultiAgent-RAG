from dataclasses import dataclass, field


@dataclass(slots=True)
class ColumnMetadata:
    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False


@dataclass(slots=True)
class TableMetadata:
    name: str
    columns: list[ColumnMetadata] = field(default_factory=list)


@dataclass(slots=True)
class DatabaseMetadata:
    tables: list[TableMetadata] = field(default_factory=list)