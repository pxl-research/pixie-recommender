"""
Simplified Attribute Collection Logic

Extracts the complex attribute gathering from conversation_loop.py
Into a clean, testable, single-responsibility class.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AttributeValue:
    """Represents a collected attribute value."""

    name: str
    value: str
    is_skipped: bool = False
    confidence: float = 1.0


@dataclass
class AttributeRequest:
    """Represents a request for an attribute."""

    name: str
    question: str
    required: bool = True
    validation_pattern: Optional[str] = None


class AttributeCollector:
    """
    Simplified attribute collection with clear responsibilities:
    - Track collected vs missing attributes
    - Generate appropriate questions
    - Validate responses
    - Determine when collection is complete

    Replaces complex scattered logic from conversation_loop.py
    """

    def __init__(self, category: str, max_attributes: int = 3):
        self.category = category
        self.max_attributes = max_attributes
        self.collected_attributes: Dict[str, AttributeValue] = {}
        self.attribute_definitions = self._load_attribute_definitions(category)

    def _load_attribute_definitions(self, category: str) -> List[AttributeRequest]:
        """Load attribute definitions for category - centralized configuration."""
        definitions = {
            "printers": [
                AttributeRequest("budget", "Wat is je budget voor een printer?"),
                AttributeRequest("brand", "Heb je een voorkeur voor een bepaald merk?"),
                AttributeRequest(
                    "technology", "Welke printtechnologie prefereer je (inkjet/laser)?"
                ),
                AttributeRequest("connectivity", "Welke verbindingsopties wil je?"),
            ],
            "laptops": [
                AttributeRequest("budget", "Wat is je budget voor een laptop?"),
                AttributeRequest("brand", "Heb je een voorkeur voor een bepaald merk?"),
                AttributeRequest("screen_size", "Welke schermgrootte zoek je?"),
            ],
            "smartphones": [
                AttributeRequest("budget", "Wat is je budget voor een smartphone?"),
                AttributeRequest("brand", "Welk merk prefereer je?"),
                AttributeRequest("screen_size", "Welke schermgrootte wil je?"),
            ],
            "computers": [
                AttributeRequest("budget", "Wat is je budget voor een computer?"),
                AttributeRequest("brand", "Heb je een voorkeur voor een bepaald merk?"),
                AttributeRequest("processor", "Welke processor prefereer je?"),
            ],
        }
        return definitions.get(category, [])

    def get_next_question(self) -> Optional[AttributeRequest]:
        """
        Get the next attribute question to ask.

        Replaces complex _get_next_stage logic from conversation_loop.py
        """
        # Find first non-collected required attribute
        for attr_def in self.attribute_definitions:
            if attr_def.name not in self.collected_attributes:
                if (
                    attr_def.required
                    or len(self.collected_attributes) < self.max_attributes
                ):
                    return attr_def

        return None  # All required attributes collected

    def collect_attribute(self, attribute_name: str, response: str) -> AttributeValue:
        """
        Process and store an attribute response.

        Replaces complex reply processing from conversation_loop.py
        """
        # Handle "don't know" responses
        skip_responses = [
            "weet ik niet",
            "geen idee",
            "whatever",
            "maakt niet uit",
            "geen voorkeur",
            "doet er niet toe",
        ]

        is_skipped = response.lower().strip() in skip_responses

        # Validate response if not skipped
        if not is_skipped:
            response = self._validate_response(attribute_name, response)

        # Store the attribute
        attr_value = AttributeValue(
            name=attribute_name,
            value=response,
            is_skipped=is_skipped,
            confidence=0.5 if is_skipped else 1.0,
        )

        self.collected_attributes[attribute_name] = attr_value

        logger.info(
            f"Collected attribute: {attribute_name} = {response} (skipped: {is_skipped})"
        )

        return attr_value

    def _validate_response(self, attribute_name: str, response: str) -> str:
        """Validate and normalize attribute responses."""
        response = response.strip()

        # Budget validation and normalization
        if attribute_name == "budget":
            return self._normalize_budget(response)

        # Brand validation - capitalize first letter
        if attribute_name == "brand":
            return response.title()

        # Technology validation for printers
        if attribute_name == "technology":
            response_lower = response.lower()
            if "laser" in response_lower:
                return "laser"
            elif "inkjet" in response_lower or "inkt" in response_lower:
                return "inkjet"

        return response

    def _normalize_budget(self, budget_str: str) -> str:
        """Normalize budget input to consistent format."""
        budget_lower = budget_str.lower().strip()

        # Handle "minder dan X" format
        if "minder dan" in budget_lower:
            return budget_str  # Keep original format

        # Add euro symbol if missing
        if "€" not in budget_str and "euro" not in budget_lower:
            if budget_str.isdigit():
                return f"€{budget_str}"

        return budget_str

    def is_collection_complete(self) -> bool:
        """
        Determine if we have enough attributes to proceed.

        Replaces complex iteration and completion logic.
        """
        # Must have at least budget (most important)
        if "budget" not in self.collected_attributes:
            return False

        # Must have minimum number of attributes. The threshold should respect
        # the configured max_attributes (set by the conversation manager) and
        # the total number of defined attributes for the category.
        collected_count = len(
            [attr for attr in self.collected_attributes.values() if not attr.is_skipped]
        )

        required_min = min(self.max_attributes, len(self.attribute_definitions))
        return collected_count >= required_min

    def get_collection_summary(self) -> Dict[str, Any]:
        """Get summary of collected attributes for search/SQL generation."""
        summary = {
            "category": self.category,
            "total_collected": len(self.collected_attributes),
            "attributes": {},
        }

        for attr_name, attr_value in self.collected_attributes.items():
            if not attr_value.is_skipped:
                summary["attributes"][attr_name] = attr_value.value

        return summary

    def get_missing_attributes(self) -> List[str]:
        """Get list of missing required attributes."""
        missing = []
        for attr_def in self.attribute_definitions:
            if attr_def.required and attr_def.name not in self.collected_attributes:
                missing.append(attr_def.name)
        return missing

    def reset(self):
        """Reset collection state for new conversation."""
        self.collected_attributes.clear()


# Usage example - clean and simple:
"""
collector = AttributeCollector("printers")

# In conversation loop:
next_question = collector.get_next_question()
if next_question:
    # Ask user the question
    pass

# When reply received:
collector.collect_attribute("budget", "€150")

# Check if done:
if collector.is_collection_complete():
    summary = collector.get_collection_summary()
    # Use summary for search
"""


"""
Benefits of this extraction:

1. **Single Responsibility**: Only handles attribute collection
2. **Clear Interface**: Simple methods with obvious purposes  
3. **Testable**: Easy to unit test in isolation
4. **Configurable**: Centralized attribute definitions
5. **Maintainable**: Changes to attribute logic only affect this class
6. **Reusable**: Can be used by different conversation managers

Replaces ~100 lines of complex logic from conversation_loop.py
with ~150 lines of clean, focused, testable code.
"""
