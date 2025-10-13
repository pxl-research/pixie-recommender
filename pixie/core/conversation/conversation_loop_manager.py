"""Conversation loop orchestration for the Pixie assistant.

The loop manager ties together:
    * the relevance/orchestration LLM (to decide the category),
    * the Azure filter LLM (to translate replies into structured filters),
    * the refinement LLM (to craft follow-up prompts),
    * the data search function.

Only the high-level flow lives in this file; reusable helpers sit in
``conversation_utils`` to keep responsibilities tidy.
"""

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
from .conversation_utils import (
    Filters,
    SearchResult,
    attribute_label,
    format_result_text,
    normalise_search_response,
    select_attribute_for_refinement,
)

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
        attribute_provider: Optional[Callable[[str], Optional[List[Dict[str, Any]]]]] = None,
    ) -> None:
        self.search_fn = search_fn
        self.llm_orchestrator = llm_orchestrator
        self.refinement_llm = refinement_llm
        self.filter_llm = filter_llm
        self.repository = repository
        self.result_threshold = max(result_threshold, 1)
        self.max_questions = max(max_questions, 1)
        self.attribute_provider = attribute_provider

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def handle_new_question(self, question: str) -> AskResponse:
        """Answer an initial user question or, if needed, kick off refinement."""
        self.repository.expire_stale()
        relevance = self.llm_orchestrator.check_relevance_and_category(question)
        if not relevance.success:
            return AskResponse(type="error", reason=relevance.error or "llm_failure")
        if not relevance.result.get("relevant"):
            return AskResponse(type="not_relevant", text="Not relevant")

        category = relevance.result.get("category")
        if not category:
            return AskResponse(type="error", reason="missing_category")

        initial_filters, answered_attributes = self._initial_filters(
            question, category, None
        )
        try:
            result = self._execute_search(category, initial_filters or None)
        except Exception as exc:  
            logger.error("loop.search_failed", exc_info=exc)
            return AskResponse(type="error", reason="search_failed")

        if initial_filters and result.total == 0:
            logger.info(
                "loop.initial_filters_no_hits",
                extra={"filters": initial_filters, "question": question},
            )
            initial_filters = []
            answered_attributes = set()
            try:
                result = self._execute_search(category)
            except Exception as exc:  
                logger.error("loop.search_failed", exc_info=exc)
                return AskResponse(type="error", reason="search_failed")

        if not initial_filters:
            post_filters, post_answered = self._initial_filters(
                question, category, result.metadata
            )
            if post_filters:
                try:
                    filtered = self._execute_search(category, post_filters)
                except Exception as exc:  
                    logger.error("loop.initial_filter_search_failed", exc_info=exc)
                    return AskResponse(type="error", reason="search_failed")
                if filtered.total > 0:
                    initial_filters = post_filters
                    answered_attributes = post_answered
                    result = filtered
                else:
                    logger.info(
                        "loop.initial_filters_no_hits",
                        extra={"filters": post_filters, "question": question},
                    )

        if result.total <= self.result_threshold:
            return self._finalise_answer(result, None)

        prompt, attribute = self._create_refinement_prompt(
            category, result, answered_attributes, initial_filters
        )
        if not prompt or not attribute:
            return self._finalise_answer(result, None)

        conv_id = str(uuid4())
        asked = set(answered_attributes)
        attr_name = attribute.get("name")
        if attr_name:
            asked.add(attr_name.lower())
        state = ConversationState(
            conversation_id=conv_id,
            category=category,
            filters=initial_filters,
            asked_attributes=asked,
            question_count=1,
            metadata=result.metadata,
            current_attribute=attribute,
        )
        with conversation_context(conv_id, 1):
            self.repository.create(state)
        return AskResponse(type="ask_user", prompt=prompt, conversation_id=conv_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def handle_reply(self, conversation_id: str, reply: str) -> AskResponse:
        """Process a follow-up reply inside an existing conversation."""
        self.repository.expire_stale()
        state = self.repository.get(conversation_id)
        if not state:
            return AskResponse(
                type="error",
                reason="unknown_conversation",
                conversation_id=conversation_id,
            )

        category = state.category
        filters: Filters = list(state.filters)
        attribute = state.current_attribute or {}

        with conversation_context(conversation_id, state.question_count + 1):
            new_filters = self._build_filters_from_answer(attribute, reply)
            if new_filters:
                attr_name = attribute.get("name")
                if attr_name:
                    filters = [f for f in filters if f.get("name") != attr_name]
                filters.extend(new_filters)

            try:
                result = self._execute_search(category, filters)
            except Exception as exc:  
                logger.error("loop.search_failed", exc_info=exc)
                self.repository.delete(conversation_id)
                return AskResponse(
                    type="error",
                    reason="search_failed",
                    conversation_id=conversation_id,
                )

        if result.total <= self.result_threshold or state.question_count >= self.max_questions:
            self.repository.delete(conversation_id)
            return self._finalise_answer(result, conversation_id)

        prompt, next_attr = self._create_refinement_prompt(
            category, result, state.asked_attributes, filters
        )
        if not prompt or not next_attr:
            self.repository.delete(conversation_id)
            return self._finalise_answer(result, conversation_id)

        state.filters = filters
        state.metadata = result.metadata
        state.current_attribute = next_attr
        state.question_count += 1
        next_name = next_attr.get("name")
        if next_name:
            state.asked_attributes.add(next_name.lower())
        self.repository.update(state)
        return AskResponse(type="ask_user", prompt=prompt, conversation_id=conversation_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _execute_search(
        self, category: str, filters: Optional[Filters] = None
    ) -> SearchResult:
        """Run the search callback and normalise its response into ``SearchResult``."""
        payload: Dict[str, Any] = {"category": category}
        if filters:
            payload["filters"] = filters
        response = self.search_fn(None, payload)
        return normalise_search_response(response, category)

    def _initial_filters(
        self, question: str, category: str, metadata: Optional[Dict[str, Any]]
    ) -> Tuple[Filters, set[str]]:
        """Let the filter LLM derive structured filters from the opening question.

        We first consult the optional ``attribute_provider`` so that we can avoid an
        initial search call when metadata is already known (for example via the
        bootstrap stage). If the provider is absent or returns nothing, we fall back
        to metadata that may be supplied by the caller. At most the first 20
        attribute descriptors are sent to the LLM to keep the prompt compact.
        """
        if not self.filter_llm:
            return [], set()

        attributes: List[Dict[str, Any]] = []
        if self.attribute_provider:
            provided = self.attribute_provider(category) or []
            attributes = list(provided[:20]) if len(provided) > 20 else list(provided)

        if not attributes and metadata:
            raw_attributes = metadata.get("attribute_options") or []
            attributes = (
                list(raw_attributes[:20]) if len(raw_attributes) > 20 else list(raw_attributes)
            )

        if not attributes:
            return [], set()

        filters = self.filter_llm.derive_filters_from_question(question, attributes) or []
        answered = {
            str(item.get("name")).lower()
            for item in filters
            if isinstance(item, dict) and item.get("name")
        }
        return filters, answered

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
        self, result: SearchResult, conversation_id: Optional[str]
    ) -> AskResponse:
        """Render a terminal response (answer/no-results) for the user."""
        text = (
            format_result_text(result)
            if result.items
            else "Geen producten gevonden"
        )
        return AskResponse(
            type="answer" if result.items else "no_results",
            text=text,
            conversation_id=conversation_id,
        )

    def _create_refinement_prompt(
        self,
        category: str,
        result: SearchResult,
        asked: set[str],
        filters: Filters,
    ) -> Tuple[Optional[str], Optional[dict]]:
        """Ask the refinement LLM for the next follow-up question."""
        metadata = result.metadata
        items = result.items
        product_name = metadata.get("product_name") or category or "producten"
        attribute = select_attribute_for_refinement(metadata, asked, items)
        if not attribute:
            return None, None

        attr = dict(attribute)
        label = attribute_label(attr)
        attr["label"] = label
        attr_type = (attr.get("type") or "").lower()
        q1, q3 = attr.get("q1"), attr.get("q3")
        values = attr.get("values")

        ctx = {
            "category": product_name,
            "attribute": attr,
            "count": result.total,
            "asked_attributes": sorted(asked),
            "applied_filters": filters or [],
        }

        question = None
        try:
            question = self.refinement_llm.generate_question(ctx)
        except Exception as exc:  
            logger.error("loop.refinement_failed", exc_info=exc)
            question = None

        if not question:
            return None, None
        question_text = question.strip()
        if not question_text:
            return None, None
        return question_text, attr

    def _build_filters_from_answer(
        self,
        attribute: Dict[str, Any],
        reply: str,
    ) -> List[Dict[str, Any]]:
        """Convert a free-form reply into structured filters for a single attribute."""
        reply_text = (reply or "").strip()
        if not reply_text:
            return []

        if not self.filter_llm:
            return []

        try:
            raw_filters = self.filter_llm.build_filters(reply_text, attribute) or []
        except Exception:  # defensive
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
