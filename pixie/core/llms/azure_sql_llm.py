from __future__ import annotations

from typing import Optional

from ..utils.schema import get_schema_manager
from .azure_openai_llm import AzureOpenAILLM


class AzureSQLLLM(AzureOpenAILLM):
    """Azure-based SQL generator for database queries.

    The generate_sql method uses dynamic schema loading to produce SQL queries
    based on the actual database schema definition rather than hard-coded information.
    """

    def __init__(
        self,
        api_version: str,
        api_endpoint: str,
        api_key: str,
        model_version: str,
        temperature: float = 0.01,
        model_name: str = "azure-sql-llm",
        default_table: str = "printers",
    ):
        super().__init__(api_version, api_endpoint, api_key, model_version, temperature)
        self.model_name = model_name
        self.default_table = default_table

    def generate_sql(
        self,
        question: Optional[str],
        attributes: Optional[dict] = None,
        table_name: Optional[str] = None,
    ) -> str:
        q = (question or "").strip()
        attrs = attributes or {}
        table = table_name or self.default_table

        if not self.model:
            raise ValueError("Azure model is not available")

        # Generate schema information dynamically
        schema_manager = get_schema_manager()
        schema_info = schema_manager.generate_table_description(table)

        # Build prompt with specific instructions for budget handling
        prompt = f"""Generate a single SQL query (no explanation) that answers the user's request.

{schema_info}

User Question: {q}
User Attributes: {attrs}

IMPORTANT RULES:
1. Always use 'price' column for price comparisons (not price_cents)
2. For budget constraints, use <= for maximum budget
3. Use exact string matching for brands and technology
4. Convert technology to lowercase for comparison: LOWER(technology) = 'inkjet'
5. Use boolean values true/false (not 1/0)
6. IGNORE vague responses like "weet ik niet", "geen idee", "maakt niet uit" - no WHERE clause

Examples:
- Budget "200 euro" → WHERE price <= 200
- Budget "maximaal 150" → WHERE price <= 150
- Budget "weet ik niet" → IGNORE (no budget filter)
- Brand "HP" → WHERE brand = 'HP'
- Brand "geen voorkeur" → IGNORE (no brand filter)
- Technology "inkjet" → WHERE LOWER(technology) = 'inkjet'
- Technology "maakt niet uit" → IGNORE (no technology filter)

Generate the SQL query:"""

        response = self.model.invoke(prompt)

        if hasattr(response, "content"):
            sql = response.content.strip()
            # Remove any markdown formatting if present
            if sql.startswith("```sql"):
                sql = sql.replace("```sql", "").replace("```", "").strip()
            return sql

        raise ValueError("Invalid response format from Azure model")
