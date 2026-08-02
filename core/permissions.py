"""Effective permissions resolution engine.

Given a (user, connection_id), merges role-level table and column permissions
to produce the effective `allowed_schema` structure used by the SQL safety pipeline.
"""

import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.permission_repo import PermissionRepository
from repositories.schema_repo import SchemaRepository
from repositories.user_repo import UserRepository


async def resolve_allowed_schema(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    connection_id: uuid.UUID,
) -> dict[str, Any]:
    """Resolve effective allowed_schema for a user on a specific connection.

    Returns dict shape:
    {
        "schemas": {
            "public": {
                "tables": {
                    "users": {
                        "columns": ["id", "username", "email"],
                        "masked_columns": ["email"],
                        "row_filter": "status = 'active'",
                        "access_type": "read"
                    }
                }
            }
        }
    }
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_with_roles(tenant_id, user_id)
    if user is None:
        return {"schemas": {}}

    role_ids = [r.id for r in user.roles]

    # Fetch all permissions for these roles on connection
    perm_repo = PermissionRepository(db)
    table_perms = await perm_repo.get_table_permissions_by_connection(connection_id, role_ids=role_ids)

    # Fetch full discovered schema
    schema_repo = SchemaRepository(db)
    db_schemas = await schema_repo.get_schemas_by_connection(connection_id)

    # If no permissions configured for any role, default to allowing full schema for all tables
    if not table_perms:
        allowed: dict[str, Any] = {"schemas": {}}
        for s in db_schemas:
            schema_entry: dict[str, Any] = {"tables": {}}
            for t in s.tables:
                schema_entry["tables"][t.table_name] = {
                    "columns": [c.column_name for c in t.columns],
                    "masked_columns": [c.column_name for c in t.columns if c.is_sensitive],
                    "row_filter": None,
                    "access_type": "read",
                }
            allowed["schemas"][s.schema_name] = schema_entry
        return allowed

    # Index permissions by (schema_name, table_name)
    # Merge permissions across roles (read/write access type, combine column permissions)
    allowed_tables: dict[tuple[str, str], dict[str, Any]] = {}
    for tp in table_perms:
        if tp.access_type == "none":
            continue

        key = (tp.schema_name.lower(), tp.table_name.lower())
        if key not in allowed_tables:
            allowed_tables[key] = {
                "schema_name": tp.schema_name,
                "table_name": tp.table_name,
                "access_type": tp.access_type,
                "row_filter": tp.row_filter,
                "column_perms": {},
            }
        else:
            # Upgrade access type if write
            if tp.access_type == "write":
                allowed_tables[key]["access_type"] = "write"
            # Keep row_filter if provided
            if tp.row_filter and not allowed_tables[key]["row_filter"]:
                allowed_tables[key]["row_filter"] = tp.row_filter

        for cp in tp.column_permissions:
            col_key = cp.column_name.lower()
            allowed_tables[key]["column_perms"][col_key] = {
                "column_name": cp.column_name,
                "is_allowed": cp.is_allowed,
                "is_masked": cp.is_masked,
            }

    # Construct resulting allowed_schema
    result_schemas: dict[str, Any] = {}

    for s in db_schemas:
        s_name_lower = s.schema_name.lower()
        tables_dict: dict[str, Any] = {}

        for t in s.tables:
            t_name_lower = t.table_name.lower()
            key = (s_name_lower, t_name_lower)

            # Check if this table is permitted
            if key not in allowed_tables:
                continue

            perm_data = allowed_tables[key]
            col_perms = perm_data["column_perms"]

            allowed_cols: list[str] = []
            masked_cols: list[str] = []

            for c in t.columns:
                c_lower = c.column_name.lower()
                # If explicit column permissions exist, honor them; else include column by default
                if col_perms:
                    if c_lower in col_perms and col_perms[c_lower]["is_allowed"]:
                        allowed_cols.append(c.column_name)
                        if col_perms[c_lower]["is_masked"] or c.is_sensitive:
                            masked_cols.append(c.column_name)
                else:
                    allowed_cols.append(c.column_name)
                    if c.is_sensitive:
                        masked_cols.append(c.column_name)

            if allowed_cols:
                tables_dict[t.table_name] = {
                    "columns": allowed_cols,
                    "masked_columns": masked_cols,
                    "row_filter": perm_data["row_filter"],
                    "access_type": perm_data["access_type"],
                }

        if tables_dict:
            result_schemas[s.schema_name] = {"tables": tables_dict}

    return {"schemas": result_schemas}
