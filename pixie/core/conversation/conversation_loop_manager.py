"""Repository-backed manager for the multi-turn conversation loop."""

from __future__ import annotations

import logging
import re
from contextlib import contextmanager
from contextvars import Token
from datetime import datetime
from typing import Any, Callable, Dict, Iterator, Optional, Tuple
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from ..llms.azure_filter_llm import AzureFilterLLM
from ..llms.azure_refinement_llm import AzureRefinementLLM
from ..utils.contracts import AskResponse
from ..utils.logging import conversation_id_ctx, turn_index_ctx
from .conversation_action import ConversationAction
from .conversation_repository import ConversationRepository
from .conversation_state import ConversationState
from .llm_orchestrator import LLMOrchestrator

logger = logging.getLogger(__name__)

_BRUSSELS_TZ = ZoneInfo("Europe/Brussels")


def _now_brussels() -> datetime:
    return datetime.now(tz=_BRUSSELS_TZ)


class ConversationLoopManager:
    """High-level conversation controller that persists state between turns."""

    def __init__(
        self,
        *,
        search_fn: Callable[[Optional[dict]], Any],
        llm_orchestrator: LLMOrchestrator,
        refinement_llm: AzureRefinementLLM,
        filter_llm: AzureFilterLLM,
        result_threshold: int = 3,
        max_questions: int = 2,
        conversation_repository: ConversationRepository | None = None,
    ) -> None:
        self.search_fn = search_fn
        self.llm_orchestrator = llm_orchestrator
        self.refinement_llm = refinement_llm
        self.filter_llm = filter_llm
        self.result_threshold = max(result_threshold, 1)
        self.max_questions = max(max_questions, 1)
        self.conversation_repository = conversation_repository or ConversationRepository()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_new_question(self, question: str) -> AskResponse:
        conversation_uuid = uuid4()
        conversation_id = str(conversation_uuid)
        state = ConversationState(conversation_id=conversation_uuid)
        state.turns.append(question)
        state.status = "processing"
        state.question_count = 0

        with self._logging_context(conversation_id=conversation_id, turn_index=0):
            logger.info(
                "loop.question",
                extra={"conversation_id": conversation_id, "question": question},
            )

        relevance = self.llm_orchestrator.check_relevance_and_category(question)
        if not relevance.success:
            state.status = "error"
            state.last_action = ConversationAction.END.name
            self._store_new_state(state)
            return AskResponse(
                type="error",
                reason=relevance.error or "llm_failure",
                conversation_id=conversation_id,
            )

        if not relevance.result.get("relevant"):
            state.status = "not_relevant"
            state.last_action = ConversationAction.END.name
            self._store_new_state(state)
            return AskResponse(
                type="not_relevant",
                text="Not relevant",
                conversation_id=conversation_id,
            )

        category = relevance.result.get("category")
        if not category:
            state.status = "error"
            state.last_action = ConversationAction.END.name
            self._store_new_state(state)
            return AskResponse(
                type="error",
                reason="missing_category",
                conversation_id=conversation_id,
            )

        try:
            results = self.search_fn({"category": category})
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("loop.search_failed", exc_info=exc)
            state.status = "error"
            state.last_action = ConversationAction.END.name
            self._store_new_state(state)
            return AskResponse(
                type="error",
                reason="search_failed",
                conversation_id=conversation_id,
            )

        items, metadata = self._normalise_results(results, category)
        total = self._total_count(metadata, items)

        state.metadata = metadata
        state.category = category
        state.active_filters = []
        state.last_action = ConversationAction.REFINE_RESULTS.name

        action = self._decide_next_action(state, total)
        if action == ConversationAction.ASK_ATTRIBUTE:
            prompt, attribute_info = self._build_refinement_prompt(
                category,
                metadata,
                total,
                set(state.requested_attributes),
                state.active_filters,
            )
            if prompt and attribute_info:
                attribute_name = attribute_info.get("name")
                if attribute_name:
                    lowered = attribute_name.lower()
                    if lowered not in state.requested_attributes:
                        state.requested_attributes.append(lowered)
                state.pending_attribute = attribute_info
                state.last_prompt = prompt
                state.status = "awaiting_reply"
                state.question_count = 1
                state.last_action = ConversationAction.ASK_ATTRIBUTE.name
                self._store_new_state(state)
                return AskResponse(
                    type="ask_user",
                    prompt=prompt,
                    conversation_id=conversation_id,
                )

        response = self._finalise_answer(items, metadata, conversation_id, state)
        state.status = "completed" if response.type == "answer" else "no_results"
        state.last_action = ConversationAction.SHOW_RESULTS.name
        state.last_prompt = None
        state.pending_attribute = None
        self._store_new_state(state)
        return response

    def handle_reply(self, conversation_id: str, reply: str) -> AskResponse:
        try:
            conversation_uuid = UUID(conversation_id)
        except ValueError:
            return AskResponse(
                type="error",
                reason="invalid_conversation_id",
                conversation_id=conversation_id,
            )

        state, is_expired = self.conversation_repository.get(conversation_uuid)
        if state is None:
            return AskResponse(
                type="error",
                reason="unknown_conversation",
                conversation_id=conversation_id,
            )
        if is_expired:
            state.status = "expired"
            state.updated_at = _now_brussels()
            try:
                self.conversation_repository.update(state)
            except KeyError:
                pass
            return AskResponse(
                type="error",
                reason="conversation_expired",
                conversation_id=conversation_id,
            )

        state.turns.append(reply)
        state.updated_at = _now_brussels()

        with self._logging_context(
            conversation_id=conversation_id, turn_index=state.question_count
        ):
            logger.info(
                "loop.reply",
                extra={"conversation_id": conversation_id, "reply": reply},
            )

        category = state.category
        metadata = state.metadata or {}
        if not category:
            state.status = "error"
            state.last_action = ConversationAction.END.name
            self._persist_existing_state(state)
            return AskResponse(
                type="error",
                reason="missing_category",
                conversation_id=conversation_id,
            )

        filters = list(state.active_filters)
        attribute_info = state.pending_attribute
        if attribute_info:
            new_filters = self._build_filters_from_answer(attribute_info, reply)
            logger.info(
                "loop.filters_updated",
                extra={
                    "attribute": attribute_info.get("name"),
                    "new_filters": new_filters,
                    "conversation_id": conversation_id,
                },
            )
            if new_filters:
                attr_name = attribute_info.get("name")
                if attr_name:
                    filters = [f for f in filters if f.get("name") != attr_name]
                filters.extend(new_filters)
        state.active_filters = filters
        state.pending_attribute = None
        state.last_prompt = None
        state.last_action = ConversationAction.REFINE_RESULTS.name

        try:
            results = self.search_fn({"category": category, "filters": filters})
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("loop.search_failed", exc_info=exc)
            state.status = "error"
            self._persist_existing_state(state)
            return AskResponse(
                type="error",
                reason="search_failed",
                conversation_id=conversation_id,
            )

        items, metadata = self._normalise_results(results, category)
        total = self._total_count(metadata, items)
        state.metadata = metadata

        action = self._decide_next_action(state, total)
        if action == ConversationAction.ASK_ATTRIBUTE:
            prompt, next_attribute = self._build_refinement_prompt(
                category,
                metadata,
                total,
                set(state.requested_attributes),
                state.active_filters,
            )
            if prompt and next_attribute:
                attribute_name = next_attribute.get("name")
                if attribute_name:
                    lowered = attribute_name.lower()
                    if lowered not in state.requested_attributes:
                        state.requested_attributes.append(lowered)
                state.pending_attribute = next_attribute
                state.last_prompt = prompt
                state.status = "awaiting_reply"
                state.question_count += 1
                state.last_action = ConversationAction.ASK_ATTRIBUTE.name
                self._persist_existing_state(state)
                return AskResponse(
                    type="ask_user",
                    prompt=prompt,
                    conversation_id=conversation_id,
                )

        response = self._finalise_answer(items, metadata, conversation_id, state)
        state.status = "completed" if response.type == "answer" else "no_results"
        state.last_action = ConversationAction.SHOW_RESULTS.name
        state.last_prompt = None
        state.pending_attribute = None
        self._persist_existing_state(state)
        return response

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _store_new_state(self, state: ConversationState) -> None:
        state.updated_at = _now_brussels()
        self.conversation_repository.create(state)

    def _persist_existing_state(self, state: ConversationState) -> None:
        state.updated_at = _now_brussels()
        self.conversation_repository.update(state)

    def _decide_next_action(self, state: ConversationState, total: int) -> ConversationAction:
        if total <= self.result_threshold:
            return ConversationAction.SHOW_RESULTS
        if state.question_count >= self.max_questions:
            return ConversationAction.SHOW_RESULTS

        metadata = state.metadata or {}
        options = metadata.get("attribute_options")
        asked = {name.lower() for name in state.requested_attributes}
        if isinstance(options, list):
            for entry in options:
                name = entry.get("name") if isinstance(entry, dict) else None
                if name and name.lower() not in asked:
                    return ConversationAction.ASK_ATTRIBUTE

        return ConversationAction.SHOW_RESULTS

    def _finalise_answer(
        self,
        items: list[dict[str, Any]],
        metadata: Dict[str, Any],
        conversation_id: str,
        state: ConversationState | None = None,
    ) -> AskResponse:
        intro = self._generate_result_intro(metadata, items, state)
        if items:
            return AskResponse(
                type="answer",
                text=self._format_results(items, metadata, intro),
                conversation_id=conversation_id,
            )
        fallback_text = (
            f"{intro}\nGeen producten gevonden" if intro else "Geen producten gevonden"
        )
        return AskResponse(
            type="no_results",
            text=fallback_text,
            conversation_id=conversation_id,
        )

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
        self,
        items: list[Dict[str, Any]],
        metadata: Dict[str, Any],
        intro: Optional[str] = None,
    ) -> str:
        header = metadata.get("product_name") or metadata.get("category") or "producten"
        preferred_columns = metadata.get("preferred_columns") or []
        lines: list[str] = []
        if intro:
            lines.append(intro)
        lines.append(f"Resultaten voor {header}:")

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

    def _generate_result_intro(
        self,
        metadata: Dict[str, Any],
        items: list[dict[str, Any]],
        state: ConversationState | None,
    ) -> Optional[str]:
        generator = getattr(self.refinement_llm, "generate_result_intro", None)
        if not callable(generator):
            return None

        base_category = (
            metadata.get("product_name")
            or metadata.get("category")
            or (state.category if state else None)
            or "producten"
        )
        count = self._total_count(metadata, items)
        filters = state.active_filters if state else []
        question_count = state.question_count if state else 0
        if filters:
            reason = "Gebaseerd op je voorkeuren"
        elif question_count > 1:
            reason = "Bijgewerkte selectie na je antwoorden"
        else:
            reason = "Eerste selectie op basis van je vraag"

        context = {
            "category": base_category,
            "count": count,
            "applied_filters": filters,
            "reason": reason,
        }

        try:
            intro = generator(context)
        except Exception:  # pragma: no cover - defensive
            return None
        if intro and isinstance(intro, str) and len(intro) <= 120:
            return intro
        return None

    def _build_refinement_prompt(
        self,
        category: str,
        metadata: Dict[str, Any],
        count: int,
        asked: set[str],
        filters: list[Dict[str, Any]] | None,
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

        if filters:
            reason = "Gebaseerd op je eerdere antwoorden"
        elif count > self.result_threshold:
            reason = f"Er zijn nog {count} resultaten, help mij kiezen"
        else:
            reason = "Verfijn de selectie"

        context = {
            "category": product_name,
            "attribute": attribute_data,
            "applied_filters": filters or [],
            "count": count,
            "asked_attributes": sorted(asked),
            "reason": reason,
        }

        question = None
        try:
            question = self.refinement_llm.generate_question(context)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("loop.refinement_failed", exc_info=exc)
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

    def _build_filters_from_answer(
        self, attribute: Dict[str, Any], reply: str
    ) -> list[Dict[str, Any]]:
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

    @contextmanager
    def _logging_context(
        self, conversation_id: Optional[str], turn_index: Optional[int]
    ) -> Iterator[None]:
        tokens: list[Tuple[Any, Token]] = []
        if conversation_id is not None:
            tokens.append((conversation_id_ctx, conversation_id_ctx.set(conversation_id)))
        if turn_index is not None:
            tokens.append((turn_index_ctx, turn_index_ctx.set(turn_index)))
        try:
            yield
        finally:
            for ctx, token in reversed(tokens):
                ctx.reset(token)
