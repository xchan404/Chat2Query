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


class LLMError(Exception):
    """Custom exception for LLM generation failures."""
    pass


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
            raise LLMError("ANTHROPIC_API_KEY is not configured. Please add it to your environment variables.")

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
                
                # Check for HTTP errors (e.g., 400 Out of Credits, 401 Unauthorized)
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        error_message = error_data.get("error", {}).get("message", response.text)
                    except Exception:
                        error_message = response.text
                    
                    raise LLMError(f"Anthropic API Error ({response.status_code}): {error_message}")
                
                response.raise_for_status()
                data = response.json()
                content = data["content"][0]["text"]

                # Extract SQL from code block
                match = re.search(r"```sql\s*(.*?)\s*```", content, re.DOTALL)
                if match:
                    return match.group(1).strip()
                return content.strip()
        except LLMError:
            raise
        except Exception as e:
            logger.error(f"LLM generation failed unexpectedly: {e}")
            raise LLMError(f"Failed to generate SQL due to unexpected LLM error: {str(e)}")


llm_client = LLMClient()
