"""Test fixtures and configuration."""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set test environment variables before importing app modules
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_platform")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("CONNECTION_ENCRYPTION_KEY", "test-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")

import pytest
