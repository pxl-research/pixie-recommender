from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from ..utils.config import get_config


class RealSearchEngine:
    """Simple JSON-backed search engine compatible with MockSearchEngine API.

    Methods:
      search(sql: str, attributes: Optional[Dict[str, Any]],
             category: Optional[str] = None) -> List[Dict]
    """

    def __init__(self, data_file_path: Optional[str] = None):
        if data_file_path is None:
            data_file_path = get_config().search.data_file_path

        self.data_dir = os.path.dirname(data_file_path)
        self._categories_data = self._load_all_categories()
        self._categories_metadata = {}

        # Load metadata for each category
        for category in self._categories_data.keys():
            metadata = self._load_category_metadata(category)
            if metadata:
                self._categories_metadata[category] = metadata

        # For backward compatibility, default to printers
        self._default_category = "printers"

        # default page size for vague queries (no attributes)
        self._default_page_size = get_config().search.default_page_size

    def _load_all_categories(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load all category JSON files from the data directory."""
        categories = {}
        category_files = {
            "printers": "printers.json",
            "laptops": "laptops.json",
            "computers": "computers.json",
            "smartphones": "smartphones.json",
        }

        for category, filename in category_files.items():
            file_path = os.path.join(self.data_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                # Extract the category data (e.g., payload["printers"])
                data = payload.get(category, [])
                categories[category] = data
            except Exception:
                # fail gracefully to empty dataset for this category
                categories[category] = []

        return categories

    def _load_category_metadata(self, category: str) -> Optional[Dict[str, Any]]:
        """Load metadata for a specific category."""
        filename = f"{category}.json"
        file_path = os.path.join(self.data_dir, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return payload.get("_metadata")
        except Exception:
            return None

    def search(
        self,
        sql: str,
        attributes: Optional[Dict[str, Any]],
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        # Determine which category to search in
        if category is None:
            category = self._default_category

        if category not in self._categories_data:
            return []

        data = self._categories_data[category]

        # If attributes is None or empty, return only a small page of items
        # to avoid returning the entire dataset for vague queries.
        if attributes is None or (
            isinstance(attributes, dict) and len(attributes) == 0
        ):
            limit = max(1, self._default_page_size)
            return [self._map_item(i) for i in data[:limit]]

        items = list(data)

        # Apply category-specific filtering
        items = self._apply_category_filters(items, attributes, category)

        # return mapped items (keep structure similar to mock: id, name, price)
        return [self._map_item(it) for it in items]

    def _apply_category_filters(
        self, items: List[Dict[str, Any]], attributes: Dict[str, Any], category: str
    ) -> List[Dict[str, Any]]:
        """Apply category-specific filtering based on attributes."""
        # Common filters for all categories
        items = self._apply_common_filters(items, attributes)

        # Category-specific filters
        if category == "printers":
            items = self._apply_printer_filters(items, attributes)
        elif category == "laptops":
            items = self._apply_laptop_filters(items, attributes)
        elif category == "computers":
            items = self._apply_computer_filters(items, attributes)
        elif category == "smartphones":
            items = self._apply_smartphone_filters(items, attributes)

        return items

    def _apply_common_filters(
        self, items: List[Dict[str, Any]], attributes: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply filters that are common across all categories (budget, brand)."""
        # budget handling: accept strings like 'maximaal 200 euro' or numeric budgets
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

        return items

    def _apply_printer_filters(
        self, items: List[Dict[str, Any]], attributes: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply printer-specific filters."""
        # technology filter (laser/inkjet)
        tech = attributes.get("technology") or attributes.get("Technology")
        if isinstance(tech, str):
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

        return items

    def _apply_laptop_filters(
        self, items: List[Dict[str, Any]], attributes: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply laptop-specific filters."""
        # screen_size filter
        screen_size = attributes.get("screen_size")
        if isinstance(screen_size, str):
            screen_size_str = screen_size.lower().strip()
            if screen_size_str not in ["weet ik niet", "geen idee", "maakt niet uit"]:
                items = [
                    it
                    for it in items
                    if screen_size_str in it.get("screen_size", "").lower()
                ]

        # processor filter
        processor = attributes.get("processor")
        if isinstance(processor, str):
            processor_str = processor.lower().strip()
            if processor_str not in ["weet ik niet", "geen idee", "maakt niet uit"]:
                items = [
                    it
                    for it in items
                    if processor_str in it.get("processor", "").lower()
                ]

        # usage_type filter
        usage_type = attributes.get("usage_type")
        if isinstance(usage_type, str):
            usage_type_str = usage_type.lower().strip()
            if usage_type_str not in ["weet ik niet", "geen idee", "maakt niet uit"]:
                items = [
                    it
                    for it in items
                    if it.get("usage_type", "").lower() == usage_type_str
                ]

        return items

    def _apply_computer_filters(
        self, items: List[Dict[str, Any]], attributes: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply computer-specific filters."""
        # processor filter
        processor = attributes.get("processor")
        if isinstance(processor, str):
            processor_str = processor.lower().strip()
            if processor_str not in ["weet ik niet", "geen idee", "maakt niet uit"]:
                items = [
                    it
                    for it in items
                    if processor_str in it.get("processor", "").lower()
                ]

        # form_factor filter
        form_factor = attributes.get("form_factor")
        if isinstance(form_factor, str):
            form_factor_str = form_factor.lower().strip()
            if form_factor_str not in ["weet ik niet", "geen idee", "maakt niet uit"]:
                items = [
                    it
                    for it in items
                    if it.get("form_factor", "").lower() == form_factor_str
                ]

        # usage_type filter
        usage_type = attributes.get("usage_type")
        if isinstance(usage_type, str):
            usage_type_str = usage_type.lower().strip()
            if usage_type_str not in ["weet ik niet", "geen idee", "maakt niet uit"]:
                items = [
                    it
                    for it in items
                    if it.get("usage_type", "").lower() == usage_type_str
                ]

        return items

    def _apply_smartphone_filters(
        self, items: List[Dict[str, Any]], attributes: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply smartphone-specific filters."""
        # screen_size filter
        screen_size = attributes.get("screen_size")
        if isinstance(screen_size, str):
            screen_size_str = screen_size.lower().strip()
            if screen_size_str not in ["weet ik niet", "geen idee", "maakt niet uit"]:
                items = [
                    it
                    for it in items
                    if screen_size_str in it.get("screen_size", "").lower()
                ]

        # operating_system filter
        operating_system = attributes.get("operating_system")
        if isinstance(operating_system, str):
            os_str = operating_system.lower().strip()
            if os_str not in ["weet ik niet", "geen idee", "maakt niet uit"]:
                items = [
                    it
                    for it in items
                    if it.get("operating_system", "").lower() == os_str
                ]

        return items

    def _map_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        # Accept either item object or dict of full fields
        if isinstance(item, dict) and "id" in item and "name" in item:
            return {
                "id": item.get("id"),
                "name": item.get("name"),
                "price": item.get("price"),
            }
        return item

    def get_categories(self) -> List[str]:
        """Get list of available categories."""
        return list(self._categories_data.keys())

    def get_category_metadata(self, category: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific category."""
        return self._categories_metadata.get(category)

    def _load_data(self, path: str) -> List[Dict[str, Any]]:
        """Legacy method for backward compatibility."""
        return self._categories_data.get(self._default_category, [])


def create_real_search_engine(data_file_path: Optional[str] = None) -> RealSearchEngine:
    return RealSearchEngine(data_file_path)
