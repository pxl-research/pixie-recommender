"""Public entrypoint for the minimal Pixie conversation service."""

import logging
from typing import Any, Callable, Dict, List, Optional

from ..llms.azure_llm_set import create_azure_llm_set
from ..utils.contracts import AskResponse
from ..utils.tabular_api import TabularAPIClient, build_tabular_client
from .direct_conversation_manager import DirectConversationManager
from .llm_orchestrator import LLMOrchestrator

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
        categories, attribute_map = self._load_categories(client, collection)
        relevance_llm, sql_llm = create_azure_llm_set(categories)
        orchestrator = LLMOrchestrator(relevance_llm, sql_llm)
        search_fn = self._build_search_fn(client, collection, default_limit, attribute_map)
        self._conversation_manager = DirectConversationManager(search_fn, orchestrator)

    def answer(self, question: str) -> AskResponse:
        logger.info("answer", extra={"question": question})
        return self._conversation_manager.handle_new_question(question)

    def reply(self, pending_id: str, reply_text: str) -> AskResponse:
        logger.info("reply", extra={"pending_id": pending_id})
        return self._conversation_manager.handle_reply(pending_id, reply_text)

    def _load_categories(
        self, client: TabularAPIClient, collection: str
    ) -> tuple[List[str], dict[str, list[str]]]:
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
        attribute_map: dict[str, list[str]] = {}
        for doc in documents:
            raw_name = doc.get("product_name") or doc.get("product") or ""
            name = str(raw_name).strip()
            if name:
                categories.append(name)
                descriptors = doc.get("attribute_descriptions") or {}
                ranked_columns = sorted(
                    descriptors.items(),
                    key=lambda item: item[1].get("rank", 10_000),
                )
                attribute_map[name.lower()] = [column for column, _ in ranked_columns]

        if not categories:
            raise RuntimeError("Tabular dataset returned documents without product names")

        logger.info(
            "tabular_categories_loaded",
            extra={"collection": collection, "categories": categories},
        )
        return categories, attribute_map

    def _build_search_fn(
        self,
        client: TabularAPIClient,
        collection: str,
        default_limit: int,
        attribute_map: dict[str, list[str]],
    ) -> SearchCallable:
        def run_search(sql: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            ctx = context or {}
            product = ctx.get("product")
            if not product:
                product = str(ctx.get("category") or "").strip().lower() or "laptop"
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
            preferred = attribute_map.get(product.lower()) or []
            if preferred:
                response.setdefault("preferred_columns", preferred)
            return response

        return run_search
