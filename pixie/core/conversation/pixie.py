"""Public entrypoint for the minimal Pixie conversation service."""

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
from ..utils.tabular_api import TabularAPIClient, build_tabular_client
from .conversation_loop_manager import ConversationLoopManager
from .conversation_repository import ConversationRepository
from .direct_conversation_manager import DirectConversationManager
from .llm_orchestrator import LLMOrchestrator

logger = logging.getLogger(__name__)

SearchCallable = Callable[[Optional[Dict[str, Any]]], Dict[str, Any]]


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
        relevance_llm = create_azure_llm_set(categories)
        refinement_llm = create_azure_refinement_llm()
        filter_llm = create_azure_filter_llm()
        orchestrator = LLMOrchestrator(relevance_llm)
        search_fn = self._build_search_fn(
            client, collection, default_limit, attribute_map
        )
        result_threshold = int(os.getenv("PIXIE_RESULT_THRESHOLD", "3"))
        max_questions = int(os.getenv("PIXIE_MAX_REFINE_QUESTIONS", "2"))
        ttl_minutes_env = os.getenv("PIXIE_CONVERSATION_TTL_MINUTES")
        ttl_minutes_default = 24 * 60
        conversation_ttl_minutes = ttl_minutes_default
        if ttl_minutes_env:
            try:
                parsed = int(ttl_minutes_env)
                conversation_ttl_minutes = parsed if parsed > 0 else ttl_minutes_default
            except ValueError:
                logger.warning(
                    "conversation_ttl_invalid",
                    extra={"value": ttl_minutes_env},
                )
        conversation_repository = ConversationRepository(
            ttl=timedelta(minutes=conversation_ttl_minutes)
        )
        flow_mode = os.getenv("PIXIE_ACTIVE_FLOW", "direct").strip().lower()
        self._active_flow = flow_mode if flow_mode in {"direct", "loop"} else "direct"
        logger.info("pixie_flow_selected", extra={"flow": self._active_flow})

        if self._active_flow == "loop":
            self._conversation_manager = ConversationLoopManager(
                search_fn,
                orchestrator,
                refinement_llm,
                filter_llm,
                result_threshold=result_threshold,
                max_questions=max_questions,
                conversation_repository=conversation_repository,
            )
        else:
            self._conversation_manager = DirectConversationManager(
                search_fn,
                orchestrator,
                refinement_llm,
                filter_llm,
                result_threshold=result_threshold,
                max_questions=max_questions,
                conversation_repository=conversation_repository,
            )

    def answer(self, question: str) -> AskResponse:
        logger.info("answer", extra={"question": question})
        return self._conversation_manager.handle_new_question(question)

    def reply(
        self, pending_id: str, reply_text: str, conversation_id: str | None = None
    ) -> AskResponse:
        logger.info(
            "reply",
            extra={
                "pending_id": pending_id,
                "conversation_id": conversation_id,
                "flow": getattr(self, "_active_flow", "direct"),
            },
        )
        if getattr(self, "_active_flow", "direct") == "loop":
            target_id = conversation_id or pending_id
            return self._conversation_manager.handle_reply(target_id, reply_text)
        return self._conversation_manager.handle_reply(pending_id, reply_text)

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

        categories = []
        attribute_map: dict[str, dict[str, Any]] = {}
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
                top_columns = [column for column, _ in ranked_columns[:3]]
                attribute_list: List[dict[str, Any]] = []
                for column, attr_info in ranked_columns:
                    entry: dict[str, Any] = {"name": column}
                    if isinstance(attr_info, dict):
                        entry.update(
                            {
                                "description": attr_info.get("description"),
                                "type": attr_info.get("type"),
                                "q1": attr_info.get("q1"),
                                "q3": attr_info.get("q3"),
                                "values": attr_info.get("values"),
                            }
                        )
                    attribute_list.append(entry)
                top_attribute = attribute_list[0] if attribute_list else None
                attribute_map[name.lower()] = {
                    "top_columns": top_columns,
                    "attributes": attribute_list,
                    "refine_attribute": top_attribute,
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
        attribute_map: dict[str, dict[str, Any]],
    ) -> SearchCallable:
        def run_search(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
                response.setdefault("refine_attribute", dict(refine_attr))
            attribute_options = metadata.get("attributes") or []
            if attribute_options:
                response.setdefault("attribute_options", attribute_options)
            return response

        return run_search
