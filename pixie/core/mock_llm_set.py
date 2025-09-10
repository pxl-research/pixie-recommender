from __future__ import annotations

from typing import Tuple
import os
import logging

from .mock_refinement_llm import MockRefinementLLM
from .mock_relevance_llm import MockRelevanceLLM
from .mock_sql_llm import MockSQLLLM


def create_mock_llm_set() -> Tuple[MockRelevanceLLM, MockSQLLLM, MockRefinementLLM]:
    """Create a trio of mock LLMs (relevance, sql, refinement).

    If Azure environment variables are present, attempt to create and return
    Azure LLMs instead. This keeps local tests working by default while
    enabling integration tests to exercise real Azure LLMs when configured.
    """
    azure_vars = (
        os.getenv("AZURE_OPENAI_API_VERSION"),
        os.getenv("AZURE_OPENAI_ENDPOINT"),
        os.getenv("AZURE_OPENAI_KEY"),
        os.getenv("AZURE_OPENAI_MODEL"),
    )
    if all(azure_vars):
        try:
            from .azure_llm_set import create_azure_llm_set

            relevance, sql, refinement = create_azure_llm_set()
            return relevance, sql, refinement
        except Exception as e:
            logging.getLogger(__name__).warning(
                "Azure LLM set requested but initialization failed: %s; falling back to mocks",
                e,
            )

    return (
        MockRelevanceLLM(),
        MockSQLLLM(),
        MockRefinementLLM(),
    )
