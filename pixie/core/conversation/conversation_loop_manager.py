"""Lightweight, in-memory conversation loop with refinement and thresholds."""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

from ..llms.azure_filter_llm import AzureFilterLLM
from ..llms.azure_refinement_llm import AzureRefinementLLM
from ..utils.contracts import AskResponse
from ..utils.logging import conversation_context
from .llm_orchestrator import LLMOrchestrator
from .repository import ConversationRepository
from .state import ConversationState

logger = logging.getLogger(__name__)


class ConversationLoopManager:
    """Minimal multi-turn controller with in-memory state.

    - Start met vraag → LLM relevantie/categorie → query
    - Bij > threshold resultaten: stel vervolgvraag op best gerankte attribuut
    - Verwerk antwoorden als filters tot ≤ threshold of max vragen bereikt
    """

    def __init__(
        self,
        *,
        search_fn: Callable[[str, Optional[dict]], Dict[str, Any]],
        llm_orchestrator: LLMOrchestrator,
        refinement_llm: AzureRefinementLLM,
        filter_llm: AzureFilterLLM,
        repository: ConversationRepository,
        result_threshold: int = 3,
        max_questions: int = 2,
    ) -> None:
        self.search_fn = search_fn
        self.llm_orchestrator = llm_orchestrator
        self.refinement_llm = refinement_llm
        self.filter_llm = filter_llm
        self.repository = repository
        self.result_threshold = max(result_threshold, 1)
        self.max_questions = max(max_questions, 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def handle_new_question(self, question: str) -> AskResponse:
        self.repository.expire_stale()
        relevance = self.llm_orchestrator.check_relevance_and_category(question)
        if not relevance.success:
            return AskResponse(type="error", reason=relevance.error or "llm_failure")
        if not relevance.result.get("relevant"):
            return AskResponse(type="not_relevant", text="Not relevant")

        category = relevance.result.get("category")
        if not category:
            return AskResponse(type="error", reason="missing_category")

        try:
            results = self.search_fn(None, {"category": category})
        except Exception as exc:  # pragma: no cover
            logger.error("loop.search_failed", exc_info=exc)
            return AskResponse(type="error", reason="search_failed")

        items, metadata = self._normalise_results(results, category)
        total = self._total_count(metadata, items)
        if total <= self.result_threshold:
            return self._finalise_answer(items, metadata, None)

        prompt, attribute = self._build_refinement_prompt(
            category, metadata, total, asked=set()
        )
        if not prompt or not attribute:
            return self._finalise_answer(items, metadata, None)

        conv_id = str(uuid4())
        attr_name = attribute.get("name")
        asked = {attr_name.lower()} if attr_name else set()
        state = ConversationState(
            conversation_id=conv_id,
            category=category,
            filters=[],
            asked_attributes=asked,
            question_count=1,
            metadata=metadata,
            current_attribute=attribute,
        )
        with conversation_context(conv_id, 1):
            self.repository.create(state)
        return AskResponse(
            type="ask_user", prompt=prompt, conversation_id=conv_id
        )

    def handle_reply(self, conversation_id: str, reply: str) -> AskResponse:
        self.repository.expire_stale()
        state = self.repository.get(conversation_id)
        if not state:
            return AskResponse(
                type="error",
                reason="unknown_conversation",
                conversation_id=conversation_id,
            )

        with conversation_context(conversation_id, state.question_count + 1):
            category = state.category
            filters = list(state.filters)
            attribute = state.current_attribute or {}

            new_filters = self._build_filters_from_answer(attribute, reply)
            if new_filters:
                attr_name = attribute.get("name")
                if attr_name:
                    filters = [f for f in filters if f.get("name") != attr_name]
                filters.extend(new_filters)

            try:
                results = self.search_fn(None, {"category": category, "filters": filters})
            except Exception as exc:  # pragma: no cover
                logger.error("loop.search_failed", exc_info=exc)
                self.repository.delete(conversation_id)
                return AskResponse(
                    type="error",
                    reason="search_failed",
                    conversation_id=conversation_id,
                )

            items, metadata = self._normalise_results(results, category)
            total = self._total_count(metadata, items)
            if total <= self.result_threshold or state.question_count >= self.max_questions:
                self.repository.delete(conversation_id)
                return self._finalise_answer(items, metadata, conversation_id)

            prompt, next_attr = self._build_refinement_prompt(
                category, metadata, total, state.asked_attributes
            )
            if not prompt or not next_attr:
                self.repository.delete(conversation_id)
                return self._finalise_answer(items, metadata, conversation_id)

            state.filters = filters
            state.metadata = metadata
            state.current_attribute = next_attr
            state.question_count += 1
            next_name = next_attr.get("name")
            if next_name:
                state.asked_attributes.add(next_name.lower())
            self.repository.update(state)
            return AskResponse(
                type="ask_user", prompt=prompt, conversation_id=conversation_id
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _total_count(metadata: Dict[str, Any], items: List[dict]) -> int:
        total = metadata.get("count")
        return int(total) if isinstance(total, int) else len(items)

    def _normalise_results(self, payload: Any, category: str) -> Tuple[List[dict], Dict[str, Any]]:
        if isinstance(payload, dict):
            meta = {k: v for k, v in payload.items() if k != "results"}
            items = payload.get("results") or []
        else:
            meta = {"category": category}
            items = payload or []
        items = [it for it in items if isinstance(it, dict)]
        return items, meta

    def _format_results(self, items: List[dict], metadata: Dict[str, Any]) -> str:
        header = metadata.get("product_name") or metadata.get("category") or "producten"
        preferred = metadata.get("preferred_columns") or []
        lines = [f"Resultaten voor {header}:"]
        for item in items[:3]:
            show: list[tuple[str, Any]] = []
            for col in preferred:
                val = item.get(col)
                if val not in (None, ""):
                    show.append((col, val))
                if len(show) == 3:
                    break
            if not show:
                for k, v in item.items():
                    if k in {"id", "created_at", "updated_at", "product_name"} or v in (None, ""):
                        continue
                    show.append((k, v))
                    if len(show) == 3:
                        break
            if not show:
                lines.append("- (geen details)")
                continue
            parts = [f"{c.replace('_',' ')}: {v}" for c, v in show]
            lines.append(f"- {' | '.join(parts)}")
        total = metadata.get("total")
        if isinstance(total, int):
            lines.append(f"Totaal gevonden: {total}")
        return "\n".join(lines)

    def _finalise_answer(
        self, items: List[dict], metadata: Dict[str, Any], conversation_id: Optional[str]
    ) -> AskResponse:
        text = self._format_results(items, metadata) if items else "Geen producten gevonden"
        return AskResponse(
            type="answer" if items else "no_results",
            text=text,
            conversation_id=conversation_id,
        )

    def _build_refinement_prompt(
        self, category: str, metadata: Dict[str, Any], count: int, asked: set[str]
    ) -> Tuple[Optional[str], Optional[dict]]:
        product_name = metadata.get("product_name") or category or "producten"
        attribute = self._select_attribute(metadata, asked)
        if not attribute:
            return None, None

        attr = dict(attribute)
        name = attr.get("name")
        label = (name or "het product").replace("_", " ")
        attr_type = (attr.get("type") or "").lower()
        q1, q3 = attr.get("q1"), attr.get("q3")
        values = attr.get("values")

        options: list[str] = []
        if (
            attr_type in {"continuous", "numeric"}
            and isinstance(q1, (int, float))
            and isinstance(q3, (int, float))
            and q1 < q3
        ):
            low = self._friendly_round(q1)
            high = self._friendly_round(q3)
            options = [
                f"minder dan {self._format_numeric_value(low)}",
                f"tussen {self._format_numeric_value(low)} en {self._format_numeric_value(high)}",
                f"meer dan {self._format_numeric_value(high)}",
            ]
            attr["options"] = options + ["weet ik niet"]
            attr.setdefault("examples", options[:3])
        elif attr_type == "boolean":
            attr["options"] = ["ja", "nee", "weet ik niet"]
            attr.setdefault("examples", ["ja", "nee"])
        elif attr_type == "categorical" and isinstance(values, list):
            sample_values = [str(v) for v in values if v][:5]
            if sample_values:
                attr["options"] = sample_values + ["weet ik niet"]
                attr.setdefault("examples", sample_values)

        ctx = {"category": product_name, "attribute": attr, "count": count, "asked_attributes": sorted(asked)}

        question = None
        try:
            question = self.refinement_llm.generate_question(ctx)
        except Exception as exc:  # pragma: no cover
            logger.error("loop.refinement_failed", exc_info=exc)
            question = None

        if not question:
            fallback = (
                f"Ik heb {count} resultaten voor {product_name}. Wat vind je belangrijk aan {label}? "
                "Je mag ook laten weten dat je het nog niet weet."
            )
            return fallback, attr
        return question, attr

    def _select_attribute(self, metadata: Dict[str, Any], asked: set[str]) -> Optional[dict]:
        options = metadata.get("attribute_options") or []
        for entry in options:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if not name or name.lower() in asked:
                continue
            return {
                "name": name,
                "description": entry.get("description"),
                "type": entry.get("type"),
                "q1": entry.get("q1"),
                "q3": entry.get("q3"),
                "values": entry.get("values"),
            }
        return None

    def _build_filters_from_answer(self, attribute: Dict[str, Any], reply: str) -> List[Dict[str, Any]]:
        # Try LLM first
        filters = self.filter_llm.build_filters(reply, attribute) if self.filter_llm else []
        if filters:
            return filters
        # Minimal fallback parsing
        reply_text = reply.strip()
        reply_lower = reply_text.lower()

        if not reply_text:
            return []

        name = attribute.get("name")
        if not name:
            return []
        attr_type = (attribute.get("type") or "").lower()
        out: List[Dict[str, Any]] = []
        if attr_type in {"continuous", "numeric"}:
            q1, q3 = attribute.get("q1"), attribute.get("q3")
            if isinstance(q1, (int, float)) and isinstance(q3, (int, float)):
                if "minder" in reply_lower or "onder" in reply_lower:
                    out.append({"name": name, "type": "range", "min_value": None, "max_value": q1})
                elif "meer" in reply_lower or "boven" in reply_lower:
                    out.append({"name": name, "type": "range", "min_value": q3, "max_value": None})
                elif "tussen" in reply_lower and "en" in reply_lower:
                    out.append({"name": name, "type": "range", "min_value": q1, "max_value": q3})
                else:
                    num = self._extract_number(reply_lower)
                    if num is not None:
                        span = max(num * 0.1, 1)
                        out.append({"name": name, "type": "range", "min_value": max(0, num - span), "max_value": num + span})
        elif attr_type == "boolean":
            if any(w in reply_lower for w in ["ja", "wel", "true", "aan"]):
                out.append({"name": name, "type": "exact", "value": True})
            elif any(w in reply_lower for w in ["nee", "niet", "false", "uit"]):
                out.append({"name": name, "type": "exact", "value": False})
        elif attr_type == "categorical":
            vals = attribute.get("values")
            val = self._match_value(reply_lower, vals) if vals else None
            if val:
                out.append({"name": name, "type": "exact", "value": val})
        return out

    @staticmethod
    def _friendly_round(value: float) -> float:
        abs_val = abs(value)
        if abs_val >= 1000:
            rounded = round(value / 50) * 50
        elif abs_val >= 100:
            rounded = round(value / 10) * 10
        elif abs_val >= 10:
            rounded = round(value)
        elif abs_val >= 1:
            rounded = round(value)
        else:
            rounded = round(value, 1)
        return float(int(rounded)) if abs(rounded - int(rounded)) < 0.01 else float(rounded)

    @staticmethod
    def _format_numeric_value(value: float) -> str:
        return str(int(value)) if abs(value - int(value)) < 0.01 else f"{value:.1f}".rstrip("0").rstrip(".")

    @staticmethod
    def _extract_number(text: str) -> Optional[float]:
        m = re.search(r"(\d+[\d.,]*)", text)
        if not m:
            return None
        num = m.group(0).replace(".", "").replace(",", ".")
        try:
            return float(num)
        except ValueError:
            return None

    @staticmethod
    def _match_value(reply_lower: str, values: Any) -> Optional[str]:
        if not isinstance(values, list):
            return None
        for v in values:
            if v is None:
                continue
            s = str(v)
            if s.lower() in reply_lower:
                return s
        return None
