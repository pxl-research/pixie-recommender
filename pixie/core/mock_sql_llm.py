from __future__ import annotations

from typing import Optional

from pixie.core.abstractclasses.llm import LLM


class MockSQLLLM(LLM):
    """Literal SQL generator: always returns SELECT * FROM printers;"""

    def __init__(self, model_name: str = "mock-sql-llm"):
        super().__init__(model_name)

    def generate_sql(
        self, question: Optional[str], attributes: Optional[dict] = None
    ) -> str:
        return "SELECT * FROM printers;"
