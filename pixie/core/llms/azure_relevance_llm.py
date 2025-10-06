from __future__ import annotations

from typing import Dict, List, Optional

from ..utils.attribute_catalog import (
    ProductType,
    get_attribute_definitions,
    get_product_type,
    list_product_types,
)
from .azure_openai_llm import AzureOpenAILLM


class AzureRelevanceLLM(AzureOpenAILLM):
    """Azure-based relevance classifier for product-related queries."""

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
        self._product_types_cache: Optional[List[ProductType]] = None
        self._attributes_cache: Optional[Dict[str, List[str]]] = None

    def _get_product_types(self) -> List[Dict]:
        """Get all supported product types from the static catalog."""
        if self._product_types_cache is None:
            self._product_types_cache = list(list_product_types())
        return self._product_types_cache

    def _get_attributes_for_product_type(self, product_type_name: str) -> List[Dict]:
        """Get all attributes for a specific product type with caching."""
        if self._attributes_cache is None:
            self._attributes_cache = {}

        if product_type_name not in self._attributes_cache:
            attributes = get_attribute_definitions(product_type_name)
            if not attributes:
                product_type = get_product_type(product_type_name)
                attributes = product_type.attributes if product_type else []
            self._attributes_cache[product_type_name] = attributes

        return [
            {
                "name": attr.name,
                "display_name": attr.display_name,
            }
            for attr in self._attributes_cache[product_type_name]
        ]

    def _build_relevance_prompt(self, question: str) -> str:
        """Build a dynamic prompt based on the static product catalog."""
        product_types = self._get_product_types()

        # Build product type list
        product_list = []
        for pt in product_types:
            attributes = self._get_attributes_for_product_type(pt.name)
            attr_names = [attr["display_name"] for attr in attributes[:5]]
            if attr_names:
                product_list.append(
                    f"{pt.display_name} (with attributes like: {', '.join(attr_names)})"
                )
            else:
                product_list.append(pt.display_name)

        prompt = (
            "Is the following question related to buying, searching for, "
            "or getting recommendations about products?\n\n"
            f"The products we support are:\n"
            f"{chr(10).join(f'- {product}' for product in product_list)}\n\n"
            f"Answer with exactly 'yes' or 'no'.\n\n"
            f"Question: {question}"
        )

        return prompt

    def _build_category_prompt(self, question: str) -> str:
        """Build a dynamic category detection prompt using the static catalog."""
        product_types = self._get_product_types()
        product_names = [pt.name for pt in product_types]

        context_lines = []
        for pt in product_types:
            context_lines.append(
                f"- {pt.name}: {pt.display_name} - {pt.description}"
            )

        prompt = (
            "Determine the product category from the following question.\n\n"
            f"Possible categories are: {', '.join(product_names)}\n\n"
            "If the question is not related to any of these categories, return 'none'.\n"
            f"Answer with exactly one word from this list: "
            f"{', '.join(product_names + ['none'])}.\n\n"
            f"Context:\n{chr(10).join(context_lines)}\n\n"
            f"Question: {question}"
        )

        return prompt

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
        """Detect the product category from the question.

        Returns one of the product type names from the catalog, or None.
        """
        text = (question or "").strip()

        if not self.model:
            raise ValueError("Azure model is not available - check your configuration")

        prompt = self._build_category_prompt(text)
        response = self.model.invoke(prompt)

        if hasattr(response, "content"):
            answer = response.content.lower().strip()

            # Check if answer is a valid product type
            valid_categories = {pt.name for pt in self._get_product_types()}
            if answer in valid_categories:
                return answer
            elif answer == "none":
                return None

        raise ValueError("Invalid response format from Azure model")

    def clear_cache(self) -> None:
        """Clear the internal cache to force a reload from the static catalog."""
        self._product_types_cache = None
        self._attributes_cache = None
