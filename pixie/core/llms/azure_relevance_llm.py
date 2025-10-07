"""Minimal relevance + category detector backed by Azure OpenAI."""

from __future__ import annotations

from typing import Dict, List, Optional

from .azure_openai_llm import AzureOpenAILLM

# Default fallback in case we cannot fetch categories at startup.
DEFAULT_CATEGORIES: List[Dict[str, str]] = [
    {"name": "printers", "label": "Printers", "description": "n.t.b."},
    {"name": "laptops", "label": "Laptops", "description": "n.t.b."},
    {"name": "smartphones", "label": "Smartphones", "description": "n.t.b."},
    {"name": "computers", "label": "Computers", "description": "n.t.b."},
]


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
        categories: Optional[List[Dict[str, str]]] = None,
    ) -> None:
        super().__init__(api_version, api_endpoint, api_key, model_version, temperature)
        self.model_name = model_name
        self.categories = self._normalise_categories(categories)
        if not self.categories:
            self.categories = self._normalise_categories(DEFAULT_CATEGORIES)

    def set_categories(self, categories: List[Dict[str, str]]) -> None:
        normalised = self._normalise_categories(categories)
        if normalised:
            self.categories = normalised

    def _categories(self) -> List[Dict[str, str]]:
        if not self.categories:
            return self._normalise_categories(DEFAULT_CATEGORIES)
        return self.categories

    def _build_relevance_prompt(self, question: str) -> str:
        categories = self._categories()
        products = []
        for item in categories:
            label = item.get("label") or item["name"]
            description = (item.get("description") or "").strip()
            if description:
                products.append(f"- {label}: {description}")
            else:
                products.append(f"- {label}")
        products_text = "\n".join(products)
        return (
            "Is de volgende vraag gerelateerd aan producten kopen of aanbevelingen?\n\n"
            f"Ondersteunde categorieën:\n{products_text}\n\n"
            "Antwoord enkel met 'yes' of 'no'.\n\n"
            f"Vraag: {question}"
        )

    def _build_category_prompt(self, question: str) -> str:
        categories = self._categories()
        names = [item["name"] for item in categories]
        context_lines: List[str] = []
        for item in categories:
            description = (item.get("description") or "").strip()
            label = item.get("label") or item["name"].title()
            if description:
                context_lines.append(f"- {item['name']}: {label} - {description}")
            else:
                context_lines.append(f"- {item['name']}: {label}")
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
            categories = self._categories()
            valid = {item["name"].lower(): item["name"] for item in categories}
            labels = {item.get("label", "").lower(): item["name"] for item in categories}
            lowered = answer.lower()
            if lowered in valid:
                return valid[lowered]
            if lowered in labels:
                return labels[lowered]
            if lowered == "none":
                return None
        raise ValueError("Invalid response format from Azure model")

    def clear_cache(self) -> None:
        pass

    @staticmethod
    def _normalise_categories(categories: Optional[List[Dict[str, str]]]) -> List[Dict[str, str]]:
        if not categories:
            return []
        result: List[Dict[str, str]] = []
        seen: set[str] = set()
        for item in categories:
            if item is None:
                continue
            if isinstance(item, dict):
                name = str(item.get("name") or item.get("product") or item.get("label") or "").strip()
                label = str(item.get("label") or name.title()).strip()
                description = str(item.get("description") or "").strip()
            else:
                name = str(item).strip()
                label = name.title()
                description = ""
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append({"name": name, "label": label, "description": description})
        return result
