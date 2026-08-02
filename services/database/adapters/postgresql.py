"""PostgreSQL adapter implementation."""

import logging
from typing import Any

import asyncpg

from services.database.adapters.base import (
    BaseDatabaseAdapter,
    ColumnInfo,
    ConnectionParams,
    SchemaInfo,
    TableInfo,
)

logger = logging.getLogger(__name__)

# System schemas to exclude from discovery
_PG_SYSTEM_SCHEMAS = {"pg_catalog", "information_schema", "pg_toast"}


class PostgreSQLAdapter(BaseDatabaseAdapter):
    """Adapter for PostgreSQL databases."""

    @property
    def dialect_name(self) -> str:
        return "postgres"

    def _dsn(self, params: ConnectionParams) -> str:
        """Build a PostgreSQL DSN string."""
        return (
            f"postgresql://{params.username}:{params.password}"
            f"@{params.host}:{params.port}/{params.database_name}"
        )

    async def _connect(self, params: ConnectionParams) -> asyncpg.Connection:
        """Create a transient connection (not pooled — adapter-level connections
        are short-lived and used for introspection/testing)."""
        ssl_mode = "require" if params.ssl_enabled else None
        return await asyncpg.connect(
            host=params.host,
            port=params.port,
            user=params.username,
            password=params.password,
            database=params.database_name,
            ssl=ssl_mode,
            timeout=10,
        )

    async def test_connection(self, params: ConnectionParams) -> tuple[bool, str]:
        """Test connectivity to a PostgreSQL database."""
        try:
            conn = await self._connect(params)
            try:
                version = await conn.fetchval("SELECT version()")
                return True, f"Connected successfully. {version}"
            finally:
                await conn.close()
        except Exception as e:
            logger.warning("PostgreSQL connection test failed", extra={"error": str(e)})
            return False, f"Connection failed: {str(e)}"

    async def list_schemas(self, params: ConnectionParams) -> list[SchemaInfo]:
        """List non-system schemas."""
        conn = await self._connect(params)
        try:
            rows = await conn.fetch(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name NOT LIKE 'pg_%' "
                "AND schema_name != 'information_schema' "
                "ORDER BY schema_name"
            )
            return [SchemaInfo(schema_name=row["schema_name"]) for row in rows]
        finally:
            await conn.close()

    async def list_tables(
        self, params: ConnectionParams, schema_name: str
    ) -> list[TableInfo]:
        """List tables and views in a schema."""
        conn = await self._connect(params)
        try:
            rows = await conn.fetch(
                "SELECT table_name, table_type "
                "FROM information_schema.tables "
                "WHERE table_schema = $1 "
                "ORDER BY table_name",
                schema_name,
            )
            tables = []
            for row in rows:
                table_type = "VIEW" if row["table_type"] == "VIEW" else "TABLE"
                tables.append(
                    TableInfo(
                        schema_name=schema_name,
                        table_name=row["table_name"],
                        table_type=table_type,
                    )
                )
            return tables
        finally:
            await conn.close()

    async def list_columns(
        self, params: ConnectionParams, schema_name: str, table_name: str
    ) -> list[ColumnInfo]:
        """List columns for a table."""
        conn = await self._connect(params)
        try:
            # Get column info
            col_rows = await conn.fetch(
                "SELECT column_name, data_type, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_schema = $1 AND table_name = $2 "
                "ORDER BY ordinal_position",
                schema_name,
                table_name,
            )
            # Get primary key columns
            pk_rows = await conn.fetch(
                "SELECT a.attname "
                "FROM pg_index i "
                "JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) "
                "JOIN pg_class c ON c.oid = i.indrelid "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE i.indisprimary AND n.nspname = $1 AND c.relname = $2",
                schema_name,
                table_name,
            )
            pk_columns = {row["attname"] for row in pk_rows}

            # Get foreign key columns
            fk_rows = await conn.fetch(
                "SELECT kcu.column_name "
                "FROM information_schema.key_column_usage kcu "
                "JOIN information_schema.table_constraints tc "
                "  ON tc.constraint_name = kcu.constraint_name "
                "  AND tc.table_schema = kcu.table_schema "
                "WHERE tc.constraint_type = 'FOREIGN KEY' "
                "AND kcu.table_schema = $1 AND kcu.table_name = $2",
                schema_name,
                table_name,
            )
            fk_columns = {row["column_name"] for row in fk_rows}

            columns = []
            for row in col_rows:
                columns.append(
                    ColumnInfo(
                        schema_name=schema_name,
                        table_name=table_name,
                        column_name=row["column_name"],
                        data_type=row["data_type"],
                        is_nullable=row["is_nullable"] == "YES",
                        is_primary_key=row["column_name"] in pk_columns,
                        is_foreign_key=row["column_name"] in fk_columns,
                    )
                )
            return columns
        finally:
            await conn.close()

    async def execute_readonly(
        self,
        params: ConnectionParams,
        sql: str,
        timeout_ms: int = 5000,
    ) -> tuple[list[dict[str, Any]], int]:
        """Execute a read-only SQL query with timeout."""
        conn = await self._connect(params)
        try:
            # Set read-only transaction and statement timeout
            await conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
            await conn.execute(f"SET statement_timeout = {timeout_ms}")

            rows = await conn.fetch(sql)
            result = [dict(row) for row in rows]
            return result, len(result)
        finally:
            await conn.close()
