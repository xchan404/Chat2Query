"""Unit tests for Section 7 SQL Safety Pipeline (services/database/query_validator.py)."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"
os.environ["CONNECTION_ENCRYPTION_KEY"] = "test-encryption-key-for-unit-tests"

import pytest
from services.database.query_validator import validate_and_transform_sql, contains_unquoted_comments

# Sample allowed schema structure for testing
SAMPLE_ALLOWED_SCHEMA = {
    "schemas": {
        "public": {
            "tables": {
                "users": {
                    "columns": ["id", "username", "email", "status", "created_at"],
                    "masked_columns": ["email"],
                    "row_filter": "status = 'active'",
                    "access_type": "read",
                },
                "orders": {
                    "columns": ["id", "user_id", "total_amount", "order_date"],
                    "masked_columns": [],
                    "row_filter": None,
                    "access_type": "read",
                },
            }
        }
    }
}


class TestCommentStrippingCheck:
    """Step 3: Reject queries containing unquoted comments."""

    def test_single_line_comment_rejected(self):
        sql = "SELECT id, username FROM users -- comment here"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert not res.is_valid
        assert res.status == "rejected"
        assert any("comment" in err.lower() for err in res.errors)

    def test_multi_line_comment_rejected(self):
        sql = "SELECT id /* secret comment */ FROM users"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert not res.is_valid
        assert res.status == "rejected"

    def test_comment_inside_string_literal_allowed(self):
        sql = "SELECT id FROM users WHERE username = 'user--name'"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert res.is_valid
        assert res.status == "approved"


class TestMultiStatementCheck:
    """Step 1 & 2: Reject stacked/multi-statement SQL."""

    def test_stacked_statements_rejected(self):
        sql = "SELECT id FROM users; DROP TABLE users;"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert not res.is_valid
        assert res.status == "rejected"
        assert any("stacked" in err.lower() or "multi-statement" in err.lower() for err in res.errors)


class TestStatementTypeCheck:
    """Step 2: Reject non-SELECT/WITH/EXPLAIN statements."""

    @pytest.mark.parametrize("statement", [
        "DROP TABLE users",
        "TRUNCATE TABLE users",
        "ALTER TABLE users ADD COLUMN age INT",
        "CREATE TABLE test (id INT)",
        "GRANT ALL PRIVILEGES ON users TO public",
        "REVOKE ALL ON users FROM public",
        "DELETE FROM users WHERE id = 1",
        "INSERT INTO users (username) VALUES ('hacker')",
        "UPDATE users SET status = 'deleted'",
    ])
    def test_destructive_and_dml_rejected(self, statement: str):
        res = validate_and_transform_sql(statement, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert not res.is_valid
        assert res.status == "rejected"


class TestSystemSchemaBlock:
    """Step 6: Reject system schemas and forbidden admin functions."""

    def test_pg_catalog_rejected(self):
        sql = "SELECT * FROM pg_catalog.pg_user"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert not res.is_valid
        assert any("system schema" in err.lower() for err in res.errors)

    def test_information_schema_rejected(self):
        sql = "SELECT * FROM information_schema.tables"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert not res.is_valid

    def test_mysql_system_schema_rejected(self):
        sql = "SELECT * FROM mysql.user"
        res = validate_and_transform_sql(sql, dialect="mysql", allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert not res.is_valid

    def test_pg_sleep_function_rejected(self):
        sql = "SELECT pg_sleep(5) FROM users"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert not res.is_valid
        assert any("system function" in err.lower() for err in res.errors)


class TestPermissionCheck:
    """Step 5: Reference extraction & permission check."""

    def test_unpermitted_table_rejected(self):
        sql = "SELECT * FROM secret_financials"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert not res.is_valid
        assert any("secret_financials" in err for err in res.errors)

    def test_permitted_table_accepted(self):
        sql = "SELECT id, username FROM users"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert res.is_valid
        assert res.status == "approved"
        assert "users" in res.referenced_tables


class TestRowFilterInjection:
    """Step 7: Server-side AST rewrite to inject row_filter into WHERE clause."""

    def test_row_filter_injected_when_no_where_clause(self):
        sql = "SELECT id, username FROM users"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert res.is_valid
        assert "status = 'active'" in res.normalized_sql.lower()
        assert "users" in res.applied_row_filters

    def test_row_filter_injected_with_existing_where_clause(self):
        sql = "SELECT id, username FROM users WHERE id = 5"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert res.is_valid
        # Result must AND the filter with existing condition
        norm = res.normalized_sql.lower()
        assert "id = 5" in norm
        assert "status = 'active'" in norm
        assert "and" in norm


class TestLimitEnforcement:
    """Step 8: Inject or clamp LIMIT clause."""

    def test_limit_injected_when_missing(self):
        sql = "SELECT id, username FROM users"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA, max_rows=100)
        assert res.is_valid
        assert "limit 100" in res.normalized_sql.lower()

    def test_limit_clamped_when_exceeding_max(self):
        sql = "SELECT id, username FROM users LIMIT 5000"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA, max_rows=500)
        assert res.is_valid
        assert "limit 500" in res.normalized_sql.lower()

    def test_limit_preserved_when_under_max(self):
        sql = "SELECT id, username FROM users LIMIT 10"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA, max_rows=100)
        assert res.is_valid
        assert "limit 10" in res.normalized_sql.lower()
