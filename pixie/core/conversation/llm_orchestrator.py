"""
Simplified LLM Orchestration

Replaces scattered LLM calls throughout conversation_loop.py
with a clean orchestrator that coordinates the 3 Azure LLMs.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

logger = logging.getLogger(__name__)


# Protocol definitions for clean dependency injection
class RelevanceLLM(Protocol):
    """Protocol for relevance checking LLM."""

    def is_relevant(self, question: Optional[str]) -> bool:
        """Check if question is product-related."""
        ...

    def detect_category(self, question: Optional[str]) -> Optional[str]:
        """Detect product category from question."""
        ...


class SQLLLM(Protocol):
    """Protocol for SQL generation LLM."""

    def generate_sql(
        self, question: str, context: Dict[str, Any], table_name: str
    ) -> str:
        """Generate SQL query from question and context."""
        ...


class RefinementLLM(Protocol):
    """Protocol for conversation refinement LLM."""

    def should_ask_question(self, question: str, context: Dict[str, Any]) -> bool:
        """Determine if we should ask clarifying questions."""
        ...

    def generate_refinement_question(
        self, question: str, context: Dict[str, Any]
    ) -> str:
        """Generate appropriate clarifying question."""
        ...


@dataclass
class LLMResponse:
    """Standardized response from LLM operations."""

    success: bool
    result: Any = None
    error: Optional[str] = None
    confidence: float = 1.0


class LLMOrchestrator:
    """
    Clean orchestrator for the 3 LLMs with:
    - Dependency injection for testability
    - Centralized error handling
    - Consistent response format
    - Reduced coupling to conversation logic

    Replaces scattered LLM calls from conversation_loop.py
    """

    def __init__(
        self,
        relevance_llm: RelevanceLLM,
        sql_llm: SQLLLM,
        refinement_llm: RefinementLLM,
    ):
        self.relevance_llm = relevance_llm
        self.sql_llm = sql_llm
        self.refinement_llm = refinement_llm

    def check_relevance_and_category(self, question: str) -> LLMResponse:
        """
        Single method to handle relevance check and category detection.

        Replaces multiple scattered LLM calls in handle_new_question.
        """
        try:
            # Check relevance first
            is_relevant = self.relevance_llm.is_relevant(question)

            if not is_relevant:
                return LLMResponse(
                    success=True, result={"relevant": False, "category": None}
                )

            # Detect category if relevant
            category = self.relevance_llm.detect_category(question)

            return LLMResponse(
                success=True,
                result={"relevant": True, "category": category},
                confidence=0.9 if category else 0.7,
            )

        except Exception as e:
            logger.error(f"Failed relevance/category check: {e}")
            return LLMResponse(
                success=False,
                error="llm_failure",
                result={"relevant": False, "category": None},
            )

    def should_collect_attributes(
        self, question: str, context: Dict[str, Any]
    ) -> LLMResponse:
        """
        Determine if we should ask clarifying questions vs direct search.

        Centralizes refinement decision logic.
        """
        try:
            should_refine = self.refinement_llm.should_ask_question(question, context)

            return LLMResponse(success=True, result={"should_collect": should_refine})

        except Exception as e:
            logger.error(f"Failed refinement decision: {e}")
            # Default to collecting attributes on error
            return LLMResponse(success=True, result={"should_collect": True})

    def generate_search_query(
        self, question: str, context: Dict[str, Any], category: str
    ) -> LLMResponse:
        """
        Generate SQL query for search.

        Centralizes SQL generation with proper error handling.
        """
        try:
            # Map category to the canonical product type name used by the catalog
            category_to_product_type = {
                "printers": "printers",
                "laptops": "laptop",  # category "laptops" maps to product_type "laptop"
                "computers": "computer",
                "smartphones": "smartphone",
            }

            product_type = category_to_product_type.get(category, category)

            sql_query = self.sql_llm.generate_sql(question, context, product_type)

            return LLMResponse(
                success=True, result={"sql": sql_query, "table": "products"}
            )

        except Exception as e:
            logger.error(f"Failed SQL generation: {e}")
            # Fallback to simple JOIN query for the category
            category_to_product_type = {
                "printers": "printers",
                "laptops": "laptop",
                "computers": "computer",
                "smartphones": "smartphone",
            }
            product_type = category_to_product_type.get(category, category)

            fallback_sql = (
                f"SELECT p.* FROM products p "
                f"JOIN product_types pt ON p.product_type_id = pt.id "
                f"WHERE pt.name = '{product_type}' LIMIT 10"
            )

            return LLMResponse(
                success=False,
                error="sql_generation_failed",
                result={"sql": fallback_sql, "table": "products"},
            )

    def generate_attribute_question(
        self, attribute_name: str, question: str, context: Dict[str, Any]
    ) -> LLMResponse:
        """
        Generate contextual attribute questions.

        Optional enhancement - can fallback to static questions.
        """
        try:
            # Use refinement LLM to generate contextual question
            refined_question = self.refinement_llm.generate_refinement_question(
                question, {**context, "target_attribute": attribute_name}
            )

            return LLMResponse(success=True, result={"question": refined_question})

        except Exception as e:
            logger.warning(
                f"Failed to generate contextual question for {attribute_name}: {e}"
            )
            # Fallback to static questions handled by AttributeCollector
            return LLMResponse(
                success=False,
                error="question_generation_failed",
                result={"question": None},
            )


def create_llm_orchestrator() -> LLMOrchestrator:
    """
    Factory function for LLM orchestrator creation.

    Creates Azure LLM instances with proper error handling.
    """
    # Import real LLMs only when needed
    from ..llms import azure_llm_set

    try:
        relevance_llm, sql_llm, refinement_llm = azure_llm_set.create_azure_llm_set()
        return LLMOrchestrator(relevance_llm, sql_llm, refinement_llm)
    except Exception as e:
        logger.error(f"Failed to create Azure LLMs: {e}")
        raise RuntimeError(
            "Azure LLM configuration is required. Please check your Azure OpenAI settings."
        ) from e


"""
Benefits of this orchestration pattern:

1. **Dependency Injection**: Easy to test with mocks
2. **Centralized Error Handling**: Consistent error responses  
3. **Protocol-Based Design**: Clear interfaces, loose coupling
4. **Single Responsibility**: Only handles LLM coordination
5. **Consistent Response Format**: LLMResponse standardizes outputs

Replaces scattered LLM calls throughout conversation_loop.py
with clean, testable, reusable orchestration logic.
"""
