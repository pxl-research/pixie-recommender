from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ..utils.config import get_config


class RealSearchEngine:
    """Simple JSON-backed search engine compatible with MockSearchEngine API.

    Methods:
      search(sql: str, attributes: Optional[Dict[str, Any]]) -> List[Dict]
    """

    def __init__(self, data_file_path: Optional[str] = None):
        if data_file_path is None:
            data_file_path = get_config().search.data_file_path
        self.data_file_path = data_file_path
        self._data = self._load_data(self.data_file_path)
        # default page size for vague queries (no attributes)
        self._default_page_size = get_config().search.default_page_size

    def _load_data(self, path: str) -> List[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return payload.get("printers", [])
        except Exception:
            # fail gracefully to empty dataset
            return []

    def search(
        self, sql: str, attributes: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # If attributes is None or empty, return only a small page of items
        # to avoid returning the entire dataset for vague queries.
        if attributes is None or (
            isinstance(attributes, dict) and len(attributes) == 0
        ):
            limit = max(1, self._default_page_size)
            return [self._map_item(i) for i in self._data[:limit]]

        items = list(self._data)

        # budget handling: accept strings like 'maximaal 200 euro' or numeric budgets
        budget = None
        if isinstance(attributes, dict):
            budget = attributes.get("budget") or attributes.get("Budget")

        max_budget_value = None
        if isinstance(budget, (int, float)):
            max_budget_value = float(budget)
        elif isinstance(budget, str):
            # Check if it's a vague response that should be ignored
            budget_str = budget.lower().strip()
            vague_budget_responses = [
                "weet ik niet",
                "geen idee",
                "maakt niet uit",
                "doet er niet toe",
                "geen voorkeur",
                "weet niet",
                "onbekend",
                "nvt",
                "n.v.t.",
            ]

            if budget_str not in vague_budget_responses:
                # Parse budget strings like "maximaal 200 euro", "200", "100-200 euro"
                import re

                # Extract numeric values from the budget string
                numbers = re.findall(r"\d+", budget_str)
                if numbers:
                    if "-" in budget_str and len(numbers) >= 2:
                        # Range format: use the maximum value
                        max_budget_value = float(numbers[-1])
                    else:
                        # Single number: use as maximum
                        max_budget_value = float(numbers[-1])

        # Apply budget filtering if we found a budget value
        if max_budget_value is not None:
            # Filter by price (euro) not price_cents
            items = [
                it for it in items if float(it.get("price", 0)) <= max_budget_value
            ]

        # brand filter
        brand = None
        if isinstance(attributes, dict):
            brand = attributes.get("brand") or attributes.get("Brand")
        if isinstance(brand, str):
            # Check if it's a vague response that should be ignored
            brand_str = brand.lower().strip()
            vague_brand_responses = [
                "weet ik niet",
                "geen idee",
                "maakt niet uit",
                "doet er niet toe",
                "geen voorkeur",
                "weet niet",
                "onbekend",
                "nvt",
                "n.v.t.",
            ]

            if brand_str not in vague_brand_responses:
                items = [
                    it for it in items if it.get("brand", "").lower() == brand.lower()
                ]

        # technology filter
        tech = None
        if isinstance(attributes, dict):
            tech = attributes.get("technology") or attributes.get("Technology")
        if isinstance(tech, str):
            # Check if it's a vague response that should be ignored
            tech_str = tech.lower().strip()
            vague_tech_responses = [
                "weet ik niet",
                "geen idee",
                "maakt niet uit",
                "doet er niet toe",
                "geen voorkeur",
                "weet niet",
                "onbekend",
                "nvt",
                "n.v.t.",
            ]

            if tech_str not in vague_tech_responses:
                items = [
                    it
                    for it in items
                    if it.get("technology", "").lower() == tech.lower()
                ]

        # return mapped items (keep structure similar to mock: id, name, price)
        return [self._map_item(it) for it in items]

    def _map_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        # Accept either item object or dict of full fields
        if isinstance(item, dict) and "id" in item and "name" in item:
            return {
                "id": item.get("id"),
                "name": item.get("name"),
                "price": item.get("price"),
            }
        return item


def create_real_search_engine(data_file_path: Optional[str] = None) -> RealSearchEngine:
    return RealSearchEngine(data_file_path)
