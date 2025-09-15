from __future__ import annotations

from typing import Optional

from ..utils.attributes import get_attribute_manager
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

        # Use attribute manager to get the next missing attribute
        attr_manager = get_attribute_manager()
        next_attr = attr_manager.get_next_missing_attribute("printer", ctx)

        if not next_attr:
            # All attributes collected
            return None

        # Get the predefined question for this attribute
        predefined_question = attr_manager.get_attribute_question(next_attr)

        # Ask the LLM to generate a natural question for this specific attribute
        prompt = (
            f"Generate a natural, conversational question in Dutch to ask about "
            f"the '{next_attr['name']}' attribute for printers. "
            f"The predefined question is: '{predefined_question}'. "
            f"You can use this as-is or rephrase it naturally. "
            f"Context: {ctx}\n\n"
            f"Return only the question, no explanation."
        )

        response = self.model.invoke(prompt)

        if hasattr(response, "content"):
            answer = response.content.strip()
            return answer if answer else predefined_question

        # Fallback to predefined question
        return predefined_question
