"""Minimal relevance + category detector backed by Azure OpenAI."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .azure_openai_llm import AzureOpenAILLM


class AzureRelevanceLLM(AzureOpenAILLM):
    """Checks relevance and maps questions onto one of the known categories."""

    def __init__(
        self,
        api_version: str,
        api_endpoint: str,
        api_key: str,
        model_version: str,
        temperature: float = 0.01,
        model_name: str = "azure-relevance-llm",
        categories: Optional[List[str]] = None,
    ) -> None:
        super().__init__(api_version, api_endpoint, api_key, model_version, temperature)
        self.model_name = model_name
        self.categories: List[str] = []
        self._initialise_categories(categories)

    def set_categories(self, categories: List[str]) -> None:
        cleaned = [item.strip() for item in categories if item and item.strip()]
        if not cleaned:
            raise ValueError("Relevance model requires non-empty categories")
        self.categories = cleaned

    def _initialise_categories(self, categories: Optional[List[str]]) -> None:
        if not categories:
            raise ValueError("At least one category is required for the relevance model")
        self.set_categories(categories)

    def _build_relevance_prompt(self, question: str) -> str:
        products_text = "\n".join(
            f"- {name.replace('_', ' ').title()}" for name in self.categories
        )
        return (
            "Is de volgende vraag gerelateerd aan producten kopen of aanbevelingen?\n\n"
            f"Ondersteunde categorieën:\n{products_text}\n\n"
            "Antwoord enkel met 'yes' of 'no'.\n\n"
            f"Vraag: {question}"
        )

    def _build_category_prompt(self, question: str) -> str:
        names = [name for name in self.categories]
        context = "\n".join(
            f"- {name}: {name.replace('_', ' ').title()}" for name in self.categories
        )
        return (
            "Bepaal de productcategorie voor de volgende vraag.\n\n"
            f"Mogelijkheden: {', '.join(names)}\n\n"
            "Antwoord met precies één productnaam uit de lijst of 'none'.\n\n"
            f"Context:\n{context}\n\n"
            f"Vraag: {question}"
        )

    def _invoke_model(self, prompt: str) -> str:
        if not self.model:
            raise ValueError("Azure model is not available - check your configuration")
        response = self.model.invoke(prompt)
        if not hasattr(response, "content"):
            raise ValueError("Invalid response format from Azure model")
        return str(response.content).strip()

    def is_relevant(self, question: Optional[str]) -> bool:
        text = (question or "").strip()
        prompt = self._build_relevance_prompt(text)
        answer = self._invoke_model(prompt).lower()
        return answer == "yes" or answer.startswith("yes")

    def detect_category(self, question: Optional[str]) -> Optional[str]:
        text = (question or "").strip()
        prompt = self._build_category_prompt(text)
        answer = self._invoke_model(prompt)
        lowered = answer.lower()
        name_lookup = {name.lower(): name for name in self.categories}
        label_lookup = {
            name.replace("_", " ").lower(): name for name in self.categories
        }
        if lowered in name_lookup:
            return name_lookup[lowered]
        if lowered in label_lookup:
            return label_lookup[lowered]
        if lowered == "none":
            return None
        raise ValueError("Invalid response format from Azure model")

    def check_relevance_and_category(self, question: Optional[str]) -> Dict[str, Any]:
        relevant = self.is_relevant(question)
        if not relevant:
            return {"relevant": False, "category": None}
        category = self.detect_category(question)
        return {"relevant": True, "category": category}

    def clear_cache(self) -> None:
        pass
