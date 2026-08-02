"""Password hashing, JWT issue/verify, and refresh token rotation."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    user_id: str,
    tenant_id: str,
    roles: list[str],
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a short-lived JWT access token."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    claims = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        claims.update(extra_claims)

    return jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, tenant_id: str) -> str:
    """Create a long-lived JWT refresh token."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    claims = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Verify and decode a JWT token.

    Returns the decoded claims dict.
    Raises JWTError if invalid, expired, or wrong type.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as e:
        logger.warning("JWT verification failed", extra={"error": str(e)})
        raise

    if payload.get("type") != expected_type:
        raise JWTError(f"Expected token type '{expected_type}', got '{payload.get('type')}'")

    return payload
