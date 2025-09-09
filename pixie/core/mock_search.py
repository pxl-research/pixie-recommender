from __future__ import annotations

from typing import Any, Dict, List, Optional


class MockSearchEngine:
    """Deterministic mock search engine used in tests.

    API: search(sql: str, attributes: dict | None) -> list[dict]
    """

    def __init__(self, large_result_count: int = 152):
        self.large_result_count = large_result_count

    def search(
        self, sql: str, attributes: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # normalize attributes
        if attributes is None:
            # return many items
            return [
                {"id": i + 1, "name": f"Item {i + 1}", "price": (i + 1) * 10}
                for i in range(self.large_result_count)
            ]

        # attributes present but empty dict
        if isinstance(attributes, dict) and len(attributes) == 0:
            return [
                {"id": i + 1, "name": f"Item {i + 1}", "price": (i + 1) * 10}
                for i in range(self.large_result_count)
            ]

        # handle specific budget rule: if budget contains "minder dan 50€" (case-insensitive)
        budget = None
        if isinstance(attributes, dict):
            budget = attributes.get("budget") or attributes.get("Budget")

        if isinstance(budget, str) and "minder dan 50€" in budget.lower():
            return []

        # otherwise return a small deterministic set (1-5 items) based on hash of values
        small = []
        # combine attribute values to pick a small number
        keys = sorted(attributes.keys()) if isinstance(attributes, dict) else []
        seed = 0
        for k in keys:
            v = attributes.get(k)
            seed += len(str(v or "")) + len(k)

        count = (seed % 5) + 1
        for i in range(count):
            small.append(
                {"id": i + 1, "name": f"Small {i + 1}", "price": (i + 1) * 100}
            )
        return small


def create_mock_search_engine() -> MockSearchEngine:
    return MockSearchEngine()
