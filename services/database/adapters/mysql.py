"""MySQL adapter implementation.

Uses aiomysql for async connectivity.
Falls back gracefully if aiomysql is not installed.
"""

import logging
from typing import Any

from services.database.adapters.base import (
    BaseDatabaseAdapter,
    ColumnInfo,
    ConnectionParams,
    SchemaInfo,
    TableInfo,
)

logger = logging.getLogger(__name__)

# System schemas to exclude from discovery
_MYSQL_SYSTEM_SCHEMAS = {
    "information_schema",
    "mysql",
    "performance_schema",
    "sys",
}


class MySQLAdapter(BaseDatabaseAdapter):
    """Adapter for MySQL databases."""

    @property
    def dialect_name(self) -> str:
        return "mysql"

    async def _connect(self, params: ConnectionParams):
        """Create a transient MySQL connection."""
        try:
            import aiomysql
        except ImportError:
            raise RuntimeError(
                "aiomysql is required for MySQL connections. "
                "Install it with: pip install aiomysql"
            )

        ssl_ctx = None
        if params.ssl_enabled:
            import ssl
            ssl_ctx = ssl.create_default_context()

        conn = await aiomysql.connect(
            host=params.host,
            port=params.port,
            user=params.username,
            password=params.password,
            db=params.database_name,
            ssl=ssl_ctx,
            connect_timeout=10,
        )
        return conn

    async def test_connection(self, params: ConnectionParams) -> tuple[bool, str]:
        """Test connectivity to a MySQL database."""
        try:
            conn = await self._connect(params)
            try:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT VERSION()")
                    row = await cur.fetchone()
                    version = row[0] if row else "unknown"
                    return True, f"Connected successfully. MySQL {version}"
            finally:
                conn.close()
        except Exception as e:
            logger.warning("MySQL connection test failed", extra={"error": str(e)})
            return False, f"Connection failed: {str(e)}"

    async def list_schemas(self, params: ConnectionParams) -> list[SchemaInfo]:
        """List non-system schemas (databases in MySQL)."""
        conn = await self._connect(params)
        try:
            async with conn.cursor() as cur:
                await cur.execute("SHOW DATABASES")
                rows = await cur.fetchall()
                return [
                    SchemaInfo(schema_name=row[0])
                    for row in rows
                    if row[0] not in _MYSQL_SYSTEM_SCHEMAS
                ]
        finally:
            conn.close()

    async def list_tables(
        self, params: ConnectionParams, schema_name: str
    ) -> list[TableInfo]:
        """List tables and views in a schema (database)."""
        conn = await self._connect(params)
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT TABLE_NAME, TABLE_TYPE "
                    "FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA = %s "
                    "ORDER BY TABLE_NAME",
                    (schema_name,),
                )
                rows = await cur.fetchall()
                return [
                    TableInfo(
                        schema_name=schema_name,
                        table_name=row[0],
                        table_type="VIEW" if row[1] == "VIEW" else "TABLE",
                    )
                    for row in rows
                ]
        finally:
            conn.close()

    async def list_columns(
        self, params: ConnectionParams, schema_name: str, table_name: str
    ) -> list[ColumnInfo]:
        """List columns for a table."""
        conn = await self._connect(params)
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY "
                    "FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
                    "ORDER BY ORDINAL_POSITION",
                    (schema_name, table_name),
                )
                rows = await cur.fetchall()

                # Get FK columns
                await cur.execute(
                    "SELECT COLUMN_NAME "
                    "FROM information_schema.KEY_COLUMN_USAGE "
                    "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
                    "AND REFERENCED_TABLE_NAME IS NOT NULL",
                    (schema_name, table_name),
                )
                fk_rows = await cur.fetchall()
                fk_columns = {row[0] for row in fk_rows}

                return [
                    ColumnInfo(
                        schema_name=schema_name,
                        table_name=table_name,
                        column_name=row[0],
                        data_type=row[1],
                        is_nullable=row[2] == "YES",
                        is_primary_key=row[3] == "PRI",
                        is_foreign_key=row[0] in fk_columns,
                    )
                    for row in rows
                ]
        finally:
            conn.close()

    async def execute_readonly(
        self,
        params: ConnectionParams,
        sql: str,
        timeout_ms: int = 5000,
    ) -> tuple[list[dict[str, Any]], int]:
        """Execute a read-only SQL query with timeout."""
        conn = await self._connect(params)
        try:
            async with conn.cursor() as cur:
                # Set read-only mode and timeout
                timeout_sec = max(1, timeout_ms // 1000)
                await cur.execute("SET SESSION TRANSACTION READ ONLY")
                await cur.execute(f"SET SESSION max_execution_time = {timeout_ms}")

                await cur.execute(sql)
                raw_rows = await cur.fetchall()

                # Get column names from cursor description
                columns = [desc[0] for desc in cur.description] if cur.description else []
                result = [dict(zip(columns, row)) for row in raw_rows]
                return result, len(result)
        finally:
            conn.close()
