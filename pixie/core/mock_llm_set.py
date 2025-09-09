from __future__ import annotations

from typing import Tuple

from .mock_refinement_llm import MockRefinementLLM
from .mock_relevance_llm import MockRelevanceLLM
from .mock_sql_llm import MockSQLLLM


def create_mock_llm_set() -> Tuple[MockRelevanceLLM, MockSQLLLM, MockRefinementLLM]:
    """Create a trio of mock LLMs (relevance, sql, refinement)."""
    return (
        MockRelevanceLLM(),
        MockSQLLLM(),
        MockRefinementLLM(),
    )
