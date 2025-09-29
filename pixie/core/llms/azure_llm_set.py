from __future__ import annotations

from typing import Any, Tuple

from ..utils.config import get_config
from .azure_refinement_llm import AzureRefinementLLM
from .azure_relevance_llm import AzureRelevanceLLM
from .azure_sql_llm import AzureSQLLLM


def create_azure_llm_set() -> Tuple[Any, Any, Any]:
    """Create Azure LLM instances using centralized configuration.

    Requires proper Azure OpenAI configuration.
    """
    azure_config = get_config().azure

    # Validate Azure configuration
    if (
        azure_config.api_endpoint == "https://example.openai.azure.com/"
        or azure_config.api_endpoint == "https://your-resource.openai.azure.com/"
        or azure_config.api_key == "dummy-key-for-development"
        or azure_config.api_key == "your-api-key-here"
    ):
        raise ValueError(
            "Azure OpenAI configuration is not properly set. "
            "Please update AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY in your environment."
        )

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
            relevance.is_relevant("test query")
        except Exception as e:
            raise RuntimeError(
                f"Azure LLM validation failed. Please check your Azure OpenAI configuration: {e}"
            ) from e

        return relevance, sql, refinement

    except Exception as e:
        raise RuntimeError(f"Failed to create Azure LLM instances: {e}") from e
