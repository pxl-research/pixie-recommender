import os
from typing import Any, Tuple

import pytest

from pixie.core.llms import azure_llm_set


@pytest.fixture(scope="session")
def azure_llm_set_fixture() -> Tuple[Any, Any, Any]:
    """
    Fixture that provides Azure LLM instances for testing.

    Requires proper Azure OpenAI configuration to run tests.
    """
    # Check if Azure is properly configured
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_key = os.getenv("AZURE_OPENAI_KEY", "")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "")
    azure_model = os.getenv("AZURE_OPENAI_MODEL", "")

    azure_configured = (
        azure_endpoint
        and azure_endpoint
        not in [
            "https://example.openai.azure.com/",
            "https://your-resource.openai.azure.com/",
        ]
        and azure_key
        and azure_key not in ["dummy-key-for-development", "your-api-key-here"]
        and azure_api_version
        and azure_model
    )

    if not azure_configured:
        pytest.skip(
            "Azure OpenAI configuration is required for tests. "
            "Please set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, "
            "AZURE_OPENAI_API_VERSION, and AZURE_OPENAI_MODEL environment variables."
        )

    try:
        # Create real Azure LLMs
        real_llms = azure_llm_set.create_azure_llm_set()
        print(f"✅ Using Azure LLMs for testing (endpoint: {azure_endpoint})")
        return real_llms
    except Exception as e:
        pytest.skip(f"Failed to create Azure LLMs: {e}")


# Legacy compatibility - can be removed once all tests are updated
@pytest.fixture(scope="session")
def llm_set(azure_llm_set_fixture):
    """Legacy fixture name for backward compatibility."""
    return azure_llm_set_fixture
