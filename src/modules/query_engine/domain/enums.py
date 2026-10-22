from enum import Enum


class QueryStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueryIntent(str, Enum):
    DATA = "data"
    DOCUMENT = "document"  # تمت الإضافة لدعم أسئلة المستندات (RAG)
    SCHEMA = "schema"
    DATABASE_INFO = "database_info"
    UNKNOWN = "unknown"


class QueryExecutionMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"


class QuerySource(str, Enum):
    CHAT_DATABASE = "chat_database"
    MULTI_AGENT = "multi_agent"  # تمت الإضافة لتوجيه أسئلة المستندات لوكيل التخطيط
    UNKNOWN = "unknown"


class QueryPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"