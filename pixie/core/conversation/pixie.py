from __future__ import annotations

import logging

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
            def search_with_category(
                sql: str, context: dict | None = None
            ) -> list[dict]:
                logger = logging.getLogger(__name__)
                logger.info(
                    "search.forward_to_external",
                    extra={"sql": sql, "context": context},
                )
                # The actual product lookup happens in the separate data service.
                # Returning an empty list keeps the flow intact while we wait for
                # that service to respond asynchronously.
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
