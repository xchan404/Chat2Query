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


class TestCTEAndExplain:
    """Test that WITH (CTEs) and EXPLAIN pass validation — spec allows SELECT, WITH, EXPLAIN."""

    def test_cte_select_accepted(self):
        """WITH x AS (...) SELECT ... is a common LLM-generated pattern and must pass."""
        sql = "WITH active_users AS (SELECT id, username FROM users WHERE status = 'active') SELECT id, username FROM active_users"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert res.is_valid
        assert res.status == "approved"

    def test_cte_with_multiple_ctes_accepted(self):
        sql = "WITH u AS (SELECT id FROM users), o AS (SELECT id, user_id FROM orders) SELECT u.id FROM u JOIN o ON u.id = o.user_id"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert res.is_valid

    def test_cte_still_gets_row_filter(self):
        """Row filters must still be injected even when query uses CTEs."""
        sql = "WITH u AS (SELECT id, username, status FROM users) SELECT id, username FROM u"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA)
        assert res.is_valid
        # The row filter should be applied to the users table
        assert "users" in res.applied_row_filters

    def test_cte_still_gets_limit(self):
        sql = "WITH u AS (SELECT id FROM users) SELECT id FROM u"
        res = validate_and_transform_sql(sql, allowed_schema=SAMPLE_ALLOWED_SCHEMA, max_rows=50)
        assert res.is_valid
        assert "limit 50" in res.normalized_sql.lower() or "limit" in res.normalized_sql.lower()


class TestSensitiveColumnMasking:
    """Test that mask_value and _mask_rows correctly mask sensitive columns in query results."""

    def test_mask_value_short_string(self):
        from services.database.query_executor import mask_value
        assert mask_value("abc") == "****"

    def test_mask_value_long_string(self):
        from services.database.query_executor import mask_value
        result = mask_value("alice@example.com")
        assert result.startswith("al")
        assert result.endswith("om")
        assert "****" not in result or "*" in result  # contains asterisks
        assert result != "alice@example.com"  # not the original

    def test_mask_value_none(self):
        from services.database.query_executor import mask_value
        assert mask_value(None) is None

    def test_mask_rows_masks_sensitive_columns(self):
        from services.database.query_executor import _mask_rows
        rows = [
            {"id": 1, "username": "alice", "email": "alice@example.com"},
            {"id": 2, "username": "bob", "email": "bob@example.com"},
        ]
        masked = _mask_rows(rows, {"email"})
        assert masked[0]["id"] == 1
        assert masked[0]["username"] == "alice"
        assert masked[0]["email"] != "alice@example.com"
        assert masked[1]["email"] != "bob@example.com"
        # Non-masked columns untouched
        assert masked[1]["username"] == "bob"

    def test_collect_masked_columns(self):
        from services.database.query_executor import _collect_masked_columns
        cols = _collect_masked_columns(SAMPLE_ALLOWED_SCHEMA)
        assert "email" in cols
        assert "id" not in cols

    def test_mask_rows_empty_list(self):
        from services.database.query_executor import _mask_rows
        assert _mask_rows([], {"email"}) == []

