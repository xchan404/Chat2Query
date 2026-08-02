"""Text-to-SQL pipeline orchestrator for single-source queries."""

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from core.permissions import resolve_allowed_schema
from services.database.connection_service import ConnectionService
from services.database.query_executor import QueryExecutor
from services.llm.client import llm_client

logger = logging.getLogger(__name__)


class Text2SQLService:
    """End-to-end single-source Text-to-SQL pipeline."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.connection_service = ConnectionService(session)
        self.executor = QueryExecutor(session)

    async def query(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        connection_id: uuid.UUID,
        question: str,
    ) -> dict[str, Any]:
        """Process NL question: fetch schema -> generate SQL -> validate -> execute -> log."""
        connection = await self.connection_service.get_connection(tenant_id, connection_id)

        # Step 1: Resolve permitted schema
        allowed_schema = await resolve_allowed_schema(
            db=self.session,
            tenant_id=tenant_id,
            user_id=user_id,
            connection_id=connection_id,
        )

        # Step 2: Generate SQL via LLM
        generated_sql = await llm_client.generate_sql(
            question=question,
            allowed_schema=allowed_schema,
            database_type=connection.database_type,
        )

        # Step 3: Validate and execute
        result = await self.executor.execute_query(
            tenant_id=tenant_id,
            user_id=user_id,
            connection_id=connection_id,
            generated_sql=generated_sql,
            allowed_schema=allowed_schema,
        )

        return {
            "question": question,
            "connection_id": str(connection_id),
            "generated_sql": generated_sql,
            "result": result,
        }
