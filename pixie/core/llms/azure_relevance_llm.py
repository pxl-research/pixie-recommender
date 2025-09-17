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

        try:
            prompt = (
                "Is the following question related to buying or searching for products? "
                "The products we support are: laptops, smartphones, headphones, "
                "monitors, tablets, printers, mixers. "
                "Answer with exactly 'yes' or 'no'.\n\n"
                f"Question: {text}"
            )

            response = self.model.invoke(prompt)

            if hasattr(response, "content"):
                answer = response.content.lower().strip()
                return answer == "yes" or answer.startswith("yes")

            raise ValueError("Invalid response format from Azure model")
        except Exception:
            # If Azure call fails, fall back to simple keyword-based relevance check
            product_keywords = [
                "laptop",
                "smartphone",
                "phone",
                "telefoon",
                "tablet",
                "monitor",
                "scherm",
                "headphones",
                "koptelefoon",
                "oortjes",
                "keyboard",
                "mouse",
                "speaker",
                "camera",
                "tv",
                "computer",
                "pc",
                "desktop",
                "printer",
                "drukker",
                "print",
                "mixer",
                "mixers",
                "keukenmachine",
                "handmixer",
                "staafmixer",
                "planetmixer",
                "blender",
            ]
            text_lower = text.lower()
            return any(keyword in text_lower for keyword in product_keywords)

    def detect_category(self, question: Optional[str]) -> Optional[str]:
        """Detect the product category from the question.

        Returns one of: "laptop", "smartphone", "headphones", "monitor",
        "tablet", "printers", or None
        """
        text = (question or "").strip()

        if not self.model:
            # Fall back to keyword-based detection if model is not available
            return self._keyword_based_category_detection(text)

        try:
            prompt = (
                "Determine the product category from the following question. "
                "Possible categories are: laptop, smartphone, headphones, "
                "monitor, tablet, printers, mixer. "
                "If the question is not related to any of these categories, return 'none'. "
                "Answer with exactly one word: laptop, smartphone, headphones, "
                "monitor, tablet, printers, or none.\n\n"
                f"Question: {text}"
            )

            response = self.model.invoke(prompt)

            if hasattr(response, "content"):
                answer = response.content.lower().strip()
                valid_categories = {
                    "laptop",
                    "smartphone",
                    "headphones",
                    "monitor",
                    "tablet",
                    "printers",
                }
                if answer in valid_categories:
                    return answer
                elif answer == "none":
                    return None

            raise ValueError("Invalid response format from Azure model")
        except Exception:
            # If Azure call fails, fall back to keyword-based detection
            return self._keyword_based_category_detection(text)

    def _keyword_based_category_detection(self, text: str) -> Optional[str]:
        """Fallback keyword-based category detection."""
        text_lower = text.lower()

        # Define keywords for each category
        category_keywords = {
            "laptop": ["laptop", "notebook", "ultrabook", "macbook", "chromebook"],
            "smartphone": [
                "smartphone",
                "phone",
                "telefoon",
                "iphone",
                "android",
                "samsung",
                "huawei",
                "xiaomi",
            ],
            "headphones": [
                "headphones",
                "headset",
                "earbuds",
                "earphones",
                "koptelefoon",
                "oortjes",
                "sony",
                "bose",
                "sennheiser",
            ],
            "monitor": [
                "monitor",
                "scherm",
                "display",
                "beeldscherm",
                "lg",
                "dell",
                "samsung",
                "asus",
            ],
            "tablet": [
                "tablet",
                "ipad",
                "surface",
                "galaxy tab",
                "lenovo",
                "microsoft",
                "apple",
            ],
            "printers": [
                "printer",
                "print",
                "drukker",
                "laserprinter",
                "inkjet",
                "hp",
                "brother",
                "canon",
                "epson",
                "samsung",
            ],
            "mixer": [
                "mixer",
                "mixers", 
                "keukenmixer",
                "handmixer",
                "staafmixer", 
                "planetmixer",
                "blender",
                "keukenmachine",
                "kitchenaid",
                "bosch",
                "philips",
                "braun",
                "kenwood",
                "smeg",
                "sage",
            ],
        }

        # Check for category-specific keywords
        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return category

        return None
