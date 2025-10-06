import logging
from typing import Optional

from ..utils.contracts import AskResponse
from .llm_orchestrator import LLMOrchestrator, create_llm_orchestrator

logger = logging.getLogger(__name__)


class SimplifiedConversationManager:
    def __init__(
        self,
        search_fn,
        llm_orchestrator: Optional[LLMOrchestrator] = None,
    ) -> None:
        self.search_fn = search_fn
        self.llm_orchestrator = llm_orchestrator or create_llm_orchestrator()

    def handle_new_question(self, question: str) -> AskResponse:
        logger.info("question", extra={"question": question})
        relevance = self.llm_orchestrator.check_relevance_and_category(question)
        if not relevance.success:
            return AskResponse(type="error", reason="llm_failure")
        if not relevance.result["relevant"]:
            return AskResponse(type="not_relevant", text="Not relevant")

        category = relevance.result["category"] or "laptops"
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

        if results:
            return AskResponse(type="answer", text=str(results))
        return AskResponse(type="no_results", text="No matching products found")

    def handle_reply(self, pending_id: str, reply: str) -> AskResponse:
        logger.info("reply_unsupported", extra={"pending_id": pending_id})
        return AskResponse(type="error", reason="no_pending_support")
