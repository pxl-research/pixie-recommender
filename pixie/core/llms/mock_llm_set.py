from __future__ import annotations

from typing import Any, Tuple


class MockRelevance:
    def is_relevant(self, text: str) -> bool:
        # Check for product-related keywords
        product_keywords = [
            "printer",
            "laptop",
            "computer",
            "phone",
            "tablet",
            "monitor",
            "keyboard",
            "mouse",
            "headphones",
            "speaker",
            "camera",
            "tv",
            "koop",
            "prijs",
            "budget",
            "merk",
            "brand",
            "laser",
            "inkjet",
        ]
        text_lower = text.lower()

        # Exclude personal/family questions
        personal_keywords = ["mama", "papa", "moeder", "vader", "familie", "vriend"]
        if any(personal in text_lower for personal in personal_keywords):
            return False

        return any(keyword in text_lower for keyword in product_keywords)


class MockSQL:
    def generate_sql(self, question: str, attributes: dict | None = None) -> str:
        return "SELECT * FROM printers;"


class MockRefinement:
    def generate_refinement_question(self, context: dict) -> "str | None":
        if not context:
            return "Wat is je budget?"
        if "budget" not in context:
            return "Wat is je budget?"
        if "budget" in context and "brand" not in context:
            return "Heb je een voorkeur voor een merk?"
        if "budget" in context and "brand" in context and "technology" not in context:
            return "Welke technologie heeft je voorkeur (inkjet/laser)?"
        return None


def create_mock_llm_set() -> Tuple[Any, Any, Any]:
    """Create mock LLM instances for testing."""
    return MockRelevance(), MockSQL(), MockRefinement()
