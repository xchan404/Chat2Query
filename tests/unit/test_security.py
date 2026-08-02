"""Unit tests for core/security.py — password hashing, JWT encode/decode, token types."""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Set test env vars before any app imports
os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"

import uuid

import pytest
from jose import JWTError

from core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_returns_string(self):
        hashed = hash_password("my-secure-password")
        assert isinstance(hashed, str)
        assert hashed != "my-secure-password"

    def test_hash_password_different_each_time(self):
        hash1 = hash_password("same-password")
        hash2 = hash_password("same-password")
        assert hash1 != hash2  # bcrypt uses random salt

    def test_verify_password_correct(self):
        password = "test-password-123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_verify_password_empty_string(self):
        hashed = hash_password("real-password")
        assert verify_password("", hashed) is False


class TestJWTAccessToken:
    """Test access token creation and verification."""

    def test_create_access_token_returns_string(self):
        token = create_access_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            roles=["admin"],
        )
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_correct_claims(self):
        user_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())
        roles = ["admin", "analyst"]

        token = create_access_token(user_id=user_id, tenant_id=tenant_id, roles=roles)
        payload = verify_token(token, expected_type="access")

        assert payload["sub"] == user_id
        assert payload["tenant_id"] == tenant_id
        assert payload["roles"] == roles
        assert payload["type"] == "access"

    def test_access_token_with_extra_claims(self):
        token = create_access_token(
            user_id="user-1",
            tenant_id="tenant-1",
            roles=["admin"],
            extra_claims={"custom_field": "custom_value"},
        )
        payload = verify_token(token, expected_type="access")
        assert payload["custom_field"] == "custom_value"


class TestJWTRefreshToken:
    """Test refresh token creation and verification."""

    def test_create_refresh_token_returns_string(self):
        token = create_refresh_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
        )
        assert isinstance(token, str)

    def test_refresh_token_contains_correct_claims(self):
        user_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())

        token = create_refresh_token(user_id=user_id, tenant_id=tenant_id)
        payload = verify_token(token, expected_type="refresh")

        assert payload["sub"] == user_id
        assert payload["tenant_id"] == tenant_id
        assert payload["type"] == "refresh"

    def test_refresh_token_rejected_as_access(self):
        token = create_refresh_token(user_id="u", tenant_id="t")
        with pytest.raises(JWTError, match="Expected token type 'access'"):
            verify_token(token, expected_type="access")

    def test_access_token_rejected_as_refresh(self):
        token = create_access_token(user_id="u", tenant_id="t", roles=[])
        with pytest.raises(JWTError, match="Expected token type 'refresh'"):
            verify_token(token, expected_type="refresh")


class TestTokenVerification:
    """Test token verification edge cases."""

    def test_invalid_token_raises_jwt_error(self):
        with pytest.raises(JWTError):
            verify_token("not-a-real-jwt-token")

    def test_tampered_token_raises_jwt_error(self):
        token = create_access_token(user_id="u", tenant_id="t", roles=[])
        # Tamper with the token by changing a character
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            verify_token(tampered)

    def test_empty_token_raises_jwt_error(self):
        with pytest.raises(JWTError):
            verify_token("")
