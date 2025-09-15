from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pixie.core.utils.config import get_config


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

        # budget handling: accept strings like 'minder dan 50€' or numeric budgets
        budget = None
        if isinstance(attributes, dict):
            budget = attributes.get("budget") or attributes.get("Budget")

        if isinstance(budget, (int, float)):
            max_cents = int(float(budget) * 100)
            items = [it for it in items if int(it.get("price_cents", 0)) <= max_cents]

        # brand filter
        brand = None
        if isinstance(attributes, dict):
            brand = attributes.get("brand") or attributes.get("Brand")
        if isinstance(brand, str):
            items = [it for it in items if it.get("brand", "").lower() == brand.lower()]

        # technology filter
        tech = None
        if isinstance(attributes, dict):
            tech = attributes.get("technology") or attributes.get("Technology")
        if isinstance(tech, str):
            items = [
                it for it in items if it.get("technology", "").lower() == tech.lower()
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
