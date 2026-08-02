"""Script to export openapi.json documentation schema."""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://platform_user:platform_pass@localhost:5432/platform"
os.environ["CONNECTION_ENCRYPTION_KEY"] = "change-me-generate-a-real-fernet-key"

from app.main import app

openapi_schema = app.openapi()
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "openapi.json")

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(openapi_schema, f, indent=2)

print(f"Exported OpenAPI spec to {out_path} ({len(json.dumps(openapi_schema))} bytes)")
