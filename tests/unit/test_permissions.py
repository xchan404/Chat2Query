"""Unit tests for core/permissions.py permission resolution engine."""

import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"
os.environ["CONNECTION_ENCRYPTION_KEY"] = "test-encryption-key-for-unit-tests"

import pytest
from core.permissions import resolve_allowed_schema


class TestPermissionResolutionStructure:
    """Test structural guarantees of resolve_allowed_schema."""

    def test_permission_resolution_importable(self):
        assert callable(resolve_allowed_schema)
