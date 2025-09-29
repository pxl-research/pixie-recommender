from __future__ import annotations

from typing import Optional

from ..database.connection import get_db_session
from ..database.repositories.flexible_repositories import get_dynamic_repository
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
        default_table: str = "products",  # Use generic products table
    ):
        super().__init__(api_version, api_endpoint, api_key, model_version, temperature)
        self.model_name = model_name
        self.default_table = default_table

        # Simple context tracking for progressive building
        self.context = {}

    def generate_sql(
        self,
        question: Optional[str],
        attributes: Optional[dict] = None,
        table_name: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> str:
        q = (question or "").strip()
        attrs = attributes or {}
        table = table_name or self.default_table

        # Merge context if provided
        if context:
            self.context.update(context)
            if "category" in context:
                table = context["category"]
            if "attributes" in context:
                attrs.update(context["attributes"])

        if not self.model:
            raise ValueError(
                "Azure LLM model is required for SQL generation. "
                "Please check your configuration."
            )

        try:
            # Get actual product type from database dynamically
            product_type = self._get_product_type_from_database(table)

            # Generate schema information dynamically
            schema_manager = get_schema_manager()
            schema_info = schema_manager.generate_table_description("products")

            # Get available attributes for this product type
            available_attributes = self._get_available_attributes(product_type)

            # Build dynamic prompt based on actual schema and attributes
            prompt = self._build_dynamic_prompt(
                q, attrs, product_type, schema_info, available_attributes
            )

            response = self.model.invoke(prompt)

            if hasattr(response, "content"):
                sql = response.content.strip()
                # Remove any markdown formatting if present
                if sql.startswith("```sql"):
                    sql = sql.replace("```sql", "").replace("```", "").strip()
                return sql

            raise ValueError("Invalid response format from Azure model")

        except Exception as e:
            raise RuntimeError(f"Failed to generate SQL query: {e}")

    def _get_product_type_from_database(self, category: str) -> str:
        """Get the actual product type name from database."""
        try:
            with get_db_session() as session:
                product_types_repo = get_dynamic_repository(session, "product_types")

                # Try to find exact match first
                product_types = product_types_repo.find_by_column("name", category)
                if product_types:
                    return product_types[0]["name"]

                # Try to find by display_name
                product_types = product_types_repo.find_by_column(
                    "display_name", category
                )
                if product_types:
                    return product_types[0]["name"]

                # If no match, return the category as-is and let LLM handle it
                return category
        except Exception:
            # If database lookup fails, return category as-is
            return category

    def _get_available_attributes(self, product_type: str) -> list:
        """Get available attributes for a product type from database."""
        try:
            with get_db_session() as session:
                # Get product type ID
                product_types_repo = get_dynamic_repository(session, "product_types")
                product_types = product_types_repo.find_by_column("name", product_type)

                if not product_types:
                    return []

                product_type_id = product_types[0]["id"]

                # Get attributes for this product type
                attr_repo = get_dynamic_repository(session, "attribute_definitions")
                attributes = attr_repo.filter_by_attributes(
                    {"product_type_id": product_type_id}
                )

                return [attr["name"] for attr in attributes]
        except Exception:
            return []

    def _build_dynamic_prompt(
        self,
        question: str,
        attributes: dict,
        product_type: str,
        schema_info: str,
        available_attributes: list,
    ) -> str:
        """Build a dynamic prompt based on actual database schema."""
        # Build attribute context
        attr_context = ""
        if available_attributes:
            attr_context = (
                f"\nAvailable attributes for {product_type}: "
                f"{', '.join(available_attributes)}"
            )

        # Build user attributes context
        user_attrs = ""
        if attributes:
            valid_attrs = {
                k: v
                for k, v in attributes.items()
                if v
                and str(v).lower()
                not in ["weet ik niet", "geen idee", "maakt niet uit"]
            }
            if valid_attrs:
                user_attrs = f"\nUser specified attributes: {valid_attrs}"

        prompt = f"""Generate a single SQL query (no explanation) that answers the user's request.

{schema_info}

DATABASE STRUCTURE:
- Use products table with JOIN to product_types table
- Product type to search: '{product_type}'
- Use product_attribute_values table for specific attributes
- Join with attribute_definitions to match attribute names{attr_context}

User Question: {question}{user_attrs}

RULES:
1. Always JOIN products with product_types: 
   'FROM products p JOIN product_types pt ON p.product_type_id = pt.id'
2. Filter by product type: 'WHERE pt.name = \'{product_type}\''
3. Use 'p.price_cents' for price (convert euros to cents: €100 = 10000 cents)
4. For attributes, use EXISTS with product_attribute_values and attribute_definitions
5. Ignore vague responses completely
6. Return only the SQL query, no explanations

Generate the SQL query:"""

        return prompt

    def collect_attribute(self, name: str, value: str) -> None:
        """Simple method to collect an attribute for progressive building."""
        if "attributes" not in self.context:
            self.context["attributes"] = {}
        self.context["attributes"][name] = value

    def set_category(self, category: str) -> None:
        """Set the detected category from azure_relevance_llm."""
        self.context["category"] = category

    def reset_context(self) -> None:
        """Reset context for new conversation."""
        self.context = {}
