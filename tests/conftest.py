import os

import pytest

from pixie.core.llms import azure_llm_set


class MockRelevance:
    def is_relevant(self, text: str) -> bool:
        return "printer" in (text or "").lower()


class MockSQL:
    def generate_sql(self, question: str, attributes: dict | None = None) -> str:
        return "SELECT * FROM printers;"


class MockRefinement:
    def generate_refinement_question(self, context: dict) -> "str | None":
        if not context:
            return "Wat is je budget?"
        if "budget" in context and "brand" not in context:
            return "Heb je een voorkeur voor een merk?"
        if "budget" in context and "brand" in context and "technology" not in context:
            return "Welke technologie heeft je voorkeur (inkjet/laser)?"
        return None


@pytest.fixture
def mock_llm_set():
    # Use Azure LLMs if environment variables are set, otherwise fall back to mocks
    if (
        os.getenv("AZURE_OPENAI_ENDPOINT") != "https://example.openai.azure.com/"
        and os.getenv("AZURE_OPENAI_KEY") != "dummy-key-for-development"
        and os.getenv("AZURE_OPENAI_API_VERSION")
        and os.getenv("AZURE_OPENAI_MODEL")
    ):
        return azure_llm_set.create_azure_llm_set()
    else:
        return MockRelevance(), MockSQL(), MockRefinement()
