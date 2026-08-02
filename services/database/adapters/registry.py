"""Adapter registry — maps database_type strings to adapter instances.

To add a new database type:
1. Create a new adapter in services/database/adapters/ implementing BaseDatabaseAdapter
2. Register it here by adding one line to _ADAPTERS
No other file changes needed.
"""

from services.database.adapters.base import BaseDatabaseAdapter
from services.database.adapters.postgresql import PostgreSQLAdapter
from services.database.adapters.mysql import MySQLAdapter

# Registry: database_type string -> adapter instance
_ADAPTERS: dict[str, BaseDatabaseAdapter] = {
    "postgresql": PostgreSQLAdapter(),
    "mysql": MySQLAdapter(),
}


def get_adapter(database_type: str) -> BaseDatabaseAdapter:
    """Return the adapter for the given database type.

    Raises ValueError if the type is not registered.
    """
    adapter = _ADAPTERS.get(database_type)
    if adapter is None:
        supported = ", ".join(sorted(_ADAPTERS.keys()))
        raise ValueError(
            f"Unsupported database type: '{database_type}'. "
            f"Supported types: {supported}"
        )
    return adapter


def get_supported_types() -> list[str]:
    """Return a sorted list of supported database types."""
    return sorted(_ADAPTERS.keys())
