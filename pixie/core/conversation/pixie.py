"""Public entrypoint for the Pixie conversation service."""

from __future__ import annotations

import logging
import os
from datetime import timedelta
from typing import Any, Callable, Dict, List, Optional

from ..llms.azure_llm_set import (
    create_azure_filter_llm,
    create_azure_llm_set,
    create_azure_refinement_llm,
)
from ..utils.contracts import AskResponse
from ..utils.logging import conversation_context
from ..utils.tabular_api import TabularAPIClient, build_tabular_client
from .conversation_loop_manager import ConversationLoopManager
from .repository import ConversationRepository

logger = logging.getLogger(__name__)

SearchCallable = Callable[[Optional[str], Optional[Dict[str, Any]]], Dict[str, Any]]


class Pixie:
    """Wraps the conversation loop manager so the API layer can stay tiny."""

    def __init__(
        self,
        conversation_manager: ConversationLoopManager | None = None,
        repository: ConversationRepository | None = None,
    ) -> None:
        if conversation_manager is not None:
            self._conversation_manager = conversation_manager
            self._repository = (
                repository
                or getattr(conversation_manager, "repository", None)
            )
            if self._repository is None:
                raise ValueError("Conversation repository is required")
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
        relevance_llm = create_azure_llm_set(categories)
        refinement_llm = create_azure_refinement_llm()
        filter_llm = create_azure_filter_llm()
        search_fn = self._build_search_fn(
            client, collection, default_limit, attribute_map
        )

        ttl_minutes = int(os.environ["PIXIE_CONVERSATION_TTL_MINUTES"])
        repo = repository or ConversationRepository(
            ttl=timedelta(minutes=ttl_minutes)
        )
        result_threshold = int(os.environ["PIXIE_RESULT_THRESHOLD"])
        max_questions = int(os.environ["PIXIE_MAX_REFINE_QUESTIONS"])

        def attribute_provider(category_name: str) -> Optional[Dict[str, Any]]:
            if not category_name:
                return None
            entry = attribute_map.get(category_name.lower())
            if not entry:
                return None
            metadata = dict(entry)
            options = metadata.get("attribute_options")
            if isinstance(options, list):
                metadata["attribute_options"] = list(options)
            return metadata

        self._conversation_manager = ConversationLoopManager(
            search_fn=search_fn,
            relevance_llm=relevance_llm,
            refinement_llm=refinement_llm,
            filter_llm=filter_llm,
            repository=repo,
            result_threshold=result_threshold,
            max_questions=max_questions,
            attribute_provider=attribute_provider,
            available_categories=categories,
        )
        self._repository = repo

    def answer(self, question: str) -> AskResponse:
        logger.info("answer", extra={"question": question})
        with conversation_context(None, 0):
            return self._conversation_manager.handle_new_question(question)

    def reply(self, conversation_id: str, reply_text: str) -> AskResponse:
        with conversation_context(conversation_id, None):
            logger.info("reply")
            return self._conversation_manager.handle_reply(conversation_id, reply_text)

    def active_conversations(self) -> int:
        return self._repository.count()

    def _load_categories(
        self, client: TabularAPIClient, collection: str
    ) -> tuple[List[str], dict[str, Dict[str, Any]]]:
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

        categories: List[str] = []
        attribute_map: dict[str, Dict[str, Any]] = {}
        for doc in documents:
            raw_name = doc.get("product_name") or doc.get("product") or ""
            name = str(raw_name).strip()
            if not name:
                continue
            categories.append(name)
            descriptors = doc.get("attribute_descriptions") or {}
            ranked = sorted(
                descriptors.items(),
                key=lambda item: item[1].get("rank", 10_000),
            )
            top_columns = [column for column, _ in ranked[:3]]
            attribute_list: List[dict[str, Any]] = []
            for column, info in ranked:
                entry: dict[str, Any] = {"name": column}
                if isinstance(info, dict):
                    entry.update(
                        {
                            "description": info.get("description"),
                            "type": info.get("type"),
                            "q1": info.get("q1"),
                            "q3": info.get("q3"),
                            "values": info.get("values"),
                        }
                    )
                attribute_list.append(entry)
            attribute_map[name.lower()] = {
                "top_columns": top_columns,
                "attribute_options": attribute_list,
                "refine_attribute": attribute_list[0] if attribute_list else None,
            }

        if not categories:
            raise RuntimeError(
                "Tabular dataset returned documents without product names"
            )

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
        attribute_map: dict[str, Dict[str, Any]],
    ) -> SearchCallable:
        def run_search(
            sql: Optional[str] = None, context: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            ctx = context or {}
            product = ctx.get("product")
            if not product:
                product = str(ctx.get("category") or "").strip().lower()
            filters = ctx.get("filters")
            limit = ctx.get("limit") or default_limit

            logger.info(
                "tabular_search_query",
                extra={
                    "product": product,
                    "collection": collection,
                    "limit": limit,
                    "filters": filters,
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

            metadata = attribute_map.get(product.lower()) or {}
            preferred = metadata.get("top_columns") or []
            if preferred:
                response.setdefault("preferred_columns", preferred)
            refine_attr = metadata.get("refine_attribute")
            if refine_attr:
                # copy to avoid mutating shared metadata
                response.setdefault("refine_attribute", dict(refine_attr))
            attribute_options = metadata.get("attribute_options") or []
            if attribute_options:
                response.setdefault("attribute_options", attribute_options)
            return response

        return run_search
