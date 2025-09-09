from __future__ import annotations

from typing import Optional

from pixie.core.abstractclasses.llm import LLM


class MockRefinementLLM(LLM):
    """Fixed refinement question sequence: budget -> brand -> technology."""

    def __init__(self, model_name: str = "mock-refinement-llm"):
        super().__init__(model_name)

    def generate_refinement_question(
        self, context: Optional[dict] = None
    ) -> Optional[str]:
        ctx = context or {}
        if "budget" not in ctx:
            return "Wat is je budget?"
        if "brand" not in ctx:
            return "Heb je een voorkeur voor een merk?"
        if "technology" not in ctx:
            return "Welke technologie heeft je voorkeur (inkjet/laser)?"
        return None
