from __future__ import annotations

from typing import Any, Callable
import logging
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
        try:
            relevant = self.relevance_model.is_relevant(question)
        except Exception as e:
            logging.getLogger(__name__).warning(
                "relevance_model.is_relevant failed for question=%r: %s", question, e
            )
            return AskResponse(type="error", reason="relevance_failed")

        if not relevant:
            return AskResponse(type="not_relevant", text="Not relevant")

        # For new relevant questions, prefer to ask refinement questions first
        # instead of immediately generating SQL and returning potentially large
        # result sets. This keeps the UX conversational and avoids dumping the
        # full dataset for vague queries. If the refinement model cannot
        # produce a prompt, fall back to generating SQL and searching.
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
        try:
            prompt = self.refinement_model.generate_refinement_question(context)
        except Exception as e:
            logging.getLogger(__name__).warning(
                "refinement_model.generate_refinement_question failed for context=%r: %s",
                context,
                e,
            )
            prompt = None

        # If refinement model could not provide a prompt, fall back to SQL/search
        if prompt is None:
            try:
                sql = self.sql_model.generate_sql(question, None)
            except Exception as e:
                logging.getLogger(__name__).warning(
                    "sql_model.generate_sql failed for question=%r: %s", question, e
                )
                return AskResponse(type="error", reason="sql_generation_failed")
            results = self.search_fn(sql, None)
            if results:
                # resolve pending entry since we have an immediate answer
                self.pending_store.resolve_pending(pending_id)
                return AskResponse(type="answer", text=str(results))

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
            try:
                prompt = self.refinement_model.generate_refinement_question(ctx)
            except Exception as e:
                logging.getLogger(__name__).warning(
                    "refinement_model.generate_refinement_question failed for context=%r: %s",
                    ctx,
                    e,
                )
                prompt = None
            return AskResponse(type="ask_user", prompt=prompt, pending_id=pending_id)

        if stage == "ask_brand":
            ctx["brand"] = reply
            ctx["stage"] = "ask_tech"
            ctx["iterations"] = ctx.get("iterations", 0) + 1
            self.pending_store.save_pending(
                pending_id, pending_entry.question, conversation_context=ctx
            )
            try:
                prompt = self.refinement_model.generate_refinement_question(ctx)
            except Exception as e:
                logging.getLogger(__name__).warning(
                    "refinement_model.generate_refinement_question failed for context=%r: %s",
                    ctx,
                    e,
                )
                prompt = None
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

        if stage == "choose_result_view":
            # user selects a view (e.g., 'gesorteerd op prijs' or 'willekeurig')
            ctx["view"] = reply
            ctx["iterations"] = ctx.get("iterations", 0) + 1
            # regenerate SQL with chosen view and perform search
            sql = self.sql_model.generate_sql(pending_entry.question, ctx)
            results = self.search_fn(sql, ctx)
            if results:
                self.pending_store.resolve_pending(pending_id)
                return AskResponse(type="answer", text=str(results))
            # nothing found after choosing view -> finish with no_results
            self.pending_store.resolve_pending(pending_id)
            return AskResponse(type="no_results", text="No results found")

        return AskResponse(type="error", reason="unsupported_stage")
