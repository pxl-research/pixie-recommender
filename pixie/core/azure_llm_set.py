from __future__ import annotations

from typing import Tuple

from pixie.core.llms.azure_refinement_llm import AzureRefinementLLM
from pixie.core.llms.azure_relevance_llm import AzureRelevanceLLM
from pixie.core.llms.azure_sql_llm import AzureSQLLLM
from pixie.core.utils.config import get_config


def create_azure_llm_set() -> Tuple[AzureRelevanceLLM, AzureSQLLLM, AzureRefinementLLM]:
    """Create Azure LLM instances reading configuration from environment variables.

    Required environment variables:
    - AZURE_OPENAI_API_VERSION
    - AZURE_OPENAI_ENDPOINT
    - AZURE_OPENAI_KEY
    - AZURE_OPENAI_MODEL (deployment name)
    """
    config = get_config()
    api_version = config.azure.api_version
    api_endpoint = config.azure.api_endpoint
    api_key = config.azure.api_key
    model_version = config.azure.model_version

    relevance = AzureRelevanceLLM(api_version, api_endpoint, api_key, model_version)
    sql = AzureSQLLLM(api_version, api_endpoint, api_key, model_version)
    refinement = AzureRefinementLLM(api_version, api_endpoint, api_key, model_version)

    return relevance, sql, refinement
