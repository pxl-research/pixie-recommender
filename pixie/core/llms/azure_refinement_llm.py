from __future__ import annotations

from typing import Optional

from .azure_openai_llm import AzureOpenAILLM


class AzureRefinementLLM(AzureOpenAILLM):
    """Legacy helper that can generate clarifying questions (TODO: new dataset)."""

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

        # TODO: load attribute metadata from external dataset
        next_attribute = None
        for candidate in ("budget", "brand", "technology", "screen_size", "processor"):
            if candidate not in collected and candidate not in skipped:
                next_attribute = candidate
                break

        if next_attribute is None:
            return None

        predefined_question = "Kun je wat meer details delen?" if next_attribute == "budget" else f"Geef meer info over {next_attribute}?"

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
        attr_name = next_attribute

        prompt = (
            "Je bent een Nederlandse productadviseur. "
            f"Formuleer een korte vraag om '{attr_name}' te achterhalen voor categorie {category}. "
            f"Basis: '{predefined_question}'. Houd het onder 15 woorden en geef uitsluitend de vraag."
        )
        prompt += context_info

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
