"""Single-pass conversation handler that relies on the LLMs to produce SQL."""

import logging
from typing import Any, Dict, Optional

from ..utils.contracts import AskResponse
from .llm_orchestrator import LLMOrchestrator, create_llm_orchestrator

logger = logging.getLogger(__name__)


class DirectConversationManager:
    """Minimal conversation layer that delegates everything to the LLM stack."""

    def __init__(
        self,
        search_fn,
        llm_orchestrator: Optional[LLMOrchestrator] = None,
    ) -> None:
        self.search_fn = search_fn
        self.llm_orchestrator = llm_orchestrator or create_llm_orchestrator()

    def handle_new_question(self, question: str) -> AskResponse:
        """Classify relevance, detect category, generate SQL, and run the search stub."""
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
        items, metadata = self._normalise_results(results, category)
        if items:
            return AskResponse(type="answer", text=self._format_results(items, metadata))
        return AskResponse(type="no_results", text="Geen producten gevonden")

    def handle_reply(self, pending_id: str, reply: str) -> AskResponse:  # noqa: ARG002
        """Replies are not supported in this minimal build."""
        logger.info("reply_unsupported", extra={"pending_id": pending_id})
        return AskResponse(type="error", reason="no_pending_support")

    def _normalise_results(
        self, payload: Any, category: str
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if isinstance(payload, dict):
            metadata = {k: v for k, v in payload.items() if k != "results"}
            items = payload.get("results") or []
        else:
            metadata = {"category": category}
            items = payload or []
        # Defensive: make sure we only pass dicts further down.
        items = [item for item in items if isinstance(item, dict)]
        return items, metadata

    def _format_results(self, items: list[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
        header = metadata.get("product_name") or metadata.get("category") or "producten"
        lines = [f"Resultaten voor {header}:"]

        for item in items[:3]:  # keep responses compact
            name = item.get("naam") or item.get("name") or item.get("product_name")
            if not name:
                name = "Onbekende naam"
            brand = item.get("merk") or item.get("brand")
            price = item.get("prijs") or item.get("price")
            availability = item.get("beschikbaar")

            details: list[str] = []
            if brand:
                details.append(str(brand))
            if isinstance(price, (int, float)):
                details.append(f"€{price:.2f}")
            if availability is True:
                details.append("op voorraad")
            elif availability is False:
                details.append("niet op voorraad")

            suffix = f" ({', '.join(details)})" if details else ""
            lines.append(f"- {name}{suffix}")

        total = metadata.get("total")
        if isinstance(total, int):
            lines.append(f"Totaal gevonden: {total}")
        return "\n".join(lines)
