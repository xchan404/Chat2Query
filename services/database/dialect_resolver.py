"""Dialect resolver mapping database connection types to SQLGlot dialects."""

_DIALECT_MAP = {
    "postgresql": "postgres",
    "postgres": "postgres",
    "mysql": "mysql",
    "sqlite": "sqlite",
    "oracle": "oracle",
    "mssql": "tsql",
    "sqlserver": "tsql",
}


def resolve_sqlglot_dialect(database_type: str) -> str:
    """Map a database_type string to its SQLGlot dialect equivalent.

    Defaults to 'postgres' if unknown.
    """
    return _DIALECT_MAP.get(database_type.lower(), "postgres")
