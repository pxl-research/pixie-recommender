import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AttributeValue:
    name: str
    value: str
    is_skipped: bool = False
    confidence: float = 1.0


@dataclass
class AttributeRequest:
    name: str
    question: str
    required: bool = True
    validation_pattern: Optional[str] = None


class AttributeCollector:
    def __init__(self, category: str, max_attributes: int = 3) -> None:
        self.category = category
        self.max_attributes = max_attributes
        self.collected_attributes: Dict[str, AttributeValue] = {}
        self.attribute_definitions = self._load_attribute_definitions(category)

    def _load_attribute_definitions(self, category: str) -> List[AttributeRequest]:
        logger.warning("TODO: load attribute definitions from dataset", extra={"category": category})
        return []

    def get_next_question(self) -> Optional[AttributeRequest]:
        for definition in self.attribute_definitions:
            if definition.name not in self.collected_attributes:
                if definition.required or len(self.collected_attributes) < self.max_attributes:
                    return definition
        return None

    def collect_attribute(self, attribute_name: str, response: str) -> AttributeValue:
        skip_responses = {
            "weet ik niet",
            "geen idee",
            "whatever",
            "maakt niet uit",
            "geen voorkeur",
            "doet er niet toe",
        }
        normalized = response.strip()
        is_skipped = normalized.lower() in skip_responses
        if not is_skipped:
            normalized = self._validate_response(attribute_name, normalized)
        value = AttributeValue(
            name=attribute_name,
            value=normalized,
            is_skipped=is_skipped,
            confidence=0.5 if is_skipped else 1.0,
        )
        self.collected_attributes[attribute_name] = value
        return value

    def _validate_response(self, attribute_name: str, response: str) -> str:
        if attribute_name == "budget":
            return self._normalize_budget(response)
        if attribute_name == "brand":
            return response.title()
        if attribute_name == "technology":
            lowered = response.lower()
            if "laser" in lowered:
                return "laser"
            if "ink" in lowered or "inkt" in lowered:
                return "inkjet"
        return response

    def _normalize_budget(self, budget: str) -> str:
        text = budget.lower().replace("€", "").strip()
        if text.startswith("minder dan"):
            number = text.replace("minder dan", "").strip()
            return f"< {number}"
        if text.endswith("euro"):
            return text.replace("euro", "").strip()
        if text.endswith("euros"):
            return text.replace("euros", "").strip()
        return text

    def is_collection_complete(self) -> bool:
        required = {d.name for d in self.attribute_definitions if d.required}
        collected = set(self.collected_attributes)
        return required.issubset(collected)

    def get_collection_summary(self) -> Dict[str, Any]:
        summary: Dict[str, Any] = {}
        for name, value in self.collected_attributes.items():
            if value.is_skipped:
                continue
            summary[name] = value.value
        return summary
