from __future__ import annotations

import logging
from typing import Any, Callable, Tuple
from uuid import uuid4

from ..llms import azure_llm_set
from ..search.search_engine import RealSearchEngine, create_real_search_engine
from ..storage.pending_store import InMemoryPendingStore
from ..utils.attributes import get_attribute_manager
from ..utils.contracts import AskResponse


class ConversationLoopManager:
    """Minimal conversation-loop manager that orchestrates the three Azure LLMs.

    The manager automatically creates Azure LLM instances and expects a
    `search_fn` callable that returns a list of dict results for a SQL query.
    """

    def __init__(
        self,
        search_fn: Callable[[str, dict | None], list[dict]],
        pending_store: InMemoryPendingStore | None = None,
        max_iterations: int = 3,
        llm_set: Tuple[Any, Any, Any] | None = None,
        search_engine: RealSearchEngine | None = None,
    ):
        if llm_set is None:
            llm_set = azure_llm_set.create_azure_llm_set()
        (
            self.relevance_model,
            self.sql_model,
            self.refinement_model,
        ) = llm_set
        self.search_fn = search_fn
        self.pending_store = pending_store or InMemoryPendingStore()
        self.max_iterations = max_iterations
        self.search_engine = search_engine or create_real_search_engine()

    def handle_new_question(self, question: str) -> AskResponse:
        logger = logging.getLogger(__name__)
        try:
            relevant = self.relevance_model.is_relevant(question)
        except Exception as e:
            logger.error("Failed to check relevance for question", exc_info=e)
            return AskResponse(type="error", reason="llm_failure")

        if not relevant:
            return AskResponse(type="not_relevant", text="Not relevant")

        # For new relevant questions, prefer to ask refinement questions first
        # instead of immediately generating SQL and returning potentially large
        # result sets. This keeps the UX conversational and avoids dumping the
        # full dataset for vague queries. If the refinement model cannot
        # produce a prompt, fall back to generating SQL and searching.
        pending_id = f"pending-{uuid4().hex[:8]}"

        # Detect category from the question
        category = None
        try:
            category = self.relevance_model.detect_category(question)
        except Exception as e:
            logger.warning(
                "Failed to detect category, falling back to default", exc_info=e
            )

        # Get category metadata from search engine
        category_metadata = None
        if category and hasattr(self.search_engine, "_categories_metadata"):
            category_metadata = self.search_engine._categories_metadata.get(category)

        # Initialize context with category information
        context: dict[str, Any] = {
            "flow": "product",
            "category": category
            or "printers",  # Default to printers for backward compatibility
            "iterations": 0,
            "question": question,
        }

        # Add category metadata if available
        if category_metadata:
            context["attribute_priority"] = category_metadata.get(
                "attribute_priority", []
            )
            context["attribute_descriptions"] = category_metadata.get(
                "attribute_descriptions", {}
            )

        # Determine first stage based on attribute manager or fallback
        try:
            attr_manager = get_attribute_manager()
            first_attr = attr_manager.get_next_missing_attribute(
                context["category"], context
            )
            if first_attr:
                context["stage"] = f"ask_{first_attr['name']}"
                context["collected_attributes"] = []
            else:
                # No attributes to collect, go directly to SQL generation
                context["stage"] = "generate_sql"
                context["collected_attributes"] = []
        except Exception:
            # Fallback to old behavior for backward compatibility
            if category_metadata and "attribute_priority" in category_metadata:
                # Use first priority attribute for initial stage
                first_attr = category_metadata["attribute_priority"][0]
                context["stage"] = f"ask_{first_attr}"
                context["collected_attributes"] = []
            else:
                context["stage"] = "ask_budget"
                context["collected_attributes"] = []
        self.pending_store.save_pending(
            pending_id, question, ttl_seconds=300, conversation_context=context
        )
        try:
            prompt = self.refinement_model.generate_refinement_question(context)
        except Exception as e:
            logger.error("Failed to generate refinement question", exc_info=e)
            prompt = None

        # If refinement model could not provide a prompt, fall back to SQL/search
        if prompt is None:
            try:
                sql = self.sql_model.generate_sql(question, None)
            except Exception as e:
                logger.error("Failed to generate SQL for fallback", exc_info=e)
                return AskResponse(type="error", reason="llm_failure")
            results = self.search_fn(sql, None)
            if results:
                # resolve pending entry since we have an immediate answer
                self.pending_store.resolve_pending(pending_id)
                return AskResponse(type="answer", text=str(results))

        return AskResponse(type="ask_user", prompt=prompt, pending_id=pending_id)

    def _get_next_stage(self, context: dict[str, Any]) -> str | None:
        """Determine the next stage based on attribute manager."""
        category = context.get("category", "printers")

        try:
            attr_manager = get_attribute_manager()
            next_attr = attr_manager.get_next_missing_attribute(category, context)
            if next_attr:
                return f"ask_{next_attr['name']}"
            else:
                return None  # All attributes collected
        except Exception:
            # Fallback to old hardcoded logic for backward compatibility
            current_stage = context.get("stage")
            if current_stage == "ask_budget":
                return "ask_brand"
            elif current_stage == "ask_brand":
                return "ask_tech"
            else:
                return None

    def handle_reply(self, pending_id: str, reply: str) -> AskResponse:
        logger = logging.getLogger(__name__)
        pending_entry = self.pending_store.get_pending(pending_id)
        if not pending_entry:
            return AskResponse(type="error", reason="invalid_pending_id")

        ctx = pending_entry.conversation_context or {}
        stage = ctx.get("stage")

        # Initialize collected_attributes if not exists
        if "collected_attributes" not in ctx:
            ctx["collected_attributes"] = []

        # Extract attribute name from stage (e.g., "ask_budget" -> "budget")
        if stage and stage.startswith("ask_"):
            attribute_name = stage[4:]  # Remove "ask_" prefix
            ctx[attribute_name] = reply
            ctx["collected_attributes"].append(attribute_name)
            ctx["iterations"] = ctx.get("iterations", 0) + 1

            # Determine next stage
            next_stage = self._get_next_stage(ctx)
            if next_stage:
                ctx["stage"] = next_stage
                self.pending_store.save_pending(
                    pending_id, pending_entry.question, conversation_context=ctx
                )
                try:
                    prompt = self.refinement_model.generate_refinement_question(ctx)
                except Exception as e:
                    logger.error(
                        f"Failed to generate refinement question for {next_stage}",
                        exc_info=e,
                    )
                    return AskResponse(type="error", reason="llm_failure")
                return AskResponse(
                    type="ask_user", prompt=prompt, pending_id=pending_id
                )
            else:
                # All attributes collected, generate SQL and search
                try:
                    # Use category to determine the correct table name
                    category = ctx.get("category", "printers")
                    table_name = category  # Table name matches category name
                    sql = self.sql_model.generate_sql(
                        pending_entry.question, ctx, table_name=table_name
                    )
                except Exception as e:
                    logger.error(
                        "Failed to generate SQL after collecting all attributes",
                        exc_info=e,
                    )
                    return AskResponse(type="error", reason="llm_failure")
                results = self.search_fn(sql, ctx)
                if results:
                    self.pending_store.resolve_pending(pending_id)
                    return AskResponse(type="answer", text=str(results))
                # No results -> ask for result view if iterations allow
                if ctx["iterations"] < self.max_iterations:
                    ctx["stage"] = "choose_result_view"
                    self.pending_store.save_pending(
                        pending_id, pending_entry.question, conversation_context=ctx
                    )
                    return AskResponse(
                        type="ask_user",
                        prompt="No results found. Would you like to try a different view "
                        "or adjust your criteria?",
                        pending_id=pending_id,
                    )
                self.pending_store.resolve_pending(pending_id)
                return AskResponse(type="no_results", text="No results found")

        if stage == "choose_result_view":
            # User selects a view (e.g., 'gesorteerd op prijs' or 'willekeurig')
            ctx["view"] = reply
            ctx["iterations"] = ctx.get("iterations", 0) + 1
            # Regenerate SQL with chosen view and perform search
            try:
                # Use category to determine the correct table name
                category = ctx.get("category", "printers")
                table_name = category  # Table name matches category name
                sql = self.sql_model.generate_sql(
                    pending_entry.question, ctx, table_name=table_name
                )
            except Exception as e:
                logger.error(
                    "Failed to generate SQL for choose_result_view", exc_info=e
                )
                return AskResponse(type="error", reason="llm_failure")
            results = self.search_fn(sql, ctx)
            if results:
                self.pending_store.resolve_pending(pending_id)
                return AskResponse(type="answer", text=str(results))
            # Nothing found after choosing view -> finish with no_results
            self.pending_store.resolve_pending(pending_id)
            return AskResponse(type="no_results", text="No results found")

        return AskResponse(type="error", reason="unsupported_stage")
