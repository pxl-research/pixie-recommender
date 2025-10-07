"""Public entrypoint for the minimal Pixie conversation service."""

import logging
from typing import List

from ..utils.contracts import AskResponse
from ..utils.tabular_api import TabularDatasetSearch, build_search_from_env
from .direct_conversation_manager import DirectConversationManager
from .llm_orchestrator import create_llm_orchestrator

logger = logging.getLogger(__name__)


class Pixie:
    """Wraps the conversation manager so the API layer can stay tiny."""

    def __init__(
        self,
        conversation_manager: DirectConversationManager | None = None,
    ) -> None:
        if conversation_manager is not None:
            self._conversation_manager = conversation_manager
            return

        search = self._build_search_backend()
        categories = self._load_categories(search)
        orchestrator = create_llm_orchestrator(categories)
        self._conversation_manager = DirectConversationManager(search.search, orchestrator)

    def answer(self, question: str) -> AskResponse:
        logger.info("answer", extra={"question": question})
        return self._conversation_manager.handle_new_question(question)

    def reply(self, pending_id: str, reply_text: str) -> AskResponse:
        logger.info("reply", extra={"pending_id": pending_id})
        return self._conversation_manager.handle_reply(pending_id, reply_text)

    def _build_search_backend(self) -> TabularDatasetSearch:
        search = build_search_from_env()
        logger.info(
            "tabular_search_enabled",
            extra={
                "base_url": search.config.base_url,
                "collection": search.config.collection,
                "limit": search.config.default_limit,
            },
        )
        return search

    def _load_categories(self, search: TabularDatasetSearch) -> List[str]:
        try:
            documents = search.list_documents()
        except Exception:
            logger.exception(
                "tabular_category_fetch_failed",
                extra={"collection": search.config.collection},
            )
            raise

        if not documents:
            raise RuntimeError(
                f"No documents found for collection '{search.config.collection}'"
            )

        categories = []
        seen: set[str] = set()
        for doc in documents:
            product = (doc.get("product_name") or doc.get("product") or "").strip()
            if not product:
                continue
            key = product.lower()
            if key in seen:
                continue
            seen.add(key)
            categories.append(product)

        if not categories:
            raise RuntimeError("Tabular dataset returned documents without product names")

        logger.info(
            "tabular_categories_loaded",
            extra={"collection": search.config.collection, "categories": categories},
        )
        return categories
