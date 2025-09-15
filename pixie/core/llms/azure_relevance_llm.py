from __future__ import annotations

from typing import Optional

from .azure_openai_llm import AzureOpenAILLM


class AzureRelevanceLLM(AzureOpenAILLM):
    """Azure-based relevance classifier for printer-related queries."""

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

        if not self.model:
            raise ValueError("Azure model is not available")

        prompt = (
            "Is the following question related to printers? "
            "Answer with exactly 'yes' or 'no'.\n\n"
            f"Question: {text}"
        )

        response = self.model.invoke(prompt)

        if hasattr(response, "content"):
            answer = response.content.lower().strip()
            return answer == "yes" or answer.startswith("yes")

        raise ValueError("Invalid response format from Azure model")
