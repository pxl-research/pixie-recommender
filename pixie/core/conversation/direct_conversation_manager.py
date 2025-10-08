"""Single-pass conversation handler that relies on the LLMs to produce SQL."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..llms.azure_filter_llm import AzureFilterLLM
from ..llms.azure_refinement_llm import AzureRefinementLLM
from ..utils.contracts import AskResponse
from .llm_orchestrator import LLMOrchestrator

logger = logging.getLogger(__name__)


class DirectConversationManager:
    """Conversation layer that delegates orchestration and manages refinements."""

    def __init__(
        self,
        search_fn,
        llm_orchestrator: LLMOrchestrator,
        refinement_llm: AzureRefinementLLM,
        filter_llm: AzureFilterLLM,
        *,
        result_threshold: int = 3,
        max_questions: int = 2,
    ) -> None:
        self.search_fn = search_fn
        self.llm_orchestrator = llm_orchestrator
        self.refinement_llm = refinement_llm
        self.filter_llm = filter_llm
        self.result_threshold = max(result_threshold, 1)
        self.max_questions = max(max_questions, 1)
        self._pending_questions: dict[str, dict[str, Any]] = {}

    def handle_new_question(self, question: str) -> AskResponse:
        logger.info("question", extra={"question": question})
        relevance = self.llm_orchestrator.check_relevance_and_category(question)
        if not relevance.success:
            return AskResponse(type="error", reason="llm_failure")
        if not relevance.result["relevant"]:
            return AskResponse(type="not_relevant", text="Not relevant")

        category = relevance.result["category"]
        if not category:
            return AskResponse(type="error", reason="missing_category")

        sql_result = self.llm_orchestrator.generate_search_query(question, {}, category)
        if not sql_result.success:
            return AskResponse(type="error", reason="search_failed")

        sql_query = sql_result.result.get("sql") if sql_result.result else None
        if not sql_query:
            return AskResponse(type="error", reason="search_failed")

        try:
            results = self.search_fn(sql_query, {"category": category})
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("search_failed", exc_info=exc)
            return AskResponse(type="error", reason="search_failed")

        items, metadata = self._normalise_results(results, category)
        total = self._total_count(metadata, items)

        if total > self.result_threshold:
            asked: set[str] = set()
            question_text, attribute_info = self._build_refinement_prompt(
                category, metadata, total, asked
            )
            if not question_text or not attribute_info:
                return self._finalise_answer(items, metadata)

            pending_id = str(uuid4())
            asked.add(attribute_info["name"].lower())
            self._pending_questions[pending_id] = {
                "category": category,
                "metadata": metadata,
                "sql": sql_query,
                "filters": [],
                "asked": asked,
                "question_count": 1,
                "current_attribute": attribute_info,
            }
            return AskResponse(
                type="ask_user", prompt=question_text, pending_id=pending_id
            )

        return self._finalise_answer(items, metadata)

    def handle_reply(self, pending_id: str, reply: str) -> AskResponse:
        logger.info("reply", extra={"pending_id": pending_id, "reply": reply})
        context = self._pending_questions.get(pending_id)
        if context is None:
            return AskResponse(type="error", reason="unknown_pending_id")

        category = context["category"]
        sql_query = context["sql"]
        filters: List[dict[str, Any]] = context.setdefault("filters", [])
        asked: set[str] = context.setdefault("asked", set())
        question_count = context.get("question_count", 1)
        attribute_info = context.get("current_attribute")

        if attribute_info:
            new_filters = self._build_filters_from_answer(attribute_info, reply)
            logger.info(
                "filter_building_result",
                extra={
                    "attribute": attribute_info.get("name"),
                    "reply": reply,
                    "new_filters": new_filters,
                },
            )
            if new_filters:
                attr_name = attribute_info.get("name")
                filters[:] = [f for f in filters if f.get("name") != attr_name]
                filters.extend(new_filters)
                logger.info(
                    "filters_updated",
                    extra={
                        "attribute": attr_name,
                        "reply": reply,
                        "new_filters": new_filters,
                        "all_filters": filters,
                    },
                )

        try:
            results = self.search_fn(
                sql_query, {"category": category, "filters": filters}
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("search_failed", exc_info=exc)
            self._pending_questions.pop(pending_id, None)
            return AskResponse(type="error", reason="search_failed")

        items, metadata = self._normalise_results(results, category)
        total = self._total_count(metadata, items)

        if total <= self.result_threshold or question_count >= self.max_questions:
            self._pending_questions.pop(pending_id, None)
            return self._finalise_answer(items, metadata)

        asked = set(asked)
        question_text, next_attribute = self._build_refinement_prompt(
            category, metadata, total, asked
        )
        if not question_text or not next_attribute:
            self._pending_questions.pop(pending_id, None)
            return self._finalise_answer(items, metadata)

        asked.add(next_attribute["name"].lower())
        context.update(
            {
                "metadata": metadata,
                "question_count": question_count + 1,
                "current_attribute": next_attribute,
                "asked": asked,
            }
        )
        return AskResponse(type="ask_user", prompt=question_text, pending_id=pending_id)

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _finalise_answer(
        self, items: list[dict[str, Any]], metadata: Dict[str, Any]
    ) -> AskResponse:
        if items:
            return AskResponse(
                type="answer", text=self._format_results(items, metadata)
            )
        return AskResponse(type="no_results", text="Geen producten gevonden")

    @staticmethod
    def _total_count(metadata: Dict[str, Any], items: list[dict[str, Any]]) -> int:
        total = metadata.get("count")
        if isinstance(total, int):
            return total
        return len(items)

    def _normalise_results(
        self, payload: Any, category: str
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if isinstance(payload, dict):
            metadata = {k: v for k, v in payload.items() if k != "results"}
            items = payload.get("results") or []
        else:
            metadata = {"category": category}
            items = payload or []
        items = [item for item in items if isinstance(item, dict)]
        return items, metadata

    def _format_results(
        self, items: list[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> str:
        header = metadata.get("product_name") or metadata.get("category") or "producten"
        preferred_columns = metadata.get("preferred_columns") or []
        lines = [f"Resultaten voor {header}:"]

        for item in items[:3]:
            columns_to_show: list[tuple[str, Any]] = []
            for column in preferred_columns:
                value = item.get(column)
                if value in (None, ""):
                    continue
                columns_to_show.append((column, value))
                if len(columns_to_show) == 3:
                    break

            if not columns_to_show:
                for key, value in item.items():
                    if key in {"id", "created_at", "updated_at", "product_name"}:
                        continue
                    if value in (None, ""):
                        continue
                    columns_to_show.append((key, value))
                    if len(columns_to_show) == 3:
                        break

            if not columns_to_show:
                lines.append("- (geen details)")
                continue

            formatted = []
            for column, value in columns_to_show:
                label = column.replace("_", " ")
                formatted.append(f"{label}: {value}")

            lines.append(f"- {' | '.join(formatted)}")

        total = metadata.get("total")
        if isinstance(total, int):
            lines.append(f"Totaal gevonden: {total}")
        return "\n".join(lines)

    def _build_refinement_prompt(
        self,
        category: str,
        metadata: Dict[str, Any],
        count: int,
        asked: set[str],
    ) -> tuple[Optional[str], Optional[dict[str, Any]]]:
        product_name = metadata.get("product_name") or category or "producten"
        attribute_info = self._select_attribute(metadata, asked)
        if attribute_info is None:
            return None, None

        attribute_data = dict(attribute_info)
        attr_name = attribute_data.get("name")
        label = (attr_name or "het product").replace("_", " ")
        attr_type = (attribute_data.get("type") or "").lower()
        q1 = attribute_data.get("q1")
        q3 = attribute_data.get("q3")
        unit = "€" if attr_name and "prijs" in attr_name.lower() else ""

        options_labels: list[str] = []
        if (
            attr_type in {"continuous", "numeric"}
            and isinstance(q1, (int, float))
            and isinstance(q3, (int, float))
            and q1 < q3
        ):
            low = self._friendly_round(q1)
            high = self._friendly_round(q3)
            formatted_low = self._format_numeric_value(low)
            formatted_high = self._format_numeric_value(high)
            options_labels = [
                f"minder dan {unit}{formatted_low}".strip(),
                f"tussen {unit}{formatted_low} en {unit}{formatted_high}".strip(),
                f"meer dan {unit}{formatted_high}".strip(),
            ]
            attribute_data["options"] = options_labels + ["weet ik niet"]

        context = {
            "category": product_name,
            "attribute": attribute_data,
        }

        question = None
        try:
            question = self.refinement_llm.generate_question(context)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("refinement_failed", exc_info=exc)
            question = None

        if not question:
            if options_labels:
                options_line = ", ".join(options_labels + ["'weet ik niet'"])
                question = (
                    f"Ik heb {count} resultaten voor {product_name}. "
                    "Kies een optie of geef je eigen antwoord.\n"
                    f"Antwoordopties: {options_line}"
                )
            else:
                question = (
                    f"Ik heb {count} resultaten voor {product_name}. "
                    f"Welk detail over {label} is voor jou het belangrijkst?"
                )

        return question, attribute_data

    def _select_attribute(
        self, metadata: Dict[str, Any], asked: set[str]
    ) -> Optional[dict[str, Any]]:
        options = metadata.get("attribute_options") or []
        for entry in options:
            name = entry.get("name")
            if not name:
                continue
            if name.lower() in asked:
                continue
            info = {
                "name": name,
                "description": entry.get("description"),
                "type": entry.get("type"),
                "q1": entry.get("q1"),
                "q3": entry.get("q3"),
                "values": entry.get("values"),
            }
            return info
        return None

    def _build_filters_from_answer(
        self, attribute: Dict[str, Any], reply: str
    ) -> List[Dict[str, Any]]:
        """Convert user reply to structured filters using the filter LLM."""
        return self.filter_llm.build_filters(reply, attribute)

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
        if abs(rounded - int(rounded)) < 0.01:
            return float(int(rounded))
        return float(rounded)

    @staticmethod
    def _format_numeric_value(value: float) -> str:
        if abs(value - int(value)) < 0.01:
            return str(int(value))
        text = f"{value:.1f}".rstrip("0").rstrip(".")
        return text

    @staticmethod
    def _extract_number(text: str) -> Optional[float]:
        match = re.search(r"(\d+[\d.,]*)", text)
        if not match:
            return None
        value_str = match.group(0).replace(".", "").replace(",", ".")
        try:
            return float(value_str)
        except ValueError:
            return None

    @staticmethod
    def _match_value(reply_lower: str, values: Any) -> Optional[str]:
        if not isinstance(values, list):
            return None
        for value in values:
            if value is None:
                continue
            value_str = str(value)
            if value_str.lower() in reply_lower:
                return value_str
        return None
