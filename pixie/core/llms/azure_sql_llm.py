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
            return self._fallback_sql_generation(q, attrs, table)

        try:
            # Generate schema information dynamically
            schema_manager = get_schema_manager()
            schema_info = schema_manager.generate_table_description(table)

            # Build prompt with specific instructions for budget handling
            prompt = (
                f"Generate a single SQL query (no explanation) that answers the user's request.\n\n"
                f"{schema_info}\n\n"
                f"User Question: {q}\n"
                f"User Attributes: {attrs}\n\n"
                "IMPORTANT RULES:\n"
                "1. Always use 'price' column for price comparisons (not price_cents)\n"
                "2. For budget constraints, use <= for maximum budget\n"
                "3. Use exact string matching for brands and technology\n"
                "4. Convert technology to lowercase for comparison: LOWER(technology) = 'inkjet'\n"
                "5. Use boolean values true/false (not 1/0)\n"
                '6. IGNORE vague responses like "weet ik niet", "geen idee", '
                '"maakt niet uit" - no WHERE clause\n\n'
                "Examples:\n"
                '- Budget "200 euro" → WHERE price <= 200\n'
                '- Budget "maximaal 150" → WHERE price <= 150\n'
                '- Budget "weet ik niet" → IGNORE (no budget filter)\n'
                "- Brand \"HP\" → WHERE brand = 'HP'\n"
                '- Brand "geen voorkeur" → IGNORE (no brand filter)\n'
                "- Technology \"inkjet\" → WHERE LOWER(technology) = 'inkjet'\n"
                '- Technology "maakt niet uit" → IGNORE (no technology filter)\n\n'
                "Generate the SQL query:"
            )

            response = self.model.invoke(prompt)

            if hasattr(response, "content"):
                sql = response.content.strip()
                # Remove any markdown formatting if present
                if sql.startswith("```sql"):
                    sql = sql.replace("```sql", "").replace("```", "").strip()
                return sql

            raise ValueError("Invalid response format from Azure model")
        except Exception:
            return self._fallback_sql_generation(q, attrs, table)

    def _fallback_sql_generation(
        self, question: str, attributes: dict, table: str
    ) -> str:
        """Fallback SQL generation when Azure LLM is not available."""
        # Simple fallback that generates basic SQL based on attributes
        conditions = []

        if "price" in attributes and attributes["price"]:
            try:
                price_val = float(
                    attributes["price"].replace("€", "").replace("euro", "").strip()
                )
                conditions.append(f"price <= {price_val}")
            except (ValueError, AttributeError):
                pass

        if "brand" in attributes and attributes["brand"]:
            brand_val = attributes["brand"].strip()
            if brand_val and brand_val.lower() not in [
                "geen voorkeur",
                "maakt niet uit",
            ]:
                conditions.append(f"brand = '{brand_val}'")

        if "technology" in attributes and attributes["technology"]:
            tech_val = attributes["technology"].strip()
            if tech_val and tech_val.lower() not in ["geen voorkeur", "maakt niet uit"]:
                conditions.append(f"LOWER(technology) = '{tech_val.lower()}'")

        # Category-specific conditions
        if table == "laptops":
            if "screen_size" in attributes and attributes["screen_size"]:
                screen_val = attributes["screen_size"].strip()
                if screen_val and screen_val.lower() not in [
                    "geen voorkeur",
                    "maakt niet uit",
                ]:
                    conditions.append(f"screen_size_inches >= {screen_val}")
            if "ram" in attributes and attributes["ram"]:
                ram_val = attributes["ram"].strip()
                if ram_val and ram_val.lower() not in [
                    "geen voorkeur",
                    "maakt niet uit",
                ]:
                    conditions.append(f"ram_gb >= {ram_val}")
        elif table == "smartphones":
            if "storage" in attributes and attributes["storage"]:
                storage_val = attributes["storage"].strip()
                if storage_val and storage_val.lower() not in [
                    "geen voorkeur",
                    "maakt niet uit",
                ]:
                    conditions.append(f"storage_gb >= {storage_val}")

        where_clause = " AND ".join(conditions) if conditions else ""
        if where_clause:
            return f"SELECT * FROM {table} WHERE {where_clause} LIMIT 10"
        else:
            return f"SELECT * FROM {table} LIMIT 10"
