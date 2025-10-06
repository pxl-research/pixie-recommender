from __future__ import annotations

from typing import Optional

from ..utils.attribute_catalog import get_attribute_definitions
from .azure_openai_llm import AzureOpenAILLM


class AzureRefinementLLM(AzureOpenAILLM):
    """Azure-based refinement question generator.

    Generates natural, contextual questions for collecting product attributes
    based on the static attribute catalog and LLM intelligence.
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
        """Generate the next refinement question based on missing attributes."""
        ctx = context or {}
        category = ctx.get("category", "laptop")

        collected = set(ctx.get("collected_attributes", []))
        skipped = set(ctx.get("skipped_attributes", []))
        next_attr = None
        for attr in get_attribute_definitions(category):
            if attr.name not in collected and attr.name not in skipped:
                next_attr = attr
                break

        if next_attr is None:
            # All attributes collected
            return None

        # Get the predefined question for this attribute
        predefined_question = next_attr.question

        # If no LLM model available, use the predefined question directly
        if not self.model:
            return predefined_question

        # Collect context about already asked/collected attributes
        collected_attrs = ctx.get("collected_attributes", [])
        skipped_attrs = ctx.get("skipped_attributes", [])

        # Build context for LLM to understand what we already know
        context_info = ""
        if collected_attrs or skipped_attrs:
            all_discussed = collected_attrs + skipped_attrs
            context_info = f"\nAlready discussed attributes: {', '.join(all_discussed)}"

        # Ask the LLM to generate a natural, contextual question
        attr_name = next_attr.name
        attr_type = next_attr.type
        attr_description = next_attr.description

        prompt = f"""Je bent een vriendelijke Nederlandse productadviseur. 
Genereer een natuurlijke vraag om meer te weten te komen over de 
'{attr_name}' eigenschap voor {category}.

Basis vraag: "{predefined_question}"
Attribuut type: {attr_type}
Beschrijving: {attr_description}

Richtlijnen:
- Houd het kort en natuurlijk (max 15 woorden)
- Begin met vraagwoorden zoals 'Wat', 'Welk', 'Heb je', 'Hoeveel'
- Maak het persoonlijk en vriendelijk
- Vermijd technisch jargon waar mogelijk
- Pas de vraag aan voor Nederlandse context{context_info}

Genereer alleen de vraag, geen uitleg."""

        try:
            response = self.model.invoke(prompt)

            if hasattr(response, "content"):
                answer = response.content.strip()

                # Clean up the response
                if answer:
                    # Remove any quotation marks
                    answer = answer.strip("\"'")
                    # Ensure it ends with a question mark
                    if not answer.endswith("?"):
                        answer += "?"

                    # Validate it's a reasonable question (not too short/long)
                    if 5 <= len(answer) <= 100:
                        return answer

            # If LLM response is invalid, use predefined question
            return predefined_question

        except Exception as e:
            print(f"Error generating refinement question: {e}")
            # Use predefined question as backup
            return predefined_question
