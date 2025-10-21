"""Client utilities for talking to the external tabular dataset API."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request
from urllib.parse import quote

logger = logging.getLogger(__name__)


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
            logger.debug(
                "tabular_api_request",
                extra={"method": method, "url": url, "payload": payload},
            )
        req = request.Request(url, data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
        except error.HTTPError as exc:  # defensive
            body = exc.read().decode("utf-8", "ignore")
            logger.error(
                "tabular_api_http_error",
                extra={"url": url, "status": exc.code, "body": body[-400:]},
            )
            error_msg = f"Tabular API error: {exc.code}"
            if body:
                error_msg += f" - {body[:200]}"
            raise RuntimeError(error_msg) from exc
        except error.URLError as exc:  # defensive
            logger.error(
                "tabular_api_unreachable", extra={"url": url, "error": str(exc.reason)}
            )
            raise RuntimeError("Tabular API unreachable") from exc

        if not body:
            return None
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:  # defensive
            logger.error(
                "tabular_api_invalid_json", extra={"url": url, "body": body[:200]}
            )
            raise RuntimeError("Tabular API returned invalid JSON") from exc

    def list_collections(self) -> List[Dict[str, Any]]:
        data = self._request("GET", "/collections/") or []
        return self._ensure_list(data)

    def list_documents(self, collection: str) -> List[Dict[str, Any]]:
        data = self._request("GET", f"/collections/{collection}/documents/") or []
        return self._ensure_list(data, extra={"collection": collection})

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
            logger.info(
                "tabular_api_filters",
                extra={
                    "collection": collection,
                    "product": product,
                    "filters": filters,
                },
            )
        # URL encode the product name to handle spaces and special characters
        encoded_product = quote(product, safe="")
        response = self._request(
            "POST",
            f"/collections/{collection}/products/{encoded_product}/query",
            payload,
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

    def _ensure_list(
        self, data: Any, extra: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return data
        details = dict(extra or {})
        details["payload"] = data
        logger.warning("tabular_api_expected_list", extra=details)
        return []


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Environment variable {name} is required for tabular search"
        )
    return value


def build_tabular_client() -> Tuple[TabularAPIClient, str, str, int]:
    base_url = _require_env("PIXIE_TABULAR_API_URL").rstrip("/")
    api_key = _require_env("PIXIE_API_KEY")
    collection = _require_env("PIXIE_TABULAR_COLLECTION")
    timeout = float(os.getenv("PIXIE_TABULAR_TIMEOUT", "10"))
    default_limit = int(os.getenv("PIXIE_DEFAULT_PAGE_SIZE", "10"))

    client = TabularAPIClient(base_url, api_key, timeout=timeout)
    return client, base_url, collection, default_limit
