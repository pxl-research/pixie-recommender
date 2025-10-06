from __future__ import annotations

from typing import Optional

from .azure_openai_llm import AzureOpenAILLM

# TODO: Replace with metadata retrieved from the external dataset.
DEFAULT_CATEGORIES = [
    {"name": "printers", "label": "Printers", "description": "n.t.b."},
    {"name": "laptops", "label": "Laptops", "description": "n.t.b."},
    {"name": "smartphones", "label": "Smartphones", "description": "n.t.b."},
    {"name": "computers", "label": "Computers", "description": "n.t.b."},
]


class AzureRelevanceLLM(AzureOpenAILLM):
    def __init__(
        self,
        api_version: str,
        api_endpoint: str,
        api_key: str,
        model_version: str,
        temperature: float = 0.01,
        model_name: str = "azure-relevance-llm",
    ) -> None:
        super().__init__(api_version, api_endpoint, api_key, model_version, temperature)
        self.model_name = model_name

    def _build_relevance_prompt(self, question: str) -> str:
        products = "\n".join(f"- {item['label']}" for item in DEFAULT_CATEGORIES)
        return (
            "Is de volgende vraag gerelateerd aan producten kopen of aanbevelingen?\n\n"
            f"Ondersteunde categorieën:\n{products}\n\n"
            "Antwoord enkel met 'yes' of 'no'.\n\n"
            f"Vraag: {question}"
        )

    def _build_category_prompt(self, question: str) -> str:
        names = [item["name"] for item in DEFAULT_CATEGORIES]
        context = [f"- {item['name']}: {item['label']} - {item['description']}" for item in DEFAULT_CATEGORIES]
        return (
            "Bepaal de productcategorie voor de volgende vraag.\n\n"
            f"Mogelijkheden: {', '.join(names)}\n\n"
            "Antwoord met precies één woord uit de lijst of 'none'.\n\n"
            f"Context:\n{chr(10).join(context)}\n\n"
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
            answer = response.content.lower().strip()
            valid = {item["name"] for item in DEFAULT_CATEGORIES}
            if answer in valid:
                return answer
            if answer == "none":
                return None
        raise ValueError("Invalid response format from Azure model")

    def clear_cache(self) -> None:
        pass
