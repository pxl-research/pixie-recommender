from __future__ import annotations

from typing import Tuple, Any
import os


def create_mock_llm_set() -> Tuple[Any, Any, Any]:
    """Create a trio of mock LLMs (relevance, sql, refinement).

    If Azure environment variables are present, attempt to create and return
    Azure LLMs instead. This keeps local tests working by default while
    enabling integration tests to exercise real Azure LLMs when configured.
    """
    # Strict-Azure mode: require all Azure env vars and return Azure LLMs.
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")
    model = os.getenv("AZURE_OPENAI_MODEL")

    missing = [
        n
        for n, v in {
            "AZURE_OPENAI_API_VERSION": api_version,
            "AZURE_OPENAI_ENDPOINT": api_endpoint,
            "AZURE_OPENAI_KEY": api_key,
            "AZURE_OPENAI_MODEL": model,
        }.items()
        if not v
    ]
    if missing:
        raise EnvironmentError(
            "Azure OpenAI environment variables missing: "
            f"{missing}. Set these variables or run tests with a mocked LLM factory."
        )

    try:
        from .azure_llm_set import create_azure_llm_set

        relevance, sql, refinement = create_azure_llm_set()
        return relevance, sql, refinement
    except Exception as e:  # propagate initialization issues clearly
        raise RuntimeError(
            "Failed to initialize Azure LLMs: "
            f"{e}. Ensure Azure credentials and SDKs are configured."
        )
