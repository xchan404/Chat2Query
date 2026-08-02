"""Tenant context extraction from JWT — FastAPI dependency."""

import logging
from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.exceptions import AuthenticationError
from core.security import verify_token

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    """Represents the authenticated user context extracted from the JWT."""
    user_id: str
    tenant_id: str
    roles: list[str]


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> CurrentUser:
    """Extract and validate the current user from the JWT Bearer token.

    This dependency ensures every protected route has access to tenant_id,
    user_id, and roles without ever reading them from request body/query params.
    """
    if credentials is None:
        raise AuthenticationError(detail="Missing authentication token")

    try:
        payload = verify_token(credentials.credentials, expected_type="access")
    except JWTError:
        raise AuthenticationError(detail="Invalid or expired token")

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    roles = payload.get("roles", [])

    if not user_id or not tenant_id:
        raise AuthenticationError(detail="Malformed token claims")

    return CurrentUser(user_id=user_id, tenant_id=tenant_id, roles=roles)


def require_role(required_role: str):
    """Return a dependency that checks the user has the specified role."""

    async def _check_role(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if required_role not in current_user.roles:
            from app.exceptions import AuthorizationError
            raise AuthorizationError(detail=f"Role '{required_role}' required")
        return current_user

    return _check_role
