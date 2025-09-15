from __future__ import annotations

from typing import Any, Tuple

from ..utils.config import get_config
from .azure_refinement_llm import AzureRefinementLLM
from .azure_relevance_llm import AzureRelevanceLLM
from .azure_sql_llm import AzureSQLLLM
from .mock_llm_set import MockRefinement, MockRelevance, MockSQL


def create_azure_llm_set() -> Tuple[Any, Any, Any]:
    """Create Azure LLM instances using centralized configuration.

    Falls back to mock LLMs if Azure environment variables are not properly configured.
    """
    azure_config = get_config().azure

    # Use Azure if endpoint and key are not defaults
    if (
        azure_config.api_endpoint != "https://example.openai.azure.com/"
        and azure_config.api_key != "dummy-key-for-development"
    ):
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
