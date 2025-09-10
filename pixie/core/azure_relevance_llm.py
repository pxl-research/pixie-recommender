from __future__ import annotations

from typing import Optional
import logging

from pixie.core.azure_openai_llm import AzureOpenAILLM


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
                    "Is the following question related to printers? Answer 'yes' or 'no'.\n\n"
                    f"Question: {text}"
                )
                resp = self.model.generate([{"role": "user", "content": prompt}])

                # Best-effort extraction of text from different langchain return shapes.
                ans = None
                if hasattr(resp, "generations"):
                    gens = resp.generations
                    if gens and len(gens) > 0 and len(gens[0]) > 0:
                        ans = getattr(gens[0][0], "text", None) or str(gens[0][0])
                elif hasattr(resp, "text"):
                    ans = resp.text

                if ans:
                    a = ans.lower()
                    return "yes" in a or "true" in a
        except Exception as e:
            logging.getLogger(__name__).warning(
                "AzureRelevanceLLM failed to classify relevance for question=%r: %s",
                text,
                e,
            )
            # fall through to heuristic fallback

        # Fallback heuristic identical to the original mock implementation.
        return "printer" in text.lower() or "printers" in text.lower()
