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
            # Map table parameter to actual product type name in database
            category_to_product_type = {
                "printers": "printers",
                "laptops": "laptop",  # category "laptops" maps to product_type "laptop"
                "computers": "computer",
                "smartphones": "smartphone",
            }
            product_type = category_to_product_type.get(table, table)

            # Generate schema information dynamically
            schema_manager = get_schema_manager()
            schema_info = schema_manager.generate_table_description("products")

            # Build prompt with specific instructions for the normalized database structure
            prompt = (
                f"Generate a single SQL query (no explanation) that answers the user's request.\n\n"
                f"{schema_info}\n\n"
                f"DATABASE STRUCTURE:\n"
                f"- Use products table with JOIN to product_types table\n"
                f"- Product type to search: '{product_type}'\n"
                f"- Use product_attribute_values table for brand, technology, "
                f"and other attributes\n\n"
                f"User Question: {q}\n"
                f"User Attributes: {attrs}\n\n"
                "IMPORTANT RULES:\n"
                "1. Always use JOIN: 'FROM products p JOIN product_types pt "
                "ON p.product_type_id = pt.id'\n"
                "2. Filter by product type: 'WHERE pt.name = '{product_type}'\n"
                "3. Use 'p.price_cents' for price comparisons (price in cents)\n"
                "4. For budget constraints, use <= for maximum budget\n"
                "5. For brand/technology/attributes, use EXISTS with product_attribute_values\n"
                '6. IGNORE vague responses like "weet ik niet", "geen idee", "maakt niet uit"\n\n'
                "EXAMPLES:\n"
                f"- Basic query: SELECT p.* FROM products p JOIN product_types pt "
                f"ON p.product_type_id = pt.id WHERE pt.name = '{product_type}'\n"
                f"- With budget: ... AND p.price_cents <= 20000\n"
                "- With brand: ... AND EXISTS (SELECT 1 FROM product_attribute_values pav "
                "JOIN attribute_definitions ad ON pav.attribute_definition_id = ad.id "
                "WHERE pav.product_id = p.id AND ad.name = 'brand' AND pav.value = 'HP')\n"
                '- Ignore "weet ik niet" responses completely\n\n'
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
        # Map category table names to actual product type names in database
        category_to_product_type = {
            "printers": "printers",
            "laptops": "laptop",  # category "laptops" maps to product_type "laptop"
            "computers": "computer",
            "smartphones": "smartphone",
        }

        product_type = category_to_product_type.get(table, table)

        # Generate conditions for filtering
        conditions = []

        if "price" in attributes and attributes["price"]:
            try:
                price_val = float(
                    attributes["price"].replace("€", "").replace("euro", "").strip()
                )
                price_cents = int(price_val * 100)  # Convert euros to cents
                conditions.append(f"p.price_cents <= {price_cents}")
            except (ValueError, AttributeError):
                pass

        if "budget" in attributes and attributes["budget"]:
            try:
                # Handle budget strings like "200" or "200 euro" or "maximaal 150"
                budget_str = (
                    attributes["budget"]
                    .replace("€", "")
                    .replace("euro", "")
                    .replace("maximaal", "")
                    .strip()
                )
                vague_responses = ["geen voorkeur", "maakt niet uit", "weet ik niet"]
                if budget_str and budget_str.lower() not in vague_responses:
                    budget_val = float(budget_str)
                    budget_cents = int(budget_val * 100)  # Convert euros to cents
                    conditions.append(f"p.price_cents <= {budget_cents}")
            except (ValueError, AttributeError):
                pass

        # Handle brand filtering using product_attribute_values
        if "brand" in attributes and attributes["brand"]:
            brand_val = attributes["brand"].strip()
            if brand_val and brand_val.lower() not in [
                "geen voorkeur",
                "maakt niet uit",
                "weet ik niet",
            ]:
                conditions.append(
                    f"""EXISTS (
                    SELECT 1 FROM product_attribute_values pav 
                    JOIN attribute_definitions ad ON pav.attribute_definition_id = ad.id 
                    WHERE pav.product_id = p.id AND ad.name = 'brand' AND pav.value = '{brand_val}'
                )"""
                )

        # Handle technology filtering using product_attribute_values
        if "technology" in attributes and attributes["technology"]:
            tech_val = attributes["technology"].strip()
            if tech_val and tech_val.lower() not in [
                "geen voorkeur",
                "maakt niet uit",
                "weet ik niet",
            ]:
                conditions.append(
                    f"""EXISTS (
                    SELECT 1 FROM product_attribute_values pav 
                    JOIN attribute_definitions ad ON pav.attribute_definition_id = ad.id 
                    WHERE pav.product_id = p.id AND ad.name = 'technology' 
                    AND LOWER(pav.value) = '{tech_val.lower()}'
                )"""
                )

        # Handle other category-specific attributes using product_attribute_values
        for attr_name, attr_value in attributes.items():
            if (
                attr_name not in ["budget", "price", "brand", "technology"]
                and attr_value
            ):
                attr_val = str(attr_value).strip()
                if attr_val and attr_val.lower() not in [
                    "geen voorkeur",
                    "maakt niet uit",
                    "weet ik niet",
                ]:
                    conditions.append(
                        f"""EXISTS (
                        SELECT 1 FROM product_attribute_values pav 
                        JOIN attribute_definitions ad ON pav.attribute_definition_id = ad.id 
                        WHERE pav.product_id = p.id AND ad.name = '{attr_name}' 
                        AND pav.value = '{attr_val}'
                    )"""
                    )

        # Build the final SQL query using products table with JOIN
        base_sql = f"""
        SELECT p.* FROM products p 
        JOIN product_types pt ON p.product_type_id = pt.id 
        WHERE pt.name = '{product_type}'
        """

        if conditions:
            where_clause = " AND ".join(conditions)
            return f"{base_sql} AND ({where_clause}) LIMIT 10"
        else:
            return f"{base_sql} LIMIT 10"
