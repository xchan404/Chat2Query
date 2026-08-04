"""Single generic database agent node — Section 6 compliance.

Takes request-scoped allowed_schema, generates SQL, validates via SQL Safety Pipeline,
and executes via read-only connection adapter.
"""

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agents.state import AgentState
from core.permissions import resolve_allowed_schema
from services.database.connection_service import ConnectionService
from services.database.query_executor import QueryExecutor
from services.llm.client import llm_client, LLMError

logger = logging.getLogger(__name__)


async def database_node(state: AgentState, session: AsyncSession) -> dict[str, Any]:
    """LangGraph node: execute single generic Text-to-SQL pipeline."""
    question = state["question"]
    tenant_id = uuid.UUID(state["tenant_id"])
    user_id = uuid.UUID(state["user_id"])
    conn_id_str = state.get("connection_id")

    if not conn_id_str:
        # Check if tenant has default connection
        conn_service = ConnectionService(session)
        conns = await conn_service.list_connections(tenant_id=tenant_id, limit=1)
        if not conns:
            return {
                "sql_result": {
                    "success": False,
                    "status": "error",
                    "errors": ["No active database connection selected or configured."],
                    "generated_sql": None,
                    "normalized_sql": None,
                    "rows": [],
                    "row_count": 0,
                    "execution_time_ms": 0.0,
                }
            }
        connection_id = conns[0].id
    else:
        connection_id = uuid.UUID(conn_id_str)

    # Step 1: Resolve permitted schema
    allowed_schema = await resolve_allowed_schema(
        db=session,
        tenant_id=tenant_id,
        user_id=user_id,
        connection_id=connection_id,
    )

    conn_service = ConnectionService(session)
    conn = await conn_service.get_connection(tenant_id, connection_id)

    # Step 2: Generate SQL via LLM (with error handling)
    try:
        generated_sql = await llm_client.generate_sql(
            question=question,
            allowed_schema=allowed_schema,
            database_type=conn.database_type,
        )
    except LLMError as e:
        logger.error(f"Database Node LLM Error: {e}")
        return {
            "allowed_schema": allowed_schema,
            "sql_result": {
                "success": False,
                "status": "error",
                "errors": [str(e)],
                "generated_sql": None,
                "normalized_sql": None,
                "rows": [],
                "row_count": 0,
                "execution_time_ms": 0.0,
            }
        }
    except Exception as e:
        logger.error(f"Database Node Unexpected Error: {e}")
        return {
            "allowed_schema": allowed_schema,
            "sql_result": {
                "success": False,
                "status": "error",
                "errors": [f"An unexpected error occurred during SQL generation: {str(e)}"],
                "generated_sql": None,
                "normalized_sql": None,
                "rows": [],
                "row_count": 0,
                "execution_time_ms": 0.0,
            }
        }

    # Step 3: Validate and execute
    executor = QueryExecutor(session)
    sql_result = await executor.execute_query(
        tenant_id=tenant_id,
        user_id=user_id,
        connection_id=connection_id,
        generated_sql=generated_sql,
        allowed_schema=allowed_schema,
    )

    return {
        "allowed_schema": allowed_schema,
        "sql_result": sql_result,
    }
