"""Client utilities for talking to the external tabular dataset API."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib import error, request

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TabularAPIConfig:
    """Configuration values required to talk to the tabular dataset service."""

    base_url: str
    api_key: str
    collection: str
    timeout: float = 10.0
    default_limit: int = 10


class TabularAPIClient:
    """Thin wrapper around ``urllib`` to avoid adding an HTTP dependency."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key.strip()
        self.timeout = timeout

    def _request(
        self, method: str, path: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any] | None:
        url = f"{self.base_url}{path}"
        headers = {"X-API-Key": self.api_key}
        data: Optional[bytes] = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = request.Request(url, data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
        except error.HTTPError as exc:  # pragma: no cover - defensive
            body = exc.read().decode("utf-8", "ignore")
            logger.error(
                "tabular_api_http_error",
                extra={"url": url, "status": exc.code, "body": body[-400:]},
            )
            raise RuntimeError(f"Tabular API error: {exc.code}") from exc
        except error.URLError as exc:  # pragma: no cover - defensive
            logger.error(
                "tabular_api_unreachable", extra={"url": url, "error": str(exc.reason)}
            )
            raise RuntimeError("Tabular API unreachable") from exc

        if not body:
            return None
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            logger.error("tabular_api_invalid_json", extra={"url": url, "body": body[:200]})
            raise RuntimeError("Tabular API returned invalid JSON") from exc

    def list_collections(self) -> List[Dict[str, Any]]:
        data = self._request("GET", "/collections/") or []
        if isinstance(data, list):
            return data
        logger.warning("tabular_api_expected_list", extra={"payload": data})
        return []

    def query_product_rows(
        self,
        collection: str,
        product: str,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"limit": limit, "offset": offset}
        if filters:
            payload["filters"] = filters
        response = self._request(
            "POST", f"/collections/{collection}/products/{product}/query", payload
        )
        if isinstance(response, dict):
            return response
        logger.warning(
            "tabular_api_unexpected_response",
            extra={"collection": collection, "product": product, "payload": response},
        )
        return {
            "product_name": product,
            "results": [],
            "count": 0,
            "total": 0,
            "limit": limit,
            "offset": offset,
        }


class TabularDatasetSearch:
    """Translate conversation search calls into tabular dataset queries."""

    CATEGORY_TO_PRODUCT = {
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

    def __init__(self, config: TabularAPIConfig) -> None:
        self.config = config
        self.client = TabularAPIClient(config.base_url, config.api_key, timeout=config.timeout)

    def search(self, sql: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = context or {}
        product = ctx.get("product")
        if not product:
            category = str(ctx.get("category") or "").strip().lower()
            product = self.CATEGORY_TO_PRODUCT.get(category, category or "laptop")
        filters = ctx.get("filters")
        limit = ctx.get("limit") or self.config.default_limit

        logger.info(
            "tabular_search_query",
            extra={
                "product": product,
                "collection": self.config.collection,
                "limit": limit,
                "filters": filters,
                "sql": sql,
            },
        )

        response = self.client.query_product_rows(
            self.config.collection,
            product,
            limit=limit,
            filters=filters,
        )
        response.setdefault("product_name", product)
        response.setdefault("results", [])
        response.setdefault("count", len(response["results"]))
        response.setdefault("limit", limit)
        return response


def build_search_from_env() -> Optional[TabularDatasetSearch]:
    base_url = (os.getenv("PIXIE_TABULAR_API_URL", "").strip() or "http://localhost:8000").rstrip("/")
    api_key = os.getenv("PIXIE_API_KEY", "").strip()
    collection = os.getenv("PIXIE_TABULAR_COLLECTION", "auva").strip() or "auva"
    default_limit = int(os.getenv("PIXIE_DEFAULT_PAGE_SIZE", "10"))
    if not api_key or api_key.lower() == "changeme":
        raise RuntimeError("PIXIE_API_KEY must be configured for tabular search")

    config = TabularAPIConfig(
        base_url=base_url,
        api_key=api_key,
        collection=collection,
        default_limit=default_limit,
    )
    return TabularDatasetSearch(config)
