"""Auth routes: login, refresh, me."""

import logging

from fastapi import APIRouter, Depends
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import AuthenticationError
from core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from core.tenant_context import CurrentUser, get_current_user
from repositories.user_repo import UserRepository
from schemas.auth import LoginRequest, RefreshRequest, TokenPair, UserOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    """Authenticate user and return JWT token pair.

    The username is looked up across all tenants (login doesn't require
    knowing the tenant beforehand). The tenant_id is embedded in the
    token from the user's record.
    """
    user_repo = UserRepository(db)
    user = await user_repo.find_by_username_across_tenants(request.username)

    from services.audit.audit_service import log_audit_event

    if user is None or not verify_password(request.password, user.password_hash):
        if user is not None:
            await log_audit_event(
                session=db,
                tenant_id=user.tenant_id,
                user_id=user.id,
                action="login_failed",
                details={"username": request.username, "reason": "invalid_credentials"},
                description=f"Failed login attempt for user '{request.username}'",
            )
            await db.commit()
        raise AuthenticationError(detail="Invalid username or password")

    if not user.is_active:
        await log_audit_event(
            session=db,
            tenant_id=user.tenant_id,
            user_id=user.id,
            action="login_failed",
            details={"username": request.username, "reason": "account_disabled"},
            description=f"Login attempt on disabled account '{request.username}'",
        )
        await db.commit()
        raise AuthenticationError(detail="Account is disabled")

    role_names = [role.name for role in user.roles]

    access_token = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        roles=role_names,
    )
    refresh_token = create_refresh_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
    )

    await log_audit_event(
        session=db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        action="login_success",
        details={"username": request.username},
        description=f"User '{request.username}' logged in successfully",
    )
    await db.commit()

    logger.info(
        "User logged in",
        extra={"user_id": str(user.id), "tenant_id": str(user.tenant_id)},
    )

    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    """Refresh token rotation: validate refresh token, issue a new pair."""
    try:
        payload = verify_token(request.refresh_token, expected_type="refresh")
    except JWTError:
        raise AuthenticationError(detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    if not user_id or not tenant_id:
        raise AuthenticationError(detail="Malformed refresh token")

    # Verify user still exists and is active
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_across_tenants(user_id)

    if user is None or not user.is_active:
        raise AuthenticationError(detail="User not found or disabled")

    role_names = [role.name for role in user.roles]

    # Issue a new token pair (rotation — old refresh token is implicitly invalidated by expiry)
    new_access = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        roles=role_names,
    )
    new_refresh = create_refresh_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
    )

    return TokenPair(access_token=new_access, refresh_token=new_refresh)


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Return the authenticated user's information, scoped by their JWT tenant."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_with_roles(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
    )

    if user is None:
        raise AuthenticationError(detail="User not found")

    return UserOut(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=[role.name for role in user.roles],
        created_at=user.created_at,
    )


@router.get("/roles")
async def get_roles(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all roles for the current tenant."""
    from repositories.role_repo import RoleRepository
    role_repo = RoleRepository(db)
    roles = await role_repo.list_all(current_user.tenant_id)
    return [{"id": str(r.id), "name": r.name} for r in roles]
