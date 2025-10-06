from __future__ import annotations

from typing import Optional

from ..utils.attribute_catalog import (
    get_attribute_definitions,
    get_product_type,
    get_schema_description,
    list_attribute_names,
)
from .azure_openai_llm import AzureOpenAILLM


class AzureSQLLLM(AzureOpenAILLM):

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
            product_type = self._resolve_product_type(table)

            schema_info = get_schema_description()

            available_attributes = list_attribute_names(product_type)

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

    def _resolve_product_type(self, category: str) -> str:
        product_type = get_product_type(category)
        if product_type:
            return product_type.name

        for candidate in [category.rstrip("s"), category.lower()]:
            product_type = get_product_type(candidate)
            if product_type:
                return product_type.name

        return category

    def _build_dynamic_prompt(
        self,
        question: str,
        attributes: dict,
        product_type: str,
        schema_info: str,
        available_attributes: list,
    ) -> str:
        attr_context = ""
        if available_attributes:
            attr_context = (
                f"\nAvailable attributes for {product_type}: "
                f"{', '.join(available_attributes)}"
            )

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
