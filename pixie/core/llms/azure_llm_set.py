from __future__ import annotations

import os
from typing import Any, Tuple

from ..utils.config import get_config
from .azure_refinement_llm import AzureRefinementLLM
from .azure_relevance_llm import AzureRelevanceLLM
from .azure_sql_llm import AzureSQLLLM


def create_azure_llm_set() -> Tuple[Any, Any, Any]:
    """Create Azure LLM instances using centralized configuration.

    Falls back to mock LLMs if Azure deployment is not available.
    """
    # Check if we should force mock usage
    if os.getenv("PIXIE_FORCE_MOCKS", "0") == "1":
        from .mock_llm_set import create_mock_llm_set

        return create_mock_llm_set()

    azure_config = get_config().azure

    # Check if endpoint and key are properly configured
    if (
        azure_config.api_endpoint == "https://example.openai.azure.com/"
        or azure_config.api_key == "dummy-key-for-development"
    ):
        from .mock_llm_set import create_mock_llm_set

        return create_mock_llm_set()

    try:
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

        # Test if the models work by making a simple call
        try:
            relevance.is_relevant("test")
        except Exception:
            # If the test call fails, fall back to mocks
            from .mock_llm_set import create_mock_llm_set

            return create_mock_llm_set()

        return relevance, sql, refinement

    except Exception:
        # If any Azure LLM creation fails, fall back to mocks
        from .mock_llm_set import create_mock_llm_set

        return create_mock_llm_set()
