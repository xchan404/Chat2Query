"""Initial schema — full platform schema.

Revision ID: 001_initial
Revises: None
Create Date: 2026-08-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable required extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"vector\"")

    # --- tenants ---
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("settings", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    # --- roles ---
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"])

    # --- user_roles ---
    op.create_table(
        "user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
    )

    # --- database_connections ---
    op.create_table(
        "database_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("database_type", sa.String(50), nullable=False),
        sa.Column("host", sa.String(255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("database_name", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("encrypted_password", sa.Text(), nullable=False),
        sa.Column("encrypted_connection_string", sa.Text(), nullable=True),
        sa.Column("ssl_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("connection_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_database_connections_tenant_id", "database_connections", ["tenant_id"])

    # --- database_schemas ---
    op.create_table(
        "database_schemas",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("schema_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["connection_id"], ["database_connections.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_database_schemas_connection_id", "database_schemas", ["connection_id"])

    # --- database_tables ---
    op.create_table(
        "database_tables",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("schema_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("table_name", sa.String(255), nullable=False),
        sa.Column("table_type", sa.String(50), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("table_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["schema_id"], ["database_schemas.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_database_tables_schema_id", "database_tables", ["schema_id"])

    # --- database_columns ---
    op.create_table(
        "database_columns",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("table_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("column_name", sa.String(255), nullable=False),
        sa.Column("data_type", sa.String(100), nullable=False),
        sa.Column("is_nullable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_primary_key", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_foreign_key", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("column_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["table_id"], ["database_tables.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_database_columns_table_id", "database_columns", ["table_id"])

    # --- table_permissions ---
    op.create_table(
        "table_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("schema_name", sa.String(255), nullable=False),
        sa.Column("table_name", sa.String(255), nullable=False),
        sa.Column("access_type", sa.String(50), nullable=False, server_default=sa.text("'read'")),
        sa.Column("row_filter", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connection_id"], ["database_connections.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_table_permissions_role_id", "table_permissions", ["role_id"])
    op.create_index("ix_table_permissions_connection_id", "table_permissions", ["connection_id"])

    # --- column_permissions ---
    op.create_table(
        "column_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("table_permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("column_name", sa.String(255), nullable=False),
        sa.Column("is_allowed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_masked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["table_permission_id"], ["table_permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_column_permissions_table_permission_id", "column_permissions", ["table_permission_id"])
    op.create_index("ix_column_permissions_role_id", "column_permissions", ["role_id"])

    # --- knowledge_bases ---
    op.create_table(
        "knowledge_bases",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("kb_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_knowledge_bases_tenant_id", "knowledge_bases", ["tenant_id"])

    # --- files ---
    op.create_table(
        "files",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("processing_status", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chunk_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("file_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "processing_status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_files_processing_status",
        ),
    )
    op.create_index("ix_files_tenant_id", "files", ["tenant_id"])
    op.create_index("ix_files_knowledge_base_id", "files", ["knowledge_base_id"])

    # --- document_chunks ---
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        # embedding column added via raw SQL below for proper vector(1024) type
        sa.Column("chunk_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_document_chunks_file_id", "document_chunks", ["file_id"])
    op.create_index("ix_document_chunks_tenant_id", "document_chunks", ["tenant_id"])
    op.create_index("ix_document_chunks_knowledge_base_id", "document_chunks", ["knowledge_base_id"])

    # Add vector embedding column via raw SQL (pgvector type)
    op.execute("ALTER TABLE document_chunks ADD COLUMN embedding vector(1024)")

    # --- conversations ---
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("conversation_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_conversations_tenant_id", "conversations", ["tenant_id"])
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    # --- messages ---
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(50), nullable=True),
        sa.Column("sources_used", postgresql.JSONB(), nullable=True),
        sa.Column("message_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_message_id"], ["messages.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    # --- query_executions ---
    op.create_table(
        "query_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("generated_sql", sa.Text(), nullable=True),
        sa.Column("normalized_sql", sa.Text(), nullable=True),
        sa.Column("validation_status", sa.String(50), nullable=False),
        sa.Column("validation_errors", postgresql.JSONB(), nullable=True),
        sa.Column("applied_row_filters", postgresql.JSONB(), nullable=True),
        sa.Column("referenced_tables", postgresql.JSONB(), nullable=True),
        sa.Column("referenced_columns", postgresql.JSONB(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("execution_time_ms", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connection_id"], ["database_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_query_executions_tenant_id", "query_executions", ["tenant_id"])
    op.create_index("ix_query_executions_connection_id", "query_executions", ["connection_id"])

    # --- message_citations ---
    op.create_table(
        "message_citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("query_execution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_name", sa.String(500), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("citation_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["query_execution_id"], ["query_executions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["chunk_id"], ["document_chunks.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_message_citations_message_id", "message_citations", ["message_id"])

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("request_id", sa.String(255), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("message_citations")
    op.drop_table("query_executions")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("document_chunks")
    op.drop_table("files")
    op.drop_table("knowledge_bases")
    op.drop_table("column_permissions")
    op.drop_table("table_permissions")
    op.drop_table("database_columns")
    op.drop_table("database_tables")
    op.drop_table("database_schemas")
    op.drop_table("database_connections")
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("users")
    op.drop_table("tenants")
