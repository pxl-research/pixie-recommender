from __future__ import annotations

import os
from typing import Tuple

from pixie.core.azure_relevance_llm import AzureRelevanceLLM
from pixie.core.azure_sql_llm import AzureSQLLLM
from pixie.core.azure_refinement_llm import AzureRefinementLLM


def create_azure_llm_set() -> Tuple[AzureRelevanceLLM, AzureSQLLLM, AzureRefinementLLM]:
    """Create Azure LLM instances reading configuration from environment variables.

    Required environment variables:
    - AZURE_OPENAI_API_VERSION
    - AZURE_OPENAI_ENDPOINT
    - AZURE_OPENAI_KEY
    - AZURE_OPENAI_MODEL (deployment name)
    """
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")
    model_version = os.getenv("AZURE_OPENAI_MODEL")

    missing = [n for n, v in {
        "AZURE_OPENAI_API_VERSION": api_version,
        "AZURE_OPENAI_ENDPOINT": api_endpoint,
        "AZURE_OPENAI_KEY": api_key,
        "AZURE_OPENAI_MODEL": model_version,
    }.items() if not v]
    if missing:
        raise EnvironmentError(f"Missing required Azure OpenAI env vars: {missing}")

    relevance = AzureRelevanceLLM(api_version, api_endpoint, api_key, model_version)
    sql = AzureSQLLLM(api_version, api_endpoint, api_key, model_version)
    refinement = AzureRefinementLLM(api_version, api_endpoint, api_key, model_version)

    return relevance, sql, refinement
