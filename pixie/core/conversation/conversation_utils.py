"""Utility helpers for search and attribute reasoning."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

"""Utility helpers for search results and attribute reasoning in the conversation flow."""

Filters = List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SearchResult:
    """Normalised output of a search call used throughout the conversation flow."""

    items: List[dict]
    metadata: Dict[str, Any]
    total: int


def normalise_search_response(payload: Any, category: str) -> SearchResult:
    """Convert raw search responses into a ``SearchResult`` instance."""
    if isinstance(payload, dict):
        metadata = {k: v for k, v in payload.items() if k != "results"}
        items = payload.get("results") or []
    else:
        metadata = {"category": category}
        items = payload or []
    items = [it for it in items if isinstance(it, dict)]

    raw_total = metadata.get("count")
    total = int(raw_total) if isinstance(raw_total, int) else len(items)
    metadata.setdefault("count", total)
    return SearchResult(items=items, metadata=metadata, total=total)


def attribute_label(attribute: Dict[str, Any]) -> str:
    """Create a readable label for an attribute dictionary."""
    name = attribute.get("name")
    if not name:
        return "het product"
    return str(name).replace("_", " ")


def collect_attribute_values(items: List[dict], attribute_name: str) -> List[str]:
    """Collect distinct values for ``attribute_name`` across the given items."""
    seen: Set[str] = set()
    ordered: List[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        value = item.get(attribute_name)
        if value in (None, "", []):
            continue
        values = value if isinstance(value, list) else [value]
        for entry in values:
            text = str(entry).strip()
            if not text:
                continue
            lowered = text.lower()
            if lowered not in seen:
                seen.add(lowered)
                ordered.append(text)
    return ordered


def select_attribute_for_refinement(
    metadata: Dict[str, Any], asked: Set[str], items: List[dict]
) -> Optional[dict]:
    """Pick the next attribute to ask about based on metadata and current results."""
    options = metadata.get("attribute_options") or []
    for entry in options:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not name or name.lower() in asked:
            continue

        attr_type = (entry.get("type") or "").lower()
        values = entry.get("values")
        available_values: Optional[List[str]] = None

        if attr_type == "categorical":
            collected = collect_attribute_values(items, name)
            metadata_values = [str(v) for v in (values or []) if v]
            if collected and len(collected) >= 2:
                available_values = collected
            elif collected and len(collected) == 1:
                if len(metadata_values) > 1:
                    available_values = metadata_values
                else:
                    continue
            elif len(metadata_values) > 1:
                available_values = metadata_values
            else:
                continue

        prepared = {
            "name": name,
            "description": entry.get("description"),
            "type": entry.get("type"),
            "q1": entry.get("q1"),
            "q3": entry.get("q3"),
            "values": available_values if available_values is not None else values,
        }
        return prepared
    return None


# ---------------------------------------------------------------------------
# Structured result preparation
# ---------------------------------------------------------------------------

_NAME_KEYS = ["name", "product_name", "title"]
_DESCRIPTION_KEYS = ["description", "short_description", "omschrijving"]
_BRAND_KEYS = ["brand", "merk"]
_PRICE_KEYS = ["price", "unit_price", "prijs", "price_value", "cost"]
_AVAILABILITY_KEYS = [
    "availability",
    "availability_status",
    "stock_status",
    "in_stock",
    "beschikbaarheid",
    "beschikbaar",
]


def _extract_value(item: dict, keys: List[str]) -> Tuple[Optional[str], Any]:
    """Return the first non-empty value for the provided keys."""
    for key in keys:
        if key not in item:
            continue
        value = item.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                continue
            return key, stripped
        if value == "" or value == []:
            continue
        return key, value
    return None, None


def _extract_price_value(item: dict) -> Optional[float]:
    """Parse a price-like value to a float for sorting."""
    _, raw = _extract_value(item, _PRICE_KEYS)
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        cleaned = re.sub(r"[^\d,.\-]", "", raw)
        if not cleaned:
            return None
        if cleaned.count(",") == 1 and cleaned.count(".") == 0:
            cleaned = cleaned.replace(",", ".")
        elif cleaned.count(",") > 1 and cleaned.count(".") == 0:
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _normalise_attribute_value(value: Any) -> Any:
    """Convert attribute values to serialisable primitives."""
    if isinstance(value, list):
        return [v for v in value if v not in (None, "")]
    if isinstance(value, str):
        return value.strip()
    return value


def _select_top_attributes(
    item: dict,
    metadata: Dict[str, Any],
    exclude: Set[str],
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """Pick the highest-ranked attribute values present on the item."""
    options = metadata.get("attribute_options") or []
    selected: List[Dict[str, Any]] = []
    for option in options:
        if not isinstance(option, dict):
            continue
        name = option.get("name")
        if not isinstance(name, str):
            continue
        lowered = name.lower()
        if lowered in exclude:
            continue
        if name not in item:
            continue
        value = item.get(name)
        if value in (None, "", []):
            continue
        normalised = _normalise_attribute_value(value)
        if normalised in (None, "", []):
            continue
        selected.append(
            {
                "name": name,
                "label": attribute_label(option),
                "value": normalised,
            }
        )
        if len(selected) >= limit:
            break
    return selected


def build_structured_summary(
    result: SearchResult,
    result_threshold: int,
    *,
    max_ranked: int = 5,
) -> Dict[str, Any]:
    """Create a structured summary containing the most relevant result entries."""
    items = list(result.items)
    if not items:
        return {"total": result.total, "count": 0, "items": []}

    if result.total <= result_threshold:
        count = min(len(items), result.total)
        selected_items = items[:count]
        sort_applied = None
    else:
        top_n = min(len(items), max_ranked)
        sorted_items = sorted(
            items,
            key=lambda entry: (
                0 if _extract_price_value(entry) is not None else 1,
                _extract_price_value(entry) or float("inf"),
            ),
        )
        selected_items = sorted_items[:top_n]
        sort_applied = {"field": "price", "order": "asc", "fallback": "original"}

    summaries: List[Dict[str, Any]] = []
    for entry in selected_items:
        summary: Dict[str, Any] = {}
        used_keys: Set[str] = set()

        name_key, name_val = _extract_value(entry, _NAME_KEYS)
        if name_val is not None:
            summary["name"] = name_val
        if name_key:
            used_keys.add(name_key.lower())

        desc_key, desc_val = _extract_value(entry, _DESCRIPTION_KEYS)
        if desc_val is not None:
            summary["description"] = desc_val
        if desc_key:
            used_keys.add(desc_key.lower())

        brand_key, brand_val = _extract_value(entry, _BRAND_KEYS)
        if brand_val is not None:
            summary["brand"] = brand_val
        if brand_key:
            used_keys.add(brand_key.lower())

        price_key, price_val = _extract_value(entry, _PRICE_KEYS)
        if price_val is not None:
            summary["price"] = price_val
        if price_key:
            used_keys.add(price_key.lower())

        availability_key, availability_val = _extract_value(entry, _AVAILABILITY_KEYS)
        if availability_val is not None:
            summary["availability"] = availability_val
        if availability_key:
            used_keys.add(availability_key.lower())

        additional = _select_top_attributes(
            entry,
            result.metadata,
            exclude=used_keys,
            limit=3,
        )
        if additional:
            summary["attributes"] = additional

        summaries.append(summary)

    payload: Dict[str, Any] = {
        "total": result.total,
        "count": len(summaries),
        "items": summaries,
    }
    if sort_applied:
        payload["sorted_by"] = sort_applied
    return payload
