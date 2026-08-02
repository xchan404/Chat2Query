"""Short-TTL connection parameter cache.

Caches decrypted ConnectionParams keyed by connection_id.
Entries expire after TTL_SECONDS — credentials are decrypted
only when needed and evicted automatically.

This is NOT a connection pool in the asyncpg/DBAPI sense —
it's a parameter cache to avoid repeated decryption + DB lookups.
The adapters create transient connections per operation.
"""

import logging
import time
from dataclasses import dataclass

from services.database.adapters.base import ConnectionParams

logger = logging.getLogger(__name__)

TTL_SECONDS = 300  # 5 minutes


@dataclass
class _CacheEntry:
    params: ConnectionParams
    adapter_type: str
    created_at: float


class ConnectionParamCache:
    """In-memory cache for decrypted connection parameters."""

    def __init__(self, ttl: int = TTL_SECONDS):
        self._cache: dict[str, _CacheEntry] = {}
        self._ttl = ttl

    def get(self, connection_id: str) -> tuple[ConnectionParams, str] | None:
        """Return cached (params, adapter_type) or None if not cached / expired."""
        entry = self._cache.get(connection_id)
        if entry is None:
            return None

        if time.monotonic() - entry.created_at > self._ttl:
            # Expired — remove and return None
            del self._cache[connection_id]
            logger.debug("Cache entry expired", extra={"connection_id": connection_id})
            return None

        return entry.params, entry.adapter_type

    def put(
        self, connection_id: str, params: ConnectionParams, adapter_type: str
    ) -> None:
        """Cache decrypted connection parameters."""
        self._cache[connection_id] = _CacheEntry(
            params=params,
            adapter_type=adapter_type,
            created_at=time.monotonic(),
        )

    def invalidate(self, connection_id: str) -> None:
        """Remove a specific entry from the cache."""
        self._cache.pop(connection_id, None)

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()

    def _evict_expired(self) -> None:
        """Remove all expired entries."""
        now = time.monotonic()
        expired = [
            k for k, v in self._cache.items()
            if now - v.created_at > self._ttl
        ]
        for k in expired:
            del self._cache[k]


# Module-level singleton
connection_cache = ConnectionParamCache()
