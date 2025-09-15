from __future__ import annotations

import os
from typing import Any, Tuple

from ..utils.config import get_config
from .azure_refinement_llm import AzureRefinementLLM
from .azure_relevance_llm import AzureRelevanceLLM
from .azure_sql_llm import AzureSQLLLM


class MockRelevance:
    def is_relevant(self, text: str) -> bool:
        return "printer" in (text or "").lower()


class MockSQL:
    def generate_sql(self, question: str, attributes: dict | None = None) -> str:
        return "SELECT * FROM printers;"


class MockRefinement:
    def generate_refinement_question(self, context: dict) -> "str | None":
        if not context:
            return "Wat is je budget?"
        if "budget" in context and "brand" not in context:
            return "Heb je een voorkeur voor een merk?"
        if "budget" in context and "brand" in context and "technology" not in context:
            return "Welke technologie heeft je voorkeur (inkjet/laser)?"
        return None


def create_azure_llm_set() -> Tuple[Any, Any, Any]:
    """Create Azure LLM instances using centralized configuration.

    Falls back to mock LLMs if Azure environment variables are not properly configured.
    """
    # Check if Azure environment variables are set (allowing defaults)
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    api_key = os.getenv("AZURE_OPENAI_KEY", "dummy-key-for-development")
    
    # Use Azure if endpoint and key are not defaults
    if (
        endpoint != "https://example.openai.azure.com/"
        and api_key != "dummy-key-for-development"
    ):
        azure_config = get_config().azure

        relevance = AzureRelevanceLLM(
            azure_config.api_version,
            azure_config.api_endpoint,
            azure_config.api_key,
            azure_config.model_version,
        )
        sql = AzureSQLLLM(
            azure_config.api_version,
            azure_config.api_endpoint,
            azure_config.api_key,
            azure_config.model_version,
        )
        refinement = AzureRefinementLLM(
            azure_config.api_version,
            azure_config.api_endpoint,
            azure_config.api_key,
            azure_config.model_version,
        )

        return relevance, sql, refinement
    else:
        # Fallback to mocks
        return MockRelevance(), MockSQL(), MockRefinement()
