"""Public entrypoint for the minimal Pixie conversation service."""

import logging

from ..utils.contracts import AskResponse
from ..utils.tabular_api import build_search_from_env
from .direct_conversation_manager import DirectConversationManager

logger = logging.getLogger(__name__)


class Pixie:
    """Wraps the conversation manager so the API layer can stay tiny."""
    def __init__(
        self,
        conversation_manager: DirectConversationManager | None = None,
    ) -> None:
        if conversation_manager is not None:
            self._conversation_manager = conversation_manager
        else:
            search_fn = self._build_default_search()
            self._conversation_manager = DirectConversationManager(search_fn)

    def answer(self, question: str) -> AskResponse:
        logger.info("answer", extra={"question": question})
        return self._conversation_manager.handle_new_question(question)

    def reply(self, pending_id: str, reply_text: str) -> AskResponse:
        logger.info("reply", extra={"pending_id": pending_id})
        return self._conversation_manager.handle_reply(pending_id, reply_text)

    def _build_default_search(self):
        search = build_search_from_env()
        logger.info(
            "tabular_search_enabled",
            extra={
                "base_url": search.config.base_url,
                "collection": search.config.collection,
                "limit": search.config.default_limit,
            },
        )
        return search.search
