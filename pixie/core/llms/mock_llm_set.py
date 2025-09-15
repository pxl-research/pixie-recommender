from __future__ import annotations

from typing import Any, Tuple


class MockRelevance:
    def is_relevant(self, text: str) -> bool:
        return True


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


def create_mock_llm_set() -> Tuple[Any, Any, Any]:
    """Create mock LLM instances for testing."""
    return MockRelevance(), MockSQL(), MockRefinement()
