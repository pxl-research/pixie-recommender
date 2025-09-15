from __future__ import annotations

import logging

from pixie.core.contracts import AskResponse
from pixie.core.conversation_loop import ConversationLoopManager
from pixie.core import azure_llm_set
from pixie.core.pending_store import InMemoryPendingStore


class Pixie:
    """Main interface for handling user questions and replies using Azure LLMs.

    Delegates all processing to the ConversationLoopManager for real LLM-based
    conversation flows.
    """

    def __init__(
        self,
        pending_store: InMemoryPendingStore | None = None,
        conversation_manager: ConversationLoopManager | None = None,
    ):
        self._pending_store = pending_store or InMemoryPendingStore()
        # If no conversation_manager was provided, create one using
        # the Azure LLM factory.
        if conversation_manager is not None:
            self._conversation_manager = conversation_manager
        else:
            relevance, sql, refinement = azure_llm_set.create_azure_llm_set()
            # Provide a default search function that will be used by the
            # ConversationLoopManager. Import lazily to avoid cycles.
            from pixie.core.search_engine import RealSearchEngine

            engine = RealSearchEngine()
            self._conversation_manager = ConversationLoopManager(
                relevance,
                sql,
                refinement,
                engine.search,
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
