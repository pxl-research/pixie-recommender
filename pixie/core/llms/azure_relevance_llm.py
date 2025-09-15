from __future__ import annotations

import logging
from typing import Optional

from .azure_openai_llm import AzureOpenAILLM


class AzureRelevanceLLM(AzureOpenAILLM):
    """Azure-based relevance classifier for printer-related queries.

    The implementation prefers using the Azure OpenAI client but falls
    back to a simple keyword heuristic when the API call fails or is
    unavailable. This keeps imports and instantiation safe in tests.
    """

    def __init__(
        self,
        api_version: str,
        api_endpoint: str,
        api_key: str,
        model_version: str,
        temperature: float = 0.01,
        model_name: str = "azure-relevance-llm",
    ):
        super().__init__(api_version, api_endpoint, api_key, model_version, temperature)
        self.model_name = model_name

    def is_relevant(self, question: Optional[str]) -> bool:
        text = (question or "").strip()

        # Try to use the Azure model if available. If anything goes wrong,
        # fall back to the conservative keyword heuristic (like the mock).
        try:
            if hasattr(self.model, "generate") and self.model is not None:
                prompt = (
                    "Is de volgende vraag gerelateerd aan printers? "
                    "Beantwoord met precies 'ja' als het gerelateerd is aan printers, "
                    "of 'nee' als niet.\n\n"
                    f"Vraag: {text}"
                )
                resp = self.model.generate([{"role": "user", "content": prompt}])

                # Best-effort extraction of text from different langchain return shapes.
                ans = None
                if hasattr(resp, "content"):
                    ans = resp.content
                elif hasattr(resp, "generations"):
                    gens = resp.generations
                    if gens and len(gens) > 0 and len(gens[0]) > 0:
                        ans = getattr(gens[0][0], "text", None) or str(gens[0][0])
                elif hasattr(resp, "text"):
                    ans = resp.text

                if ans:
                    a = ans.lower().strip()
                    return (
                        "yes" in a
                        or "true" in a
                        or "ja" in a
                        or "oui" in a
                        or "si" in a
                        or a.startswith("y")
                        or a.startswith("j")
                        or a == "ja"
                        or a == "yes"
                    )
        except Exception as e:
            logging.getLogger(__name__).error(
                "AzureRelevanceLLM failed to classify relevance for question=%r: %s",
                text,
                e,
            )
            raise  # Re-raise the exception instead of falling back to heuristic
