"""Lightweight, in-memory conversation loop with refinement and thresholds."""

from __future__ import annotations

import logging
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

        base_items, base_metadata = self._normalise_results(results, category)
        base_total = self._total_count(base_metadata, base_items)
        items, metadata = base_items, base_metadata
        total = base_total

        initial_filters: List[Dict[str, Any]] = []
        answered_attributes: set[str] = set()
        if self.filter_llm:
            try:
                initial_filters = self._derive_filters_from_question(question, metadata)
            except Exception:  # pragma: no cover - defensive
                logger.warning("initial_filter_derivation_failed", exc_info=True)
                initial_filters = []
            if initial_filters:
                answered_attributes = {
                    str(name).lower()
                    for name in (flt.get("name") for flt in initial_filters)
                    if isinstance(name, str) and name
                }
                try:
                    results = self.search_fn(
                        None, {"category": category, "filters": initial_filters}
                    )
                except Exception as exc:  # pragma: no cover
                    logger.error("loop.initial_filter_search_failed", exc_info=exc)
                    return AskResponse(type="error", reason="search_failed")
                items, metadata = self._normalise_results(results, category)
                total = self._total_count(metadata, items)
                if total == 0:
                    logger.info(
                        "loop.initial_filters_no_hits",
                        extra={"filters": initial_filters, "question": question},
                    )
                    items, metadata, total = base_items, base_metadata, base_total
                    initial_filters = []
                    # Keep answered_attributes so we do not ask again,
                    # even though the filter could not be applied reliably.

        if total <= self.result_threshold:
            return self._finalise_answer(items, metadata, None)

        prompt, attribute = self._build_refinement_prompt(
            category,
            metadata,
            items,
            total,
            asked=answered_attributes,
            filters=initial_filters,
        )
        if not prompt or not attribute:
            return self._finalise_answer(items, metadata, None)

        conv_id = str(uuid4())
        attr_name = attribute.get("name")
        asked = set(answered_attributes)
        if attr_name:
            asked.add(attr_name.lower())
        state = ConversationState(
            conversation_id=conv_id,
            category=category,
            filters=initial_filters,
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
            category, metadata, items, total, state.asked_attributes, filters
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
        self,
        category: str,
        metadata: Dict[str, Any],
        items: List[dict],
        count: int,
        asked: set[str],
        filters: Optional[List[Dict[str, Any]]],
    ) -> Tuple[Optional[str], Optional[dict]]:
        product_name = metadata.get("product_name") or category or "producten"
        attribute = self._select_attribute(metadata, asked, items)
        if not attribute:
            return None, None

        attr = dict(attribute)
        label = self._attribute_label(attr)
        attr["label"] = label
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

        ctx = {
            "category": product_name,
            "attribute": attr,
            "count": count,
            "asked_attributes": sorted(asked),
            "applied_filters": filters or [],
        }

        question = None
        try:
            question = self.refinement_llm.generate_question(ctx)
        except Exception as exc:  # pragma: no cover
            logger.error("loop.refinement_failed", exc_info=exc)
            question = None

        if not question:
            return None, None
        question_text = question.strip()
        if not question_text:
            return None, None
        return question_text, attr

    def _select_attribute(
        self, metadata: Dict[str, Any], asked: set[str], items: List[dict]
    ) -> Optional[dict]:
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
                collected = self._collect_attribute_values(items, name)
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

    def _derive_filters_from_question(
        self, question: str, metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        attribute_options = metadata.get("attribute_options") or []
        collected: dict[tuple[str, str], Dict[str, Any]] = {}
        for attribute in attribute_options:
            if not isinstance(attribute, dict):
                continue
            filters = self._build_filters_from_answer(attribute, question)
            for flt in filters:
                key = (flt.get("name"), flt.get("type"))
                if key[0] and key not in collected:
                    collected[key] = flt
        return list(collected.values())

    def _build_filters_from_answer(
        self,
        attribute: Dict[str, Any],
        reply: str,
    ) -> List[Dict[str, Any]]:
        reply_text = (reply or "").strip()
        if not reply_text:
            return []

        if not self.filter_llm:
            return []

        try:
            raw_filters = self.filter_llm.build_filters(reply_text, attribute) or []
        except Exception:  # pragma: no cover - defensive
            logger.warning("filter_llm_failed_to_parse", exc_info=True)
            return []

        name = attribute.get("name")
        if not name:
            return []

        valid: List[Dict[str, Any]] = []
        for item in raw_filters:
            if isinstance(item, dict) and item.get("name") == name:
                valid.append(item)
        return valid

    @staticmethod
    def _attribute_label(attribute: Dict[str, Any]) -> str:
        name = attribute.get("name")
        if not name:
            return "het product"
        return str(name).replace("_", " ")

    @staticmethod
    def _collect_attribute_values(items: List[dict], attribute_name: str) -> List[str]:
        seen: set[str] = set()
        ordered: List[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            value = item.get(attribute_name)
            if value in (None, "", []):
                continue
            if isinstance(value, list):
                candidates = value
            else:
                candidates = [value]
            for candidate in candidates:
                text = str(candidate).strip()
                if not text:
                    continue
                lowered = text.lower()
                if lowered not in seen:
                    seen.add(lowered)
                    ordered.append(text)
        return ordered

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
        if abs(value - int(value)) < 0.01:
            return str(int(value))
        formatted = f"{value:.1f}".rstrip("0").rstrip(".")
        return formatted
