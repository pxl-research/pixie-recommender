from __future__ import annotations

from typing import Any, Callable
from uuid import uuid4

from pixie.core.contracts import AskResponse
from pixie.core.pending_store import InMemoryPendingStore


class ConversationLoopManager:
    """Minimal conversation-loop manager that orchestrates the three mock LLMs.

    The manager expects simple, literal behaviors from the supplied models and a
    `search_fn` callable that returns a list of dict results for a SQL query.
    """

    def __init__(
        self,
        relevance_model: Any,
        sql_model: Any,
        refinement_model: Any,
        search_fn: Callable[[str, dict | None], list[dict]],
        pending_store: InMemoryPendingStore | None = None,
        max_iterations: int = 3,
    ):
        self.relevance_model = relevance_model
        self.sql_model = sql_model
        self.refinement_model = refinement_model
        self.search_fn = search_fn
        self.pending_store = pending_store or InMemoryPendingStore()
        self.max_iterations = max_iterations

    def handle_new_question(self, question: str) -> AskResponse:
        if not self.relevance_model.is_relevant(question):
            return AskResponse(type="not_relevant", text="Not relevant")

        sql = self.sql_model.generate_sql(question, None)
        results = self.search_fn(sql, None)
        if results:
            return AskResponse(type="answer", text=str(results))

        # create pending and ask refinement question sequence
        pending_id = f"pending-{uuid4().hex[:8]}"
        context: dict[str, Any] = {
            "flow": "product",
            "stage": "ask_budget",
            "iterations": 0,
            "question": question,
        }
        self.pending_store.save_pending(
            pending_id, question, ttl_seconds=300, conversation_context=context
        )
        prompt = self.refinement_model.generate_refinement_question(context)
        return AskResponse(type="ask_user", prompt=prompt, pending_id=pending_id)

    def handle_reply(self, pending_id: str, reply: str) -> AskResponse:
        pending_entry = self.pending_store.get_pending(pending_id)
        if not pending_entry:
            return AskResponse(type="error", reason="invalid_pending_id")

        ctx = pending_entry.conversation_context or {}
        stage = ctx.get("stage")
        # very literal attribute extraction
        if stage == "ask_budget":
            ctx["budget"] = reply
            ctx["stage"] = "ask_brand"
            ctx["iterations"] = ctx.get("iterations", 0) + 1
            self.pending_store.save_pending(
                pending_id, pending_entry.question, conversation_context=ctx
            )
            prompt = self.refinement_model.generate_refinement_question(ctx)
            return AskResponse(type="ask_user", prompt=prompt, pending_id=pending_id)

        if stage == "ask_brand":
            ctx["brand"] = reply
            ctx["stage"] = "ask_tech"
            ctx["iterations"] = ctx.get("iterations", 0) + 1
            self.pending_store.save_pending(
                pending_id, pending_entry.question, conversation_context=ctx
            )
            prompt = self.refinement_model.generate_refinement_question(ctx)
            return AskResponse(type="ask_user", prompt=prompt, pending_id=pending_id)

        if stage == "ask_tech":
            ctx["technology"] = reply
            ctx["iterations"] = ctx.get("iterations", 0) + 1
            sql = self.sql_model.generate_sql(pending_entry.question, ctx)
            results = self.search_fn(sql, ctx)
            if results:
                self.pending_store.resolve_pending(pending_id)
                return AskResponse(type="answer", text=str(results))
            # no results -> either ask next or finish
            if ctx["iterations"] < self.max_iterations:
                ctx["stage"] = "choose_result_view"
                self.pending_store.save_pending(
                    pending_id, pending_entry.question, conversation_context=ctx
                )
                return AskResponse(
                    type="ask_user",
                    prompt="No results, choose view?",
                    pending_id=pending_id,
                )
            self.pending_store.resolve_pending(pending_id)
            return AskResponse(type="no_results", text="No results found")

        return AskResponse(type="error", reason="unsupported_stage")
