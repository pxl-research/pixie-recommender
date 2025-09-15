from __future__ import annotations

from typing import Optional

from .azure_openai_llm import AzureOpenAILLM


class AzureRefinementLLM(AzureOpenAILLM):
    """Azure-based refinement question generator.

    Attempts to derive the next clarification question from context. Falls
    back to the same static sequence used by the mock when the API is
    unavailable.
    """

    def __init__(
        self,
        api_version: str,
        api_endpoint: str,
        api_key: str,
        model_version: str,
        temperature: float = 0.01,
        model_name: str = "azure-refinement-llm",
    ):
        super().__init__(api_version, api_endpoint, api_key, model_version, temperature)
        self.model_name = model_name

    def generate_refinement_question(
        self, context: Optional[dict] = None
    ) -> Optional[str]:
        ctx = context or {}

        if not self.model:
            raise ValueError("Azure model is not available")

        prompt = (
            "Given the conversation context, determine which attribute to ask about next. "
            "Follow this exact sequence: 1) budget, 2) brand/merk, 3) technology (inkjet/laser). "
            "Return ONLY the appropriate question in Dutch, "
            "or empty string if all attributes are collected.\n\n"
            "Rules:\n"
            "- If 'budget' is missing: ask 'Wat is je budget?'\n"
            "- If 'budget' exists but 'brand' is missing: "
            "ask 'Heb je een voorkeur voor een merk?'\n"
            "- If 'budget' and 'brand' exist but 'technology' is missing: "
            "ask 'Welke technologie heeft je voorkeur (inkjet/laser)?'\n"
            "- If all three exist: return empty string\n\n"
            f"Context: {ctx}"
        )

        response = self.model.invoke(prompt)

        if hasattr(response, "content"):
            answer = response.content.strip()
            return answer if answer else None

        raise ValueError("Invalid response format from Azure model")
