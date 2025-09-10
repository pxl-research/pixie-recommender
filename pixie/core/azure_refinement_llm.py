from __future__ import annotations

from typing import Optional
import logging

from pixie.core.azure_openai_llm import AzureOpenAILLM


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

    def generate_refinement_question(self, context: Optional[dict] = None) -> Optional[str]:
        ctx = context or {}
        try:
            if hasattr(self.model, "generate") and self.model is not None:
                prompt = (
                    "Given the conversation context as JSON, return a single short"
                    " follow-up question aimed at clarifying the user's needs about"
                    " printers, or return an empty string if no clarification is"
                    " required. Do not add any explanation.\n\n"
                    f"Context: {ctx}"
                )
                resp = self.model.generate([{"role": "user", "content": prompt}])
                if hasattr(resp, "generations"):
                    gens = resp.generations
                    if gens and len(gens) > 0 and len(gens[0]) > 0:
                        return getattr(gens[0][0], "text", None) or str(gens[0][0])
                if hasattr(resp, "text"):
                    return resp.text
        except Exception as e:
            logging.getLogger(__name__).warning(
                "AzureRefinementLLM failed to generate refinement question for context=%r: %s",
                ctx,
                e,
            )

        # Fallback deterministic sequence matching the mock behaviour
        if "budget" not in ctx:
            return "Wat is je budget?"
        if "brand" not in ctx:
            return "Heb je een voorkeur voor een merk?"
        if "technology" not in ctx:
            return "Welke technologie heeft je voorkeur (inkjet/laser)?"
        return None
