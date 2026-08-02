"""Query Executor — executes validated SQL and logs execution records."""

import logging
import time
import uuid
from typing import Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from models.query_execution import QueryExecution
from repositories.base import BaseRepository
from services.database.adapters.registry import get_adapter
from services.database.connection_service import ConnectionService
from services.database.dialect_resolver import resolve_sqlglot_dialect
from services.database.query_validator import validate_and_transform_sql

logger = logging.getLogger(__name__)


def mask_value(val: Any) -> str:
    """Mask a sensitive column value (BUILD_PLAN Section 8)."""
    if val is None:
        return None
    s = str(val)
    if len(s) <= 4:
        return "****"
    return s[:2] + "*" * (len(s) - 4) + s[-2:]


class QueryExecutor:
    """Service to validate, execute, and record SQL query attempts."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.connection_service = ConnectionService(session)

    async def execute_query(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        connection_id: uuid.UUID,
        generated_sql: str,
        allowed_schema: dict[str, Any],
        message_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Validate and execute SQL query against target database connection.

        Writes a `query_executions` audit row regardless of outcome.
        """
        settings = get_settings()
        connection = await self.connection_service.get_connection(tenant_id, connection_id)
        dialect = resolve_sqlglot_dialect(connection.database_type)

        # Step 1: Run SQL Safety Pipeline
        val_result = validate_and_transform_sql(
            raw_sql=generated_sql,
            dialect=dialect,
            allowed_schema=allowed_schema,
            max_rows=settings.SQL_MAX_ROWS,
        )

        execution_record = QueryExecution(
            tenant_id=tenant_id,
            connection_id=connection_id,
            user_id=user_id,
            message_id=message_id,
            generated_sql=generated_sql,
            normalized_sql=val_result.normalized_sql,
            validation_status=val_result.status,
            validation_errors=val_result.errors if val_result.errors else None,
            applied_row_filters=val_result.applied_row_filters if val_result.applied_row_filters else None,
            referenced_tables=val_result.referenced_tables if val_result.referenced_tables else None,
            referenced_columns=val_result.referenced_columns if val_result.referenced_columns else None,
        )

        if not val_result.is_valid:
            self.session.add(execution_record)
            await self.session.flush()
            await self.session.commit()
            return {
                "execution_id": str(execution_record.id),
                "success": False,
                "status": "rejected",
                "errors": val_result.errors,
                "generated_sql": generated_sql,
                "normalized_sql": None,
                "rows": [],
                "row_count": 0,
                "execution_time_ms": 0.0,
            }

        # Step 2: Execute normalized SQL via adapter
        params = self.connection_service.get_decrypted_params(connection)
        adapter = get_adapter(connection.database_type)

        start_time = time.monotonic()
        try:
            rows, count = await adapter.execute_readonly(
                params=params,
                sql=val_result.normalized_sql,
                timeout_ms=settings.SQL_STATEMENT_TIMEOUT_MS,
            )
            elapsed_ms = (time.monotonic() - start_time) * 1000

            execution_record.row_count = count
            execution_record.execution_time_ms = elapsed_ms
            execution_record.executed_at = datetime.now(timezone.utc)

            self.session.add(execution_record)
            await self.session.flush()
            await self.session.commit()

            return {
                "execution_id": str(execution_record.id),
                "success": True,
                "status": "approved",
                "errors": [],
                "generated_sql": generated_sql,
                "normalized_sql": val_result.normalized_sql,
                "rows": rows,
                "row_count": count,
                "execution_time_ms": round(elapsed_ms, 2),
            }

        except Exception as e:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            err_msg = str(e)
            logger.error(f"SQL execution error: {err_msg}")

            execution_record.validation_status = "error"
            execution_record.error_message = err_msg
            execution_record.execution_time_ms = elapsed_ms

            self.session.add(execution_record)
            await self.session.flush()
            await self.session.commit()

            return {
                "execution_id": str(execution_record.id),
                "success": False,
                "status": "error",
                "errors": [err_msg],
                "generated_sql": generated_sql,
                "normalized_sql": val_result.normalized_sql,
                "rows": [],
                "row_count": 0,
                "execution_time_ms": round(elapsed_ms, 2),
            }
