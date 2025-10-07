"""Public entrypoint for the minimal Pixie conversation service."""

import logging
from typing import Any, Callable, Dict, List, Optional

from ..utils.contracts import AskResponse
from ..utils.tabular_api import TabularAPIClient, build_tabular_client
from .direct_conversation_manager import DirectConversationManager
from .llm_orchestrator import create_llm_orchestrator

logger = logging.getLogger(__name__)

SearchCallable = Callable[[str, Optional[Dict[str, Any]]], Dict[str, Any]]


class Pixie:
    """Wraps the conversation manager so the API layer can stay tiny."""

    def __init__(
        self,
        conversation_manager: DirectConversationManager | None = None,
    ) -> None:
        if conversation_manager is not None:
            self._conversation_manager = conversation_manager
            return

        client, base_url, collection, default_limit = build_tabular_client()
        logger.info(
            "tabular_search_enabled",
            extra={
                "base_url": base_url,
                "collection": collection,
                "limit": default_limit,
            },
        )
        categories = self._load_categories(client, collection)
        orchestrator = create_llm_orchestrator(categories)
        search_fn = self._build_search_fn(client, collection, default_limit)
        self._conversation_manager = DirectConversationManager(search_fn, orchestrator)

    def answer(self, question: str) -> AskResponse:
        logger.info("answer", extra={"question": question})
        return self._conversation_manager.handle_new_question(question)

    def reply(self, pending_id: str, reply_text: str) -> AskResponse:
        logger.info("reply", extra={"pending_id": pending_id})
        return self._conversation_manager.handle_reply(pending_id, reply_text)

    def _load_categories(self, client: TabularAPIClient, collection: str) -> List[str]:
        try:
            documents = client.list_documents(collection)
        except Exception:
            logger.exception(
                "tabular_category_fetch_failed",
                extra={"collection": collection},
            )
            raise

        if not documents:
            raise RuntimeError(f"No documents found for collection '{collection}'")

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
            extra={"collection": collection, "categories": categories},
        )
        return categories

    def _build_search_fn(
        self, client: TabularAPIClient, collection: str, default_limit: int
    ) -> SearchCallable:
        def run_search(sql: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            ctx = context or {}
            product = ctx.get("product")
            if not product:
                category_value = str(ctx.get("category") or "").strip().lower()
                product = self._map_category_to_product(category_value)
            filters = ctx.get("filters")
            limit = ctx.get("limit") or default_limit

            logger.info(
                "tabular_search_query",
                extra={
                    "product": product,
                    "collection": collection,
                    "limit": limit,
                    "filters": filters,
                    "sql": sql,
                },
            )

            response = client.query_product_rows(
                collection,
                product,
                limit=limit,
                filters=filters,
            )
            response.setdefault("product_name", product)
            results = response.setdefault("results", [])
            response.setdefault("count", len(results))
            response.setdefault("limit", limit)
            return response

        return run_search

    @staticmethod
    def _map_category_to_product(category: str) -> str:
        mapping = {
            "printer": "printer",
            "printers": "printer",
            "laptop": "laptop",
            "laptops": "laptop",
            "smartphone": "smartphone",
            "smartphones": "smartphone",
            "computer": "pc",
            "computers": "pc",
            "pc": "pc",
        }
        return mapping.get(category, category or "laptop")
