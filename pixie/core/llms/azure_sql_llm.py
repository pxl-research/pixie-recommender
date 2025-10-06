from __future__ import annotations

from typing import Optional

from .azure_openai_llm import AzureOpenAILLM

SCHEMA_DESCRIPTION = """
Table: products (id, name, description, price_cents, currency, product_type_id, created_at, updated_at)
Table: product_types (id, name, display_name, description, is_active)
Table: attribute_definitions (id, name, display_name, canonical_name, data_type, is_required, product_type_id)
Table: product_attribute_values (id, product_id, attribute_definition_id, value)
""".strip()

# TODO: replace with metadata obtained from the external dataset service.
DEFAULT_ATTRIBUTES = {
    "printers": ["budget", "brand", "technology"],
    "laptops": ["budget", "brand", "screen_size"],
    "smartphones": ["budget", "brand", "screen_size"],
    "computers": ["budget", "brand", "processor"],
}


class AzureSQLLLM(AzureOpenAILLM):
    def __init__(
        self,
        api_version: str,
        api_endpoint: str,
        api_key: str,
        model_version: str,
        temperature: float = 0.01,
        model_name: str = "azure-sql-llm",
        default_table: str = "products",
    ) -> None:
        super().__init__(api_version, api_endpoint, api_key, model_version, temperature)
        self.model_name = model_name
        self.default_table = default_table
        self.context: dict = {}

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

        if context:
            self.context.update(context)
            if "category" in context:
                table = context["category"]
            if "attributes" in context:
                attrs.update(context["attributes"])

        if not self.model:
            raise ValueError("Azure LLM model is required for SQL generation. Check configuration.")

        product_type = self._resolve_product_type(table)
        available_attributes = DEFAULT_ATTRIBUTES.get(product_type, [])

        prompt = self._build_prompt(q, attrs, product_type, available_attributes)
        response = self.model.invoke(prompt)
        if hasattr(response, "content"):
            sql = response.content.strip()
            if sql.startswith("```sql"):
                sql = sql.replace("```sql", "").replace("```", "").strip()
            return sql
        raise ValueError("Invalid response format from Azure model")

    def _resolve_product_type(self, category: str) -> str:
        if category in DEFAULT_ATTRIBUTES:
            return category
        candidate = category.rstrip("s")
        if candidate in DEFAULT_ATTRIBUTES:
            return candidate
        return category

    def _build_prompt(
        self,
        question: str,
        attributes: dict,
        product_type: str,
        available_attributes: list,
    ) -> str:
        attr_context = ""
        if available_attributes:
            attr_context = f"\nBeschikbare attributen: {', '.join(available_attributes)}"
        user_attrs = ""
        if attributes:
            filtered = {
                k: v
                for k, v in attributes.items()
                if v and str(v).lower() not in {"weet ik niet", "geen idee", "maakt niet uit"}
            }
            if filtered:
                user_attrs = f"\nGebruiker gaf op: {filtered}"
        return f"""Generate a SQL query without explanation.

{SCHEMA_DESCRIPTION}

Focus on product type '{product_type}'.
Gebruik products JOIN product_types en product_attribute_values waar nodig.{attr_context}

Gebruikersvraag: {question}{user_attrs}

Alleen de SQL-query retour."""

    def collect_attribute(self, name: str, value: str) -> None:
        self.context.setdefault("attributes", {})[name] = value

    def set_category(self, category: str) -> None:
        self.context["category"] = category

    def reset_context(self) -> None:
        self.context = {}
