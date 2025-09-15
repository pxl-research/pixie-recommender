import pytest


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
    return MockRelevance(), MockSQL(), MockRefinement()
