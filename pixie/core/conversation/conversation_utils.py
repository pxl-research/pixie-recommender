"""Utility helpers for search and attribute reasoning."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

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


def format_result_text(result: SearchResult) -> str:
    """Render the top items in ``result`` into a human-friendly summary string."""
    metadata = result.metadata
    header = metadata.get("product_name") or metadata.get("category") or "producten"
    preferred = metadata.get("preferred_columns") or []
    lines = [f"Resultaten voor {header}:"]

    for item in result.items[:3]:
        show: List[tuple[str, Any]] = []
        for col in preferred:
            val = item.get(col)
            if val not in (None, ""):
                show.append((col, val))
            if len(show) == 3:
                break
        if not show:
            for key, value in item.items():
                if key in {"id", "created_at", "updated_at", "product_name"} or value in (None, ""):
                    continue
                show.append((key, value))
                if len(show) == 3:
                    break
        if not show:
            lines.append("- (geen details)")
            continue
        formatted = [f"{col.replace('_', ' ')}: {value}" for col, value in show]
        lines.append(f"- {' | '.join(formatted)}")

    total = metadata.get("total")
    if isinstance(total, int):
        lines.append(f"Totaal gevonden: {total}")
    return "\n".join(lines)


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
