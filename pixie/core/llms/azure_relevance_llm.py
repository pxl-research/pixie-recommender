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
        if not categories:
            raise ValueError("At least one category is required for the relevance model")
        self.categories: List[str] = [item.strip() for item in categories if item and item.strip()]
        if not self.categories:
            raise ValueError("At least one category is required for the relevance model")

    def set_categories(self, categories: List[str]) -> None:
        cleaned = [item.strip() for item in categories if item and item.strip()]
        if not cleaned:
            raise ValueError("Relevance model requires non-empty categories")
        self.categories = cleaned

    def _build_relevance_prompt(self, question: str) -> str:
        products = []
        for name in self.categories:
            label = name.replace("_", " ").title()
            products.append(f"- {label}")
        products_text = "\n".join(products)
        return (
            "Is de volgende vraag gerelateerd aan producten kopen of aanbevelingen?\n\n"
            f"Ondersteunde categorieën:\n{products_text}\n\n"
            "Antwoord enkel met 'yes' of 'no'.\n\n"
            f"Vraag: {question}"
        )

    def _build_category_prompt(self, question: str) -> str:
        names: List[str] = []
        context_lines: List[str] = []
        for name in self.categories:
            label = name.replace("_", " ").title()
            names.append(name)
            context_lines.append(f"- {name}: {label}")
        context = "\n".join(context_lines)
        return (
            "Bepaal de productcategorie voor de volgende vraag.\n\n"
            f"Mogelijkheden: {', '.join(names)}\n\n"
            "Antwoord met precies één productnaam uit de lijst of 'none'.\n\n"
            f"Context:\n{context}\n\n"
            f"Vraag: {question}"
        )

    def is_relevant(self, question: Optional[str]) -> bool:
        text = (question or "").strip()
        if not self.model:
            raise ValueError("Azure model is not available - check your configuration")
        prompt = self._build_relevance_prompt(text)
        response = self.model.invoke(prompt)
        if hasattr(response, "content"):
            answer = response.content.lower().strip()
            return answer == "yes" or answer.startswith("yes")
        raise ValueError("Invalid response format from Azure model")

    def detect_category(self, question: Optional[str]) -> Optional[str]:
        text = (question or "").strip()
        if not self.model:
            raise ValueError("Azure model is not available - check your configuration")
        prompt = self._build_category_prompt(text)
        response = self.model.invoke(prompt)
        if hasattr(response, "content"):
            answer = response.content.strip()
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
