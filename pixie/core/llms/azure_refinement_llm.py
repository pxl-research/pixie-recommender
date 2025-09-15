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
            "Given the conversation context as JSON, return a single short "
            "follow-up question aimed at clarifying the user's needs about "
            "printers, or return an empty string if no clarification is "
            "required. Do not add any explanation.\n\n"
            f"Context: {ctx}"
        )

        response = self.model.invoke(prompt)

        if hasattr(response, "content"):
            answer = response.content.strip()
            return answer if answer else None

        raise ValueError("Invalid response format from Azure model")
