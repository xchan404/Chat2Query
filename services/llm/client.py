"""Thin wrapper around Anthropic API for LLM operations.

Single place to swap models/providers or adjust prompts.
"""

import json
import logging
import re
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin Anthropic LLM client wrapper."""

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = getattr(settings, "ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")

    async def generate_sql(
        self,
        question: str,
        allowed_schema: dict[str, Any],
        database_type: str = "postgresql",
    ) -> str:
        """Generate read-only SQL from natural language question and allowed schema."""
        schema_summary = json.dumps(allowed_schema, indent=2)

        prompt = f"""You are a Text-to-SQL expert for {database_type}.
Given the following database schema (ONLY touch tables and columns explicitly listed in this schema):

{schema_summary}

User Question: {question}

Instructions:
1. Generate a single, syntactically valid read-only SQL query (SELECT statement only).
2. DO NOT use multi-statements or comments.
3. Only reference schemas, tables, and columns explicitly present in the provided schema.
4. AGGREGATION RULE: If the user asks for totals, sums, counts, averages, or statistics (e.g., "total sum", "how many", "average amount"), use appropriate SQL aggregate functions such as SUM(), COUNT(), AVG(), or GROUP BY. Do NOT perform a simple row scan when an aggregate calculation is requested.
5. Output ONLY the raw SQL statement inside ```sql ... ``` codeblock without any explanation.
"""

        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not configured — using fallback mock SQL generator")
            return self._fallback_sql_generator(question, allowed_schema)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["content"][0]["text"]

                # Extract SQL from code block
                match = re.search(r"```sql\s*(.*?)\s*```", content, re.DOTALL)
                if match:
                    return match.group(1).strip()
                return content.strip()
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._fallback_sql_generator(question, allowed_schema)

    def _fallback_sql_generator(
        self, question: str, allowed_schema: dict[str, Any]
    ) -> str:
        """Heuristic fallback when API key is missing or API call fails."""
        schemas = allowed_schema.get("schemas", {})
        if not schemas:
            return "SELECT 1"

        first_schema_name = list(schemas.keys())[0]
        tables = schemas[first_schema_name].get("tables", {})
        if not tables:
            return "SELECT 1"

        first_table_name = list(tables.keys())[0]
        tbl_info = tables[first_table_name]
        columns = tbl_info.get("columns", ["*"]) if isinstance(tbl_info, dict) else tbl_info

        q_lower = question.lower()
        if any(w in q_lower for w in ["avg", "average"]):
            num_col = next((c for c in columns if "amount" in c or "val" in c), columns[0] if columns else "*")
            return f"SELECT AVG({num_col}) AS average_amount FROM {first_table_name}"
        elif any(w in q_lower for w in ["count", "how many", "number of"]):
            return f"SELECT COUNT(*) AS total_count FROM {first_table_name}"
        elif any(w in q_lower for w in ["total", "sum", "revenue"]):
            num_col = next((c for c in columns if "amount" in c or "total" in c or "val" in c), columns[0] if columns else "*")
            return f"SELECT SUM({num_col}) AS total_amount FROM {first_table_name}"
        elif "amount" in q_lower:
            num_col = next((c for c in columns if "amount" in c or "total" in c or "val" in c), columns[0] if columns else "*")
            return f"SELECT SUM({num_col}) AS total_amount FROM {first_table_name}"

        cols_str = ", ".join(columns[:5]) if columns else "*"
        return f"SELECT {cols_str} FROM {first_table_name} LIMIT 10"


llm_client = LLMClient()
