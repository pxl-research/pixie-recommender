from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class AttributeManager:
    """Manages product attributes and their questioning sequence."""

    def __init__(self, attributes_file: str = "pixie/core/data/attributes.json"):
        self.attributes_file = Path(attributes_file)
        self._attributes_cache: Optional[Dict[str, Any]] = None

    def _load_attributes(self) -> Dict[str, Any]:
        """Load attributes configuration from JSON file."""
        if self._attributes_cache is None:
            try:
                with open(self.attributes_file, "r", encoding="utf-8") as f:
                    self._attributes_cache = json.load(f)
            except Exception:
                # Fallback to empty config
                self._attributes_cache = {}
        return self._attributes_cache or {}

    def get_attributes_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all attributes for a specific category (e.g., 'printer')."""
        config = self._load_attributes()
        return config.get(category, {}).get("attributes", [])

    def get_next_missing_attribute(
        self, category: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find the next attribute that hasn't been collected yet."""
        attributes = self.get_attributes_for_category(category)

        for attr in attributes:
            attr_name = attr["name"]
            if attr_name not in context:
                return attr

        return None  # All attributes collected

    def get_attribute_question(self, attribute: Dict[str, Any]) -> str:
        """Get the question to ask for a specific attribute."""
        return attribute.get(
            "question", f"What is your preference for {attribute['name']}?"
        )


# Global instance
_attribute_manager: Optional[AttributeManager] = None


def get_attribute_manager() -> AttributeManager:
    """Get the global attribute manager instance."""
    global _attribute_manager
    if _attribute_manager is None:
        _attribute_manager = AttributeManager()
    return _attribute_manager
