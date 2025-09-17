from __future__ import annotations

import logging

from ..search.unified_search_engine import SearchEngine
from ..storage.pending_store import InMemoryPendingStore
from ..utils.contracts import AskResponse
from .simplified_conversation_manager import SimplifiedConversationManager


class Pixie:
    """Main interface for handling user questions and replies using Azure LLMs.

    Delegates all processing to the SimplifiedConversationManager for real LLM-based
    conversation flows.
    """

    def __init__(
        self,
        pending_store: InMemoryPendingStore | None = None,
        conversation_manager: SimplifiedConversationManager | None = None,
    ):
        self._pending_store = pending_store or InMemoryPendingStore()
        # If no conversation_manager was provided, create one using
        # the Azure LLM factory.
        if conversation_manager is not None:
            self._conversation_manager = conversation_manager
        else:
            # Provide a default search function that will be used by the
            # SimplifiedConversationManager.
            engine = SearchEngine()

            # Create a wrapper function that extracts category from context
            def search_with_category(
                sql: str, context: dict | None = None
            ) -> list[dict]:
                category = None
                if context and isinstance(context, dict):
                    category = context.get("category")
                result = engine.search(sql, context, category)
                # Handle both old dict format and new list format
                if isinstance(result, dict):
                    return result.get("results", [])
                elif isinstance(result, list):
                    return result
                else:
                    return []

            self._conversation_manager = SimplifiedConversationManager(
                search_with_category,
                pending_store=self._pending_store,
            )

    def answer(self, question: str) -> AskResponse:
        logger = logging.getLogger(__name__)
        logger.info("pixie.answer", extra={"question": question})

        # Delegate to conversation manager for all questions
        return self._conversation_manager.handle_new_question(question)

    def reply(self, pending_id: str, reply_text: str) -> AskResponse:
        logger = logging.getLogger(__name__)
        logger.info(
            "pixie.reply", extra={"pending_id": pending_id, "reply_text": reply_text}
        )

        # Delegate to conversation manager for all replies
        return self._conversation_manager.handle_reply(pending_id, reply_text)
