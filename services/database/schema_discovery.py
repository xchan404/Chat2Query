"""Schema discovery service — introspects live databases via adapters."""

import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from models.schema_metadata import DatabaseSchema, DatabaseTable, DatabaseColumn
from repositories.schema_repo import SchemaRepository
from schemas.schema_metadata import SchemaOut, SyncSchemaResponse
from services.database.adapters.registry import get_adapter
from services.database.connection_service import ConnectionService
from services.database.metadata_cache import metadata_cache

logger = logging.getLogger(__name__)


class SchemaDiscoveryService:
    """Service to discover and cache database schemas."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.schema_repo = SchemaRepository(session)
        self.connection_service = ConnectionService(session)

    async def sync_schema(
        self, tenant_id: uuid.UUID, connection_id: uuid.UUID
    ) -> SyncSchemaResponse:
        """Introspect target DB via adapter and update app DB schema records."""
        connection = await self.connection_service.get_connection(tenant_id, connection_id)
        params = self.connection_service.get_decrypted_params(connection)
        adapter = get_adapter(connection.database_type)

        schemas_info = await adapter.list_schemas(params)

        # Clear existing metadata for clean overwrite
        await self.schema_repo.clear_schemas_by_connection(connection_id)

        schemas_count = 0
        tables_count = 0
        columns_count = 0

        for s_info in schemas_info:
            db_schema = DatabaseSchema(
                connection_id=connection_id,
                schema_name=s_info.schema_name,
                is_active=True,
            )
            tables_info = await adapter.list_tables(params, s_info.schema_name)
            schemas_count += 1

            for t_info in tables_info:
                db_table = DatabaseTable(
                    table_name=t_info.table_name,
                    table_type=t_info.table_type,
                    row_count=t_info.row_count,
                )
                db_schema.tables.append(db_table)
                tables_count += 1

                columns_info = await adapter.list_columns(
                    params, s_info.schema_name, t_info.table_name
                )
                for c_info in columns_info:
                    db_col = DatabaseColumn(
                        column_name=c_info.column_name,
                        data_type=c_info.data_type,
                        is_nullable=c_info.is_nullable,
                        is_primary_key=c_info.is_primary_key,
                        is_foreign_key=c_info.is_foreign_key,
                    )
                    db_table.columns.append(db_col)
                    columns_count += 1

            await self.schema_repo.save_schema(db_schema)

        # Invalidate metadata cache so next fetch reads updated data
        metadata_cache.invalidate(connection_id)

        logger.info(
            "Schema sync completed",
            extra={
                "connection_id": str(connection_id),
                "schemas": schemas_count,
                "tables": tables_count,
                "columns": columns_count,
            },
        )

        return SyncSchemaResponse(
            connection_id=connection_id,
            schemas_synced=schemas_count,
            tables_synced=tables_count,
            columns_synced=columns_count,
            message="Schema synchronization completed successfully",
        )

    async def get_schemas(
        self, tenant_id: uuid.UUID, connection_id: uuid.UUID
    ) -> list[SchemaOut]:
        """Get cached or stored schema metadata for a connection."""
        # Verify connection belongs to tenant
        await self.connection_service.get_connection(tenant_id, connection_id)

        # Check memory cache first
        cached = metadata_cache.get(connection_id)
        if cached is not None:
            return cached

        db_schemas = await self.schema_repo.get_schemas_by_connection(connection_id)
        result = [SchemaOut.model_validate(s) for s in db_schemas]

        metadata_cache.put(connection_id, result)
        return result
