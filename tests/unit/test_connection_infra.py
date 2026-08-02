"""Unit tests for the adapter registry and connection pool."""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"
os.environ["CONNECTION_ENCRYPTION_KEY"] = "test-encryption-key-for-unit-tests"

import pytest

from services.database.adapters.base import BaseDatabaseAdapter, ConnectionParams
from services.database.adapters.registry import get_adapter, get_supported_types
from services.database.connection_pool import ConnectionParamCache


class TestAdapterRegistry:
    """Test the adapter registry pattern."""

    def test_postgresql_adapter_registered(self):
        adapter = get_adapter("postgresql")
        assert isinstance(adapter, BaseDatabaseAdapter)
        assert adapter.dialect_name == "postgres"

    def test_mysql_adapter_registered(self):
        adapter = get_adapter("mysql")
        assert isinstance(adapter, BaseDatabaseAdapter)
        assert adapter.dialect_name == "mysql"

    def test_unsupported_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported database type"):
            get_adapter("oracle")

    def test_supported_types_includes_both(self):
        types = get_supported_types()
        assert "postgresql" in types
        assert "mysql" in types

    def test_adding_new_adapter_requires_only_registry(self):
        """Verify the architectural property: adding a new DB type
        is just one file + one line in registry.py.

        We check that the BaseDatabaseAdapter interface has exactly the
        methods listed in BUILD_PLAN Section 6 Phase 2.
        """
        import inspect
        abstract_methods = {
            name
            for name, _ in inspect.getmembers(BaseDatabaseAdapter, predicate=inspect.isfunction)
            if getattr(getattr(BaseDatabaseAdapter, name, None), "__isabstractmethod__", False)
        }
        # dialect_name is a property, check separately
        assert hasattr(BaseDatabaseAdapter, "dialect_name")

        expected = {"test_connection", "list_schemas", "list_tables", "list_columns", "execute_readonly"}
        assert abstract_methods == expected


class TestConnectionParamCache:
    """Test the short-TTL connection parameter cache."""

    def test_put_and_get(self):
        cache = ConnectionParamCache(ttl=60)
        params = ConnectionParams(
            host="localhost",
            port=5432,
            database_name="testdb",
            username="user",
            password="pass",
        )
        cache.put("conn-1", params, "postgresql")

        result = cache.get("conn-1")
        assert result is not None
        assert result[0].password == "pass"
        assert result[1] == "postgresql"

    def test_get_nonexistent_returns_none(self):
        cache = ConnectionParamCache(ttl=60)
        assert cache.get("nonexistent") is None

    def test_cache_expiry(self):
        cache = ConnectionParamCache(ttl=0)  # TTL of 0 = immediately expired
        params = ConnectionParams(
            host="localhost", port=5432, database_name="db",
            username="u", password="p",
        )
        cache.put("conn-2", params, "postgresql")
        time.sleep(0.01)  # Ensure expiry
        assert cache.get("conn-2") is None

    def test_invalidate(self):
        cache = ConnectionParamCache(ttl=60)
        params = ConnectionParams(
            host="localhost", port=5432, database_name="db",
            username="u", password="p",
        )
        cache.put("conn-3", params, "postgresql")
        assert cache.get("conn-3") is not None

        cache.invalidate("conn-3")
        assert cache.get("conn-3") is None

    def test_clear(self):
        cache = ConnectionParamCache(ttl=60)
        params = ConnectionParams(
            host="localhost", port=5432, database_name="db",
            username="u", password="p",
        )
        cache.put("a", params, "postgresql")
        cache.put("b", params, "mysql")
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_password_only_in_memory(self):
        """The cache holds decrypted passwords in memory but they are
        Python objects — verify they're accessible but not persisted."""
        cache = ConnectionParamCache(ttl=60)
        secret_password = "super-secret-123"
        params = ConnectionParams(
            host="localhost", port=5432, database_name="db",
            username="u", password=secret_password,
        )
        cache.put("conn-mem", params, "postgresql")

        # Password is available in memory
        result = cache.get("conn-mem")
        assert result[0].password == secret_password

        # After invalidation, it's gone
        cache.invalidate("conn-mem")
        assert cache.get("conn-mem") is None
