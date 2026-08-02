"""Shared constants and enumerations."""

import enum


class ProcessingStatus(str, enum.Enum):
    """File processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DatabaseType(str, enum.Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class MessageRole(str, enum.Enum):
    """Chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class IntentType(str, enum.Enum):
    """Chat intent classification."""
    GENERAL = "general"
    DATABASE = "database"
    DOCUMENT = "document"
    HYBRID = "hybrid"
    CLARIFICATION = "clarification"


class PermissionType(str, enum.Enum):
    """Permission access levels."""
    READ = "read"
    WRITE = "write"
    NONE = "none"


class AuditAction(str, enum.Enum):
    """Audit log action types."""
    LOGIN = "login"
    LOGOUT = "logout"
    CONNECTION_CREATE = "connection_create"
    CONNECTION_TEST = "connection_test"
    CONNECTION_DELETE = "connection_delete"
    SCHEMA_SYNC = "schema_sync"
    PERMISSION_CHANGE = "permission_change"
    FILE_UPLOAD = "file_upload"
    FILE_DELETE = "file_delete"
    CHAT_REQUEST = "chat_request"
    QUERY_EXECUTION = "query_execution"
