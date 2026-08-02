"""Abstract base adapter for database connections.

To add a new database type:
1. Create a new adapter file (e.g., adapters/mssql.py)
2. Implement all abstract methods
3. Register it in adapters/registry.py

No other file changes required.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Sequence


@dataclass
class ConnectionParams:
    """Parameters needed to connect to a database."""
    host: str
    port: int
    database_name: str
    username: str
    password: str  # Decrypted, in-memory only
    ssl_enabled: bool = False


@dataclass
class SchemaInfo:
    """Metadata for a database schema."""
    schema_name: str


@dataclass
class TableInfo:
    """Metadata for a database table."""
    schema_name: str
    table_name: str
    table_type: str = "TABLE"  # TABLE or VIEW
    row_count: int | None = None


@dataclass
class ColumnInfo:
    """Metadata for a database column."""
    schema_name: str
    table_name: str
    column_name: str
    data_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False


class BaseDatabaseAdapter(ABC):
    """Abstract adapter interface for database backends.

    Implementations must provide:
    - test_connection: verify connectivity
    - list_schemas: enumerate schemas
    - list_tables: enumerate tables in a schema
    - list_columns: enumerate columns in a table
    - execute_readonly: run a read-only query
    - dialect_name: SQLGlot dialect identifier
    """

    @property
    @abstractmethod
    def dialect_name(self) -> str:
        """Return the SQLGlot dialect name for this database type."""
        ...

    @abstractmethod
    async def test_connection(self, params: ConnectionParams) -> tuple[bool, str]:
        """Test connectivity to the database.

        Returns (success: bool, message: str).
        """
        ...

    @abstractmethod
    async def list_schemas(self, params: ConnectionParams) -> list[SchemaInfo]:
        """List all user-accessible schemas in the database."""
        ...

    @abstractmethod
    async def list_tables(
        self, params: ConnectionParams, schema_name: str
    ) -> list[TableInfo]:
        """List all tables/views in a specific schema."""
        ...

    @abstractmethod
    async def list_columns(
        self, params: ConnectionParams, schema_name: str, table_name: str
    ) -> list[ColumnInfo]:
        """List all columns in a specific table."""
        ...

    @abstractmethod
    async def execute_readonly(
        self,
        params: ConnectionParams,
        sql: str,
        timeout_ms: int = 5000,
    ) -> tuple[list[dict[str, Any]], int]:
        """Execute a read-only SQL query.

        Returns (rows as list of dicts, total row count).
        The implementation must enforce read-only semantics.
        """
        ...
