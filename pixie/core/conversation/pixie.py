import logging

from ..storage.pending_store import InMemoryPendingStore
from ..utils.contracts import AskResponse
from .simplified_conversation_manager import SimplifiedConversationManager

logger = logging.getLogger(__name__)


class Pixie:
    def __init__(
        self,
        pending_store: InMemoryPendingStore | None = None,
        conversation_manager: SimplifiedConversationManager | None = None,
    ) -> None:
        self._pending_store = pending_store or InMemoryPendingStore()
        if conversation_manager is not None:
            self._conversation_manager = conversation_manager
        else:
            def search_with_category(sql: str, context: dict | None = None) -> list[dict]:
                logger.info("search_stub", extra={"sql": sql, "context": context})
                return []

            self._conversation_manager = SimplifiedConversationManager(
                search_with_category,
                pending_store=self._pending_store,
            )

    def answer(self, question: str) -> AskResponse:
        logger.info("answer", extra={"question": question})
        return self._conversation_manager.handle_new_question(question)

    def reply(self, pending_id: str, reply_text: str) -> AskResponse:
        logger.info("reply", extra={"pending_id": pending_id})
        return self._conversation_manager.handle_reply(pending_id, reply_text)
