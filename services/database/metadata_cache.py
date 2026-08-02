"""In-memory metadata cache for discovered database schemas."""

import time
import uuid
from typing import Any

from schemas.schema_metadata import SchemaOut


class MetadataCache:
    """In-memory cache for schema metadata with TTL."""

    def __init__(self, ttl: int = 300):
        self._cache: dict[str, tuple[list[SchemaOut], float]] = {}
        self._ttl = ttl

    def get(self, connection_id: uuid.UUID) -> list[SchemaOut] | None:
        """Get cached schemas for a connection."""
        key = str(connection_id)
        entry = self._cache.get(key)
        if entry is None:
            return None
        schemas, timestamp = entry
        if time.monotonic() - timestamp > self._ttl:
            del self._cache[key]
            return None
        return schemas

    def put(self, connection_id: uuid.UUID, schemas: list[SchemaOut]) -> None:
        """Put schemas into cache."""
        self._cache[str(connection_id)] = (schemas, time.monotonic())

    def invalidate(self, connection_id: uuid.UUID) -> None:
        """Invalidate cache for a connection."""
        self._cache.pop(str(connection_id), None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


metadata_cache = MetadataCache()
