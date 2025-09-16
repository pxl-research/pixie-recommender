"""Database-backed search engine that replaces JSON-based search."""

import logging
from typing import Any, Dict, List, Optional

from ..database.connection import get_db_session
from ..database.repositories import (
    ComputerRepository,
    LaptopRepository,
    PrinterRepository,
    SmartphoneRepository,
)

logger = logging.getLogger(__name__)


class DatabaseSearchEngine:
    """Database-backed search engine compatible with RealSearchEngine API.

    Methods:
      search(sql: str, attributes: Optional[Dict[str, Any]],
             category: Optional[str] = None) -> List[Dict]
    """

    def __init__(self):
        self._default_category = "printers"
        self._default_page_size = 10  # This should come from config

    def search(
        self,
        sql: str,
        attributes: Optional[Dict[str, Any]],
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search products using database queries."""
        # Determine which category to search in
        if category is None:
            category = self._default_category

        # If attributes is None or empty, return only a small page of items
        if attributes is None or (
            isinstance(attributes, dict) and len(attributes) == 0
        ):
            return self._get_default_results(category)

        with get_db_session() as session:
            try:
                # Route to appropriate repository based on category
                if category == "printers":
                    return self._search_printers(session, attributes)
                elif category == "laptops":
                    return self._search_laptops(session, attributes)
                elif category == "computers":
                    return self._search_computers(session, attributes)
                elif category == "smartphones":
                    return self._search_smartphones(session, attributes)
                else:
                    logger.warning(f"Unknown category: {category}")
                    return []
            except Exception as e:
                logger.error(f"Search error for category {category}: {e}")
                return []

    def _get_default_results(self, category: str) -> List[Dict[str, Any]]:
        """Get default results when no attributes are provided."""
        with get_db_session() as session:
            try:
                if category == "printers":
                    repo = PrinterRepository(session)
                    printers = repo.get_all(limit=self._default_page_size)
                    return [self._map_printer(p) for p in printers]
                elif category == "laptops":
                    repo = LaptopRepository(session)
                    laptops = repo.get_all(limit=self._default_page_size)
                    return [self._map_laptop(L) for L in laptops]
                elif category == "computers":
                    repo = ComputerRepository(session)
                    computers = repo.get_all(limit=self._default_page_size)
                    return [self._map_computer(c) for c in computers]
                elif category == "smartphones":
                    repo = SmartphoneRepository(session)
                    smartphones = repo.get_all(limit=self._default_page_size)
                    return [self._map_smartphone(s) for s in smartphones]
                else:
                    return []
            except Exception as e:
                logger.error(f"Error getting default results for {category}: {e}")
                return []

    def _search_printers(self, session, attributes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search printers with database queries."""
        repo = PrinterRepository(session)

        # Apply common filters
        filtered_items = self._apply_common_filters(repo, attributes)

        # Apply printer-specific filters
        filtered_items = self._apply_printer_filters(filtered_items, attributes)

        # Convert to dict format
        return [self._map_printer(p) for p in filtered_items]

    def _search_laptops(self, session, attributes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search laptops with database queries."""
        repo = LaptopRepository(session)

        # Apply common filters
        filtered_items = self._apply_common_filters(repo, attributes)

        # Apply laptop-specific filters
        filtered_items = self._apply_laptop_filters(filtered_items, attributes)

        # Convert to dict format
        return [self._map_laptop(L) for L in filtered_items]

    def _search_computers(self, session, attributes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search computers with database queries."""
        repo = ComputerRepository(session)

        # Apply common filters
        filtered_items = self._apply_common_filters(repo, attributes)

        # Apply computer-specific filters
        filtered_items = self._apply_computer_filters(filtered_items, attributes)

        # Convert to dict format
        return [self._map_computer(c) for c in filtered_items]

    def _search_smartphones(self, session, attributes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search smartphones with database queries."""
        repo = SmartphoneRepository(session)

        # Apply common filters
        filtered_items = self._apply_common_filters(repo, attributes)

        # Apply smartphone-specific filters
        filtered_items = self._apply_smartphone_filters(filtered_items, attributes)

        # Convert to dict format
        return [self._map_smartphone(s) for s in filtered_items]

    def _apply_common_filters(self, repo, attributes: Dict[str, Any]):
        """Apply filters that are common across all categories (budget, brand)."""
        # Start with all items
        items = repo.get_all()

        # Budget filtering
        budget = attributes.get("budget") or attributes.get("Budget")
        max_budget_value = self._parse_budget(budget)

        if max_budget_value is not None:
            # Filter by price (not price_cents)
            items = [item for item in items if float(getattr(item, 'price', 0)) <= max_budget_value]

        # Brand filtering
        brand = attributes.get("brand") or attributes.get("Brand")
        if isinstance(brand, str) and not self._is_vague_response(brand):
            # Use repository's brand filtering
            items = repo.get_by_brand(brand)

        return items

    def _apply_printer_filters(self, items, attributes: Dict[str, Any]):
        """Apply printer-specific filters."""
        # Technology filter
        tech = attributes.get("technology") or attributes.get("Technology")
        if isinstance(tech, str) and not self._is_vague_response(tech):
            # Filter items by technology
            items = [
                item for item in items
                if getattr(item, 'technology', '').lower() == tech.lower()
            ]

        return items

    def _apply_laptop_filters(self, items, attributes: Dict[str, Any]):
        """Apply laptop-specific filters."""
        # Screen size filter
        screen_size = attributes.get("screen_size")
        if isinstance(screen_size, str) and not self._is_vague_response(screen_size):
            items = [
                item for item in items
                if screen_size.lower() in getattr(item, 'screen_size_inches', '').lower()
            ]

        # Processor filter
        processor = attributes.get("processor")
        if isinstance(processor, str) and not self._is_vague_response(processor):
            items = [
                item for item in items
                if processor.lower() in getattr(item, 'processor', '').lower()
            ]

        return items

    def _apply_computer_filters(self, items, attributes: Dict[str, Any]):
        """Apply computer-specific filters."""
        # Processor filter
        processor = attributes.get("processor")
        if isinstance(processor, str) and not self._is_vague_response(processor):
            items = [
                item for item in items
                if processor.lower() in getattr(item, 'processor', '').lower()
            ]

        return items

    def _apply_smartphone_filters(self, items, attributes: Dict[str, Any]):
        """Apply smartphone-specific filters."""
        # Screen size filter
        screen_size = attributes.get("screen_size")
        if isinstance(screen_size, str) and not self._is_vague_response(screen_size):
            items = [
                item for item in items
                if screen_size.lower() in getattr(item, 'screen_size_inches', '').lower()
            ]

        # Operating system filter
        operating_system = attributes.get("operating_system")
        if isinstance(operating_system, str) and not self._is_vague_response(operating_system):
            items = [
                item for item in items
                if operating_system.lower() == getattr(item, 'operating_system', '').lower()
            ]

        return items

    def _parse_budget(self, budget) -> Optional[float]:
        """Parse budget value from various formats."""
        if isinstance(budget, (int, float)):
            return float(budget)
        elif isinstance(budget, str):
            if self._is_vague_response(budget):
                return None

            # Parse budget strings like "maximaal 200 euro", "200", "100-200 euro"
            import re
            numbers = re.findall(r"\d+", budget)
            if numbers:
                if "-" in budget and len(numbers) >= 2:
                    # Range format: use the maximum value
                    return float(numbers[-1])
                else:
                    # Single number: use as maximum
                    return float(numbers[-1])
        return None

    def _is_vague_response(self, response: str) -> bool:
        """Check if response is vague and should be ignored."""
        vague_responses = [
            "weet ik niet", "geen idee", "maakt niet uit", "doet er niet toe",
            "geen voorkeur", "weet niet", "onbekend", "nvt", "n.v.t."
        ]
        return response.lower().strip() in vague_responses

    def _map_printer(self, printer) -> Dict[str, Any]:
        """Map printer model to dict format."""
        return {
            "id": printer.id,
            "name": printer.name,
            "price": float(printer.price),
        }

    def _map_laptop(self, laptop) -> Dict[str, Any]:
        """Map laptop model to dict format."""
        return {
            "id": laptop.id,
            "name": laptop.name,
            "price": float(laptop.price),
        }

    def _map_computer(self, computer) -> Dict[str, Any]:
        """Map computer model to dict format."""
        return {
            "id": computer.id,
            "name": computer.name,
            "price": float(computer.price),
        }

    def _map_smartphone(self, smartphone) -> Dict[str, Any]:
        """Map smartphone model to dict format."""
        return {
            "id": smartphone.id,
            "name": smartphone.name,
            "price": float(smartphone.price),
        }

    def get_categories(self) -> List[str]:
        """Get list of available categories."""
        return ["printers", "laptops", "computers", "smartphones"]

    def get_category_metadata(self, category: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific category."""
        # This would need to be implemented based on attributes table
        # For now, return None to maintain compatibility
        return None


def create_database_search_engine() -> DatabaseSearchEngine:
    """Factory function for database search engine."""
    return DatabaseSearchEngine()
