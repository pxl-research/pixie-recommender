import logging
from typing import Any, Dict, Optional
from uuid import uuid4

from ..storage.pending_store import InMemoryPendingStore
from ..utils.contracts import AskResponse
from .attribute_collector import AttributeCollector
from .llm_orchestrator import LLMOrchestrator, create_llm_orchestrator

logger = logging.getLogger(__name__)


class SimplifiedConversationManager:
    def __init__(
        self,
        search_fn,
        pending_store: Optional[InMemoryPendingStore] = None,
        llm_orchestrator: Optional[LLMOrchestrator] = None,
        max_iterations: int = 3,
    ) -> None:
        self.search_fn = search_fn
        self.pending_store = pending_store or InMemoryPendingStore()
        self.llm_orchestrator = llm_orchestrator or create_llm_orchestrator()
        self.max_iterations = max_iterations

    def handle_new_question(self, question: str) -> AskResponse:
        logger.info("question", extra={"question": question})
        relevance = self.llm_orchestrator.check_relevance_and_category(question)
        if not relevance.success:
            return AskResponse(type="error", reason="llm_failure")
        if not relevance.result["relevant"]:
            return AskResponse(type="not_relevant", text="Not relevant")
        category = relevance.result["category"] or "laptops"
        decision = self.llm_orchestrator.should_collect_attributes(question, {})
        if decision.success and not decision.result["should_collect"]:
            return self._generate_direct_results(question, category)
        return self._start_attribute_collection(question, category)

    def handle_reply(self, pending_id: str, reply: str) -> AskResponse:
        logger.info("reply", extra={"pending_id": pending_id})
        pending_entry = self.pending_store.get_pending(pending_id)
        if not pending_entry:
            return AskResponse(type="error", reason="invalid_pending_id")
        context = pending_entry.conversation_context or {}
        category = context.get("category", "laptops")
        collector = self._get_attribute_collector(context, category)
        current_question = context.get("current_question")
        if current_question:
            collector.collect_attribute(current_question, reply)
            context["iterations"] = context.get("iterations", 0) + 1
        if collector.is_collection_complete() or context["iterations"] >= self.max_iterations:
            return self._generate_search_results(pending_id, collector, context)
        return self._ask_next_question(pending_id, collector, context)

    def _start_attribute_collection(self, question: str, category: str) -> AskResponse:
        pending_id = f"pending-{uuid4().hex[:8]}"
        collector = AttributeCollector(category, self.max_iterations)
        next_question = collector.get_next_question()
        if not next_question:
            return self._generate_direct_results(question, category)
        context = {
            "category": category,
            "question": question,
            "current_question": next_question.name,
            "iterations": 0,
            "collector_state": self._serialize_collector(collector),
        }
        self.pending_store.save_pending(pending_id, question, conversation_context=context)
        return AskResponse(type="ask_user", prompt=next_question.question, pending_id=pending_id)

    def _ask_next_question(
        self, pending_id: str, collector: AttributeCollector, context: Dict[str, Any]
    ) -> AskResponse:
        next_question = collector.get_next_question()
        if not next_question:
            return self._generate_search_results(pending_id, collector, context)
        context["current_question"] = next_question.name
        context["collector_state"] = self._serialize_collector(collector)
        pending_entry = self.pending_store.get_pending(pending_id)
        if pending_entry:
            self.pending_store.save_pending(
                pending_id, pending_entry.question, conversation_context=context
            )
        return AskResponse(type="ask_user", prompt=next_question.question, pending_id=pending_id)

    def _generate_search_results(
        self, pending_id: str, collector: AttributeCollector, context: Dict[str, Any]
    ) -> AskResponse:
        category = context.get("category", "laptops")
        question = context.get("question", "")
        summary = collector.get_collection_summary()
        sql_result = self.llm_orchestrator.generate_search_query(question, summary, category)
        if not sql_result.success:
            return AskResponse(type="error", reason="search_failed")
        try:
            sql_query = sql_result.result["sql"]
            results = self.search_fn(sql_query, {"category": category})
            self.pending_store.resolve_pending(pending_id)
            if results:
                return AskResponse(type="answer", text=str(results))
            return AskResponse(type="no_results", text="No matching products found")
        except Exception as exc:  # pragma: no cover - external dependency placeholder
            logger.error("search_failed", exc_info=exc)
            return AskResponse(type="error", reason="search_failed")

    def _generate_direct_results(self, question: str, category: str) -> AskResponse:
        sql_result = self.llm_orchestrator.generate_search_query(question, {}, category)
        sql_query = sql_result.result.get("sql") if sql_result.result else None
        if not sql_query:
            return AskResponse(type="error", reason="search_failed")
        try:
            results = self.search_fn(sql_query, {"category": category})
            if results:
                return AskResponse(type="answer", text=str(results))
            return AskResponse(type="no_results", text="No matching products found")
        except Exception as exc:  # pragma: no cover - external dependency placeholder
            logger.error("search_failed", exc_info=exc)
            return AskResponse(type="error", reason="search_failed")

    def _get_attribute_collector(
        self, context: Dict[str, Any], category: str
    ) -> AttributeCollector:
        state = context.get("collector_state")
        collector = AttributeCollector(category, self.max_iterations)
        if state:
            collector.collected_attributes = state.get("collected_attributes", {})
        return collector

    def _serialize_collector(self, collector: AttributeCollector) -> Dict[str, Any]:
        return {
            "collected_attributes": collector.collected_attributes,
            "category": collector.category,
            "max_attributes": collector.max_attributes,
        }
