"""Factory helpers that turn environment variables into Azure LLM instances."""

from __future__ import annotations

import os
from typing import Any, Optional, Tuple

from .azure_refinement_llm import AzureRefinementLLM
from .azure_relevance_llm import AzureRelevanceLLM
from .azure_sql_llm import AzureSQLLLM

PLACEHOLDERS = {
    "https://example.openai.azure.com/",
    "https://your-resource.openai.azure.com/",
    "dummy-key-for-development",
    "your-api-key-here",
}


def _require_env(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    if not value:
        raise ValueError(f"Environment variable {name} is required")
    return value


def _load_azure_config() -> Tuple[str, str, str, str]:
    api_version = _require_env("AZURE_OPENAI_API_VERSION", "2024-02-01")
    endpoint = _require_env("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    api_key = _require_env("AZURE_OPENAI_KEY", "dummy-key-for-development")
    model = _require_env("AZURE_OPENAI_MODEL", "gpt-4")
    if endpoint in PLACEHOLDERS or api_key in PLACEHOLDERS:
        raise ValueError("Azure OpenAI configuration is not set")
    return api_version, endpoint, api_key, model


def create_azure_llm_set(categories: Optional[list[str]] = None) -> Tuple[Any, Any]:
    api_version, endpoint, api_key, model = _load_azure_config()
    if not categories:
        raise ValueError("Category metadata is required to initialise the Azure relevance model")
    relevance = AzureRelevanceLLM(
        api_version, endpoint, api_key, model, categories=categories
    )
    sql = AzureSQLLLM(api_version, endpoint, api_key, model)
    try:
        relevance.is_relevant("test query")
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError("Azure LLM validation failed") from exc
    return relevance, sql


def create_azure_refinement_llm() -> AzureRefinementLLM:
    api_version, endpoint, api_key, model = _load_azure_config()
    return AzureRefinementLLM(api_version, endpoint, api_key, model)
