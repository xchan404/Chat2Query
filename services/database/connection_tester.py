"""Connection tester — tests live database connectivity."""

import logging
import time

from services.database.adapters.base import ConnectionParams
from services.database.adapters.registry import get_adapter

logger = logging.getLogger(__name__)


async def test_connection(
    database_type: str,
    params: ConnectionParams,
) -> tuple[bool, str, float | None]:
    """Test a database connection.

    Returns (success, message, latency_ms).
    """
    adapter = get_adapter(database_type)

    start = time.monotonic()
    try:
        success, message = await adapter.test_connection(params)
        elapsed_ms = (time.monotonic() - start) * 1000
        return success, message, elapsed_ms
    except Exception as e:
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.warning(
            "Connection test error",
            extra={"database_type": database_type, "error": str(e)},
        )
        return False, f"Connection test failed: {str(e)}", elapsed_ms
