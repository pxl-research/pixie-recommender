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
        category = ctx.get(
            "category", "laptop"
        )  # Use category from context, default to laptop

        if not self.model:
            return self._fallback_refinement_question(ctx, category)

        try:
            # Use attribute manager to get the next missing attribute
            attr_manager = get_attribute_manager()
            next_attr = attr_manager.get_next_missing_attribute(category, ctx)

            if not next_attr:
                # All attributes collected
                return None

            # Get the predefined question for this attribute
            predefined_question = attr_manager.get_attribute_question(next_attr)

            # Ask the LLM to generate a natural question for this specific attribute
            prompt = (
                f"Generate a natural, conversational question in Dutch to ask about "
                f"the '{next_attr['name']}' attribute for {category}. "
                f"The predefined question is: '{predefined_question}'. "
                f"You can use this as-is or rephrase it naturally, but keep it concise and "
                f"friendly."
                f"Always start with a question word like 'Wat', 'Welk', 'Heb je', etc. "
                f"Context: {ctx}\n\n"
                f"Return only the question, no explanation."
            )

            response = self.model.invoke(prompt)

            if hasattr(response, "content"):
                answer = response.content.strip()
                return answer if answer else predefined_question

            # Fallback to predefined question
            return predefined_question
        except Exception:
            return self._fallback_refinement_question(ctx, category)

    def _fallback_refinement_question(
        self, context: dict, category: str
    ) -> Optional[str]:
        """Fallback refinement question generation when Azure LLM is not available."""
        # Simple fallback logic based on collected attributes and category
        collected = set(context.get("collected_attributes", []))

        # Get category-specific attributes
        category_attrs = self._get_default_category_attributes(category)

        # Find next uncollected attribute
        for attr_name in category_attrs:
            if attr_name not in collected:
                return self._get_question_for_attribute(attr_name, category)

        return None

    def _get_default_category_attributes(self, category: str) -> list[str]:
        """Get default attribute list for a category."""
        if category == "laptop":
            return [
                "budget",
                "brand",
                "screen_size",
                "processor",
                "ram",
            ]
        elif category == "smartphone":
            return [
                "budget",
                "brand",
                "screen_size",
                "storage",
                "camera",
            ]
        elif category == "headphones":
            return [
                "budget",
                "brand",
                "type",
                "wireless",
                "noise_cancelling",
            ]
        elif category == "monitor":
            return [
                "budget",
                "brand",
                "screen_size",
                "resolution",
                "refresh_rate",
            ]
        elif category == "tablet":
            return [
                "budget",
                "brand",
                "screen_size",
                "storage",
                "cellular",
            ]
        else:  # unknown category
            return ["budget", "brand"]

    def _get_question_for_attribute(self, attr_name: str, category: str) -> str:
        """Get the appropriate question for an attribute based on category."""
        # Try to get from attribute manager first
        try:
            # For now, use hardcoded questions as the attribute manager
            # doesn't support getting questions by name easily
            pass
        except Exception:
            pass

        # Fallback to hardcoded questions
        questions = {
            "price": "Wat is je budget?",
            "budget": "Wat is je budget?",
            "brand": "Heb je een voorkeur voor een merk?",
            "screen_size": "Welke schermgrootte heeft je voorkeur?",
            "processor": "Welke processor heeft je voorkeur?",
            "ram": "Hoeveel RAM heb je nodig?",
            "storage": "Hoeveel opslagruimte heb je nodig?",
            "battery_life": "Hoe belangrijk is de batterijduur?",
            "usage_type": "Waar ga je het apparaat voor gebruiken?",
            "operating_system": "Welk besturingssysteem heeft je voorkeur?",
            "camera_megapixels": "Hoe belangrijk is de camera kwaliteit?",
            "battery_capacity": "Hoe belangrijk is de batterij capaciteit?",
            "form_factor": "Welke vormfactor heeft je voorkeur?",
            "technology": "Welke technologie heeft je voorkeur?",
            "has_color": "Heb je kleurenfunctionaliteit nodig?",
            "is_multifunction": "Moet het apparaat multifunctioneel zijn?",
        }

        return questions.get(attr_name, f"Wat zijn je voorkeuren voor {attr_name}?")
