from __future__ import annotations

from typing import Optional

from pixie.core.abstractclasses.llm import LLM


class MockRelevanceLLM(LLM):
    """Minimal mock that returns True iff the question contains 'printer' or 'printers'."""

    def __init__(self, model_name: str = "mock-relevance-llm"):
        super().__init__(model_name)

    def is_relevant(self, question: Optional[str]) -> bool:
        text = (question or "").lower()
        return "printer" in text or "printers" in text
