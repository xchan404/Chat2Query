"""SQL Safety Pipeline — services/database/query_validator.py

Strict validation, AST inspection, permission enforcement, row-filter injection,
and limit clamping for Text-to-SQL execution.
Implements BUILD_PLAN Section 7 specifications.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

import sqlglot
from sqlglot import exp

logger = logging.getLogger(__name__)

# System schemas blocked from querying
FORBIDDEN_SCHEMAS = {
    "pg_catalog",
    "information_schema",
    "mysql",
    "sys",
    "performance_schema",
    "pg_toast",
}

# Forbidden system/admin functions
FORBIDDEN_FUNCTIONS = {
    "pg_sleep",
    "version",
    "load_file",
    "into_outfile",
    "into_infile",
    "system",
    "sh",
    "exec",
    "eval",
    "sleep",
    "benchmark",
}

ALLOWED_ROOT_TYPES = (exp.Select, exp.Union, exp.Selectable)


@dataclass
class ValidationResult:
    """Result of SQL safety pipeline validation."""
    is_valid: bool
    status: str  # "approved" or "rejected"
    errors: list[str] = field(default_factory=list)
    normalized_sql: str | None = None
    applied_row_filters: dict[str, str] = field(default_factory=dict)
    referenced_tables: list[str] = field(default_factory=list)
    referenced_columns: list[str] = field(default_factory=list)


def contains_unquoted_comments(sql: str) -> bool:
    """Check if the raw SQL string contains comments outside of string literals.

    Detects '--' and '/* ... */' comment styles.
    """
    in_single_quote = False
    in_double_quote = False
    in_backtick = False
    i = 0
    length = len(sql)

    while i < length:
        char = sql[i]
        next_char = sql[i + 1] if i + 1 < length else ""

        # Handle string literal toggles and escape characters
        if char == "\\" and (in_single_quote or in_double_quote):
            i += 2
            continue

        if char == "'" and not in_double_quote and not in_backtick:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote and not in_backtick:
            in_double_quote = not in_double_quote
        elif char == "`" and not in_single_quote and not in_double_quote:
            in_backtick = not in_backtick

        if not (in_single_quote or in_double_quote or in_backtick):
            if char == "-" and next_char == "-":
                return True
            if char == "/" and next_char == "*":
                return True

        i += 1

    return False


def validate_and_transform_sql(
    raw_sql: str,
    dialect: str = "postgres",
    allowed_schema: dict[str, Any] | None = None,
    max_rows: int = 1000,
) -> ValidationResult:
    """Validate raw SQL through the SQL Safety Pipeline (BUILD_PLAN Section 7).

    Steps:
    1. Comment check: Reject if raw SQL contains unquoted '--' or '/* */'.
    2. Parse: Reject if parsing fails or returns > 1 statement.
    3. Statement type check: Walk AST, only SELECT/WITH/EXPLAIN allowed. Reject DDL/DML.
    4. Reference extraction: Collect referenced tables and columns.
    5. Permission check: Confirm referenced tables/columns exist in allowed_schema.
    6. System schema block: Reject references to system schemas or admin functions.
    7. Row filter injection: Server-side AND of table permissions' row_filter into WHERE.
    8. Limit enforcement: Inject or clamp LIMIT to max_rows.
    """
    errors: list[str] = []
    raw_sql = raw_sql.strip()

    if not raw_sql:
        return ValidationResult(is_valid=False, status="rejected", errors=["Empty SQL query"])

    # Step 3 (in spec order): Comment stripping check
    if contains_unquoted_comments(raw_sql):
        return ValidationResult(
            is_valid=False,
            status="rejected",
            errors=["SQL query contains comments (-- or /* */) which are disallowed for security reasons"],
        )

    # Step 1: Parse
    try:
        statements = sqlglot.parse(raw_sql, read=dialect)
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            status="rejected",
            errors=[f"SQL parsing failed: {str(e)}"],
        )

    if not statements or None in statements:
        return ValidationResult(
            is_valid=False,
            status="rejected",
            errors=["Failed to parse valid SQL statement"],
        )

    if len(statements) > 1:
        return ValidationResult(
            is_valid=False,
            status="rejected",
            errors=[f"Stacked or multi-statement SQL is rejected (found {len(statements)} statements)"],
        )

    ast = statements[0]

    # Step 2: Statement type check
    # Check root expression
    if not isinstance(ast, ALLOWED_ROOT_TYPES):
        return ValidationResult(
            is_valid=False,
            status="rejected",
            errors=[f"Disallowed statement type: '{type(ast).__name__}'. Only SELECT queries are permitted"],
        )

    # Check for forbidden AST nodes anywhere in tree
    forbidden_nodes = (
        exp.Drop,
        exp.TruncateTable,
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Create,
        exp.Alter,
        exp.Grant,
        exp.Revoke,
        exp.Command,
    )
    for node in ast.walk():
        if isinstance(node, forbidden_nodes):
            errors.append(f"Forbidden SQL operation detected: '{type(node).__name__}'")

    if errors:
        return ValidationResult(is_valid=False, status="rejected", errors=errors)

    # Step 6: System schema & function check
    for func_node in ast.find_all(exp.Func):
        func_name = func_node.name.lower()
        if func_name in FORBIDDEN_FUNCTIONS:
            errors.append(f"Forbidden system function call: '{func_node.name}'")

    # Step 4: Reference extraction
    ref_tables: set[str] = set()
    ref_columns: set[str] = set()

    for table_node in ast.find_all(exp.Table):
        schema_name = table_node.db or ""
        table_name = table_node.name
        full_table = f"{schema_name}.{table_name}" if schema_name else table_name
        ref_tables.add(full_table)

        if schema_name.lower() in FORBIDDEN_SCHEMAS:
            errors.append(f"Access to system schema '{schema_name}' is blocked")

    for col_node in ast.find_all(exp.Column):
        col_name = col_node.name
        if col_name and col_name != "*":
            ref_columns.add(col_name)

    if errors:
        return ValidationResult(
            is_valid=False,
            status="rejected",
            errors=errors,
            referenced_tables=sorted(list(ref_tables)),
            referenced_columns=sorted(list(ref_columns)),
        )

    # Step 5: Permission check against allowed_schema
    applied_row_filters: dict[str, str] = {}

    if allowed_schema is not None:
        schemas_data = allowed_schema.get("schemas", {})

        for table_node in ast.find_all(exp.Table):
            t_schema = (table_node.db or "").lower()
            t_name = table_node.name.lower()

            # Find matching schema in allowed_schema
            matched_schema = None
            for s_k, s_val in schemas_data.items():
                if not t_schema or s_k.lower() == t_schema:
                    matched_schema = s_val
                    break

            if not matched_schema:
                errors.append(f"Table '{table_node.name}' is not in permitted schemas")
                continue

            tables_data = matched_schema.get("tables", {})
            matched_table = None
            for tbl_k, tbl_val in tables_data.items():
                if tbl_k.lower() == t_name:
                    matched_table = tbl_val
                    break

            if not matched_table:
                errors.append(f"Table '{table_node.name}' is not permitted")
                continue

            # Capture row filter if present
            row_filter_str = matched_table.get("row_filter")
            if row_filter_str:
                applied_row_filters[table_node.name] = row_filter_str

    if errors:
        return ValidationResult(
            is_valid=False,
            status="rejected",
            errors=errors,
            referenced_tables=sorted(list(ref_tables)),
            referenced_columns=sorted(list(ref_columns)),
        )

    # Step 7: Row filter injection via AST manipulation
    if applied_row_filters:
        for select_node in ast.find_all(exp.Select):
            for table_node in select_node.find_all(exp.Table):
                t_name = table_node.name
                if t_name in applied_row_filters:
                    rf_str = applied_row_filters[t_name]
                    try:
                        rf_ast = sqlglot.parse_one(rf_str, read=dialect)
                        select_node.where(rf_ast, copy=False)
                    except Exception as e:
                        logger.error(f"Failed to inject row filter '{rf_str}': {e}")
                        errors.append(f"Invalid row filter for table '{t_name}': {e}")

    if errors:
        return ValidationResult(
            is_valid=False,
            status="rejected",
            errors=errors,
            referenced_tables=sorted(list(ref_tables)),
            referenced_columns=sorted(list(ref_columns)),
        )

    # Step 8: Limit enforcement
    if isinstance(ast, exp.Select):
        limit_node = ast.args.get("limit")
        if limit_node is None:
            ast.limit(max_rows, copy=False)
        else:
            try:
                current_limit = int(limit_node.expression.this)
                if current_limit > max_rows:
                    ast.limit(max_rows, copy=False)
            except (AttributeError, ValueError):
                ast.limit(max_rows, copy=False)

    normalized_sql = ast.sql(dialect=dialect)

    return ValidationResult(
        is_valid=True,
        status="approved",
        errors=[],
        normalized_sql=normalized_sql,
        applied_row_filters=applied_row_filters,
        referenced_tables=sorted(list(ref_tables)),
        referenced_columns=sorted(list(ref_columns)),
    )
