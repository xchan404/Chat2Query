"""Connection service — CRUD + encryption orchestration.

Handles creating, updating, and deleting database connections
with transparent credential encryption. Passwords are encrypted
before storage and decrypted only transiently in memory.
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError, ValidationError
from core.encryption import decrypt_value, encrypt_value
from models.connection import DatabaseConnection
from repositories.connection_repo import ConnectionRepository
from schemas.connection import ConnectionCreate, ConnectionUpdate
from services.database.adapters.base import ConnectionParams
from services.database.adapters.registry import get_adapter, get_supported_types
from services.database.connection_pool import connection_cache

logger = logging.getLogger(__name__)


class ConnectionService:
    """Service layer for database connection management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ConnectionRepository(session)

    async def create_connection(
        self, tenant_id: uuid.UUID, data: ConnectionCreate
    ) -> DatabaseConnection:
        """Create a new database connection with encrypted credentials."""
        # Validate database type
        if data.database_type not in get_supported_types():
            raise ValidationError(
                detail=f"Unsupported database type: '{data.database_type}'. "
                f"Supported: {', '.join(get_supported_types())}"
            )

        # Encrypt password before storage
        encrypted_password = encrypt_value(data.password)

        # Build connection string and encrypt it too
        conn_string = (
            f"{data.database_type}://{data.username}:{data.password}"
            f"@{data.host}:{data.port}/{data.database_name}"
        )
        encrypted_conn_string = encrypt_value(conn_string)

        connection = DatabaseConnection(
            tenant_id=tenant_id,
            name=data.name,
            database_type=data.database_type,
            host=data.host,
            port=data.port,
            database_name=data.database_name,
            username=data.username,
            encrypted_password=encrypted_password,
            encrypted_connection_string=encrypted_conn_string,
            ssl_enabled=data.ssl_enabled,
        )

        created = await self.repo.create(connection)
        logger.info(
            "Connection created",
            extra={
                "connection_id": str(created.id),
                "tenant_id": str(tenant_id),
                "database_type": data.database_type,
            },
        )
        return created

    async def get_connection(
        self, tenant_id: uuid.UUID, connection_id: uuid.UUID
    ) -> DatabaseConnection:
        """Get a connection by ID, scoped to tenant."""
        conn = await self.repo.get_by_id(tenant_id, connection_id)
        if conn is None:
            raise NotFoundError(detail="Database connection not found")
        return conn

    async def list_connections(
        self, tenant_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[DatabaseConnection]:
        """List all connections for a tenant."""
        return list(await self.repo.list_all(tenant_id, limit=limit, offset=offset))

    async def update_connection(
        self, tenant_id: uuid.UUID, connection_id: uuid.UUID, data: ConnectionUpdate
    ) -> DatabaseConnection:
        """Update an existing connection. Re-encrypts password if changed."""
        conn = await self.get_connection(tenant_id, connection_id)

        update_values = {}
        if data.name is not None:
            update_values["name"] = data.name
        if data.host is not None:
            update_values["host"] = data.host
        if data.port is not None:
            update_values["port"] = data.port
        if data.database_name is not None:
            update_values["database_name"] = data.database_name
        if data.username is not None:
            update_values["username"] = data.username
        if data.ssl_enabled is not None:
            update_values["ssl_enabled"] = data.ssl_enabled

        if data.password is not None:
            update_values["encrypted_password"] = encrypt_value(data.password)
            # Rebuild and re-encrypt connection string
            host = data.host or conn.host
            port = data.port or conn.port
            db_name = data.database_name or conn.database_name
            username = data.username or conn.username
            conn_string = (
                f"{conn.database_type}://{username}:{data.password}"
                f"@{host}:{port}/{db_name}"
            )
            update_values["encrypted_connection_string"] = encrypt_value(conn_string)

        if not update_values:
            return conn

        # Invalidate cache since credentials may have changed
        connection_cache.invalidate(str(connection_id))

        updated = await self.repo.update_by_id(tenant_id, connection_id, update_values)
        if updated is None:
            raise NotFoundError(detail="Database connection not found")

        logger.info(
            "Connection updated",
            extra={"connection_id": str(connection_id), "tenant_id": str(tenant_id)},
        )
        return updated

    async def delete_connection(
        self, tenant_id: uuid.UUID, connection_id: uuid.UUID
    ) -> bool:
        """Delete a connection. Invalidates any cached params."""
        connection_cache.invalidate(str(connection_id))
        deleted = await self.repo.delete_by_id(tenant_id, connection_id)
        if not deleted:
            raise NotFoundError(detail="Database connection not found")
        logger.info(
            "Connection deleted",
            extra={"connection_id": str(connection_id), "tenant_id": str(tenant_id)},
        )
        return True

    def get_decrypted_params(self, conn: DatabaseConnection) -> ConnectionParams:
        """Decrypt credentials and return ConnectionParams.

        The returned object holds the plaintext password ONLY in memory —
        it is never persisted or logged.
        """
        # Check cache first
        cached = connection_cache.get(str(conn.id))
        if cached is not None:
            return cached[0]

        # Decrypt password
        plaintext_password = decrypt_value(conn.encrypted_password)

        params = ConnectionParams(
            host=conn.host,
            port=conn.port,
            database_name=conn.database_name,
            username=conn.username,
            password=plaintext_password,
            ssl_enabled=conn.ssl_enabled,
        )

        # Cache the decrypted params
        connection_cache.put(str(conn.id), params, conn.database_type)

        return params
