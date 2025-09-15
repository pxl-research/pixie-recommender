from __future__ import annotations

from typing import Tuple

from ..utils.config import get_config
from .azure_refinement_llm import AzureRefinementLLM
from .azure_relevance_llm import AzureRelevanceLLM
from .azure_sql_llm import AzureSQLLLM


def create_azure_llm_set() -> Tuple[AzureRelevanceLLM, AzureSQLLLM, AzureRefinementLLM]:
    """Create Azure LLM instances using centralized configuration.

    Configuration is loaded from environment variables at startup.
    """
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
