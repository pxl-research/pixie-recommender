from __future__ import annotations

from typing import Any, Tuple

from ..utils.config import get_config
from .azure_refinement_llm import AzureRefinementLLM
from .azure_relevance_llm import AzureRelevanceLLM
from .azure_sql_llm import AzureSQLLLM


def create_azure_llm_set() -> Tuple[Any, Any, Any]:
    config = get_config().azure
    placeholders = {
        "https://example.openai.azure.com/",
        "https://your-resource.openai.azure.com/",
        "dummy-key-for-development",
        "your-api-key-here",
    }
    if config.api_endpoint in placeholders or config.api_key in placeholders:
        raise ValueError("Azure OpenAI configuration is not set")
    relevance = AzureRelevanceLLM(
        config.api_version,
        config.api_endpoint,
        config.api_key,
        config.model_version,
    )
    sql = AzureSQLLLM(
        config.api_version,
        config.api_endpoint,
        config.api_key,
        config.model_version,
    )
    refinement = AzureRefinementLLM(
        config.api_version,
        config.api_endpoint,
        config.api_key,
        config.model_version,
    )
    try:
        relevance.is_relevant("test query")
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError("Azure LLM validation failed") from exc
    return relevance, sql, refinement
