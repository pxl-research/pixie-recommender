from __future__ import annotations

from typing import Optional

from .azure_openai_llm import AzureOpenAILLM


class AzureSQLLLM(AzureOpenAILLM):
    """Azure-based SQL generator for printer queries.

    The generate_sql method attempts to use the Azure model with a focused
    prompt to produce a SQL query. On failure it falls back to a safe default
    query matching previous mock behaviour.
    """

    def __init__(
        self,
        api_version: str,
        api_endpoint: str,
        api_key: str,
        model_version: str,
        temperature: float = 0.01,
        model_name: str = "azure-sql-llm",
    ):
        super().__init__(api_version, api_endpoint, api_key, model_version, temperature)
        self.model_name = model_name

    def generate_sql(
        self, question: Optional[str], attributes: Optional[dict] = None
    ) -> str:
        q = (question or "").strip()
        attrs = attributes or {}

        if not self.model:
            raise ValueError("Azure model is not available")

        prompt = (
            "Generate a single concise SQL query (no explanation) that "
            "answers the user's request. Use the table `printers` and "
            "available attributes.\n\n"
            f"Question: {q}\nAttributes: {attrs}"
        )

        response = self.model.invoke(prompt)

        if hasattr(response, "content"):
            return response.content.strip()

        raise ValueError("Invalid response format from Azure model")
