import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

logger = logging.getLogger(__name__)


class RelevanceLLM(Protocol):
    def is_relevant(self, question: Optional[str]) -> bool: ...

    def detect_category(self, question: Optional[str]) -> Optional[str]: ...


class SQLLLM(Protocol):
    def generate_sql(
        self, question: str, context: Dict[str, Any], table_name: str
    ) -> str: ...


class RefinementLLM(Protocol):
    def should_ask_question(self, question: str, context: Dict[str, Any]) -> bool: ...

    def generate_refinement_question(
        self, question: str, context: Dict[str, Any]
    ) -> str: ...


@dataclass
class LLMResponse:
    success: bool
    result: Any = None
    error: Optional[str] = None
    confidence: float = 1.0


class LLMOrchestrator:
    def __init__(
        self,
        relevance_llm: RelevanceLLM,
        sql_llm: SQLLLM,
        refinement_llm: RefinementLLM,
    ) -> None:
        self.relevance_llm = relevance_llm
        self.sql_llm = sql_llm
        self.refinement_llm = refinement_llm

    def check_relevance_and_category(self, question: str) -> LLMResponse:
        try:
            relevant = self.relevance_llm.is_relevant(question)
            if not relevant:
                return LLMResponse(success=True, result={"relevant": False, "category": None})
            category = self.relevance_llm.detect_category(question)
            return LLMResponse(
                success=True,
                result={"relevant": True, "category": category},
                confidence=0.9 if category else 0.7,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("relevance_failed", exc_info=exc)
            return LLMResponse(success=False, error="llm_failure", result={"relevant": False, "category": None})

    def should_collect_attributes(self, question: str, context: Dict[str, Any]) -> LLMResponse:
        try:
            should_collect = self.refinement_llm.should_ask_question(question, context)
            return LLMResponse(success=True, result={"should_collect": should_collect})
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("refinement_failed", exc_info=exc)
            return LLMResponse(success=True, result={"should_collect": True})

    def generate_search_query(
        self, question: str, context: Dict[str, Any], category: str
    ) -> LLMResponse:
        mapping = {
            "printers": "printers",
            "laptops": "laptop",
            "computers": "computer",
            "smartphones": "smartphone",
        }
        product_type = mapping.get(category, category)
        try:
            sql = self.sql_llm.generate_sql(question, context, product_type)
            return LLMResponse(success=True, result={"sql": sql, "table": "products"})
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("sql_failed", exc_info=exc)
            fallback = (
                "SELECT p.* FROM products p "
                "JOIN product_types pt ON p.product_type_id = pt.id "
                f"WHERE pt.name = '{product_type}' LIMIT 10"
            )
            return LLMResponse(
                success=False,
                error="sql_generation_failed",
                result={"sql": fallback, "table": "products"},
            )

    def generate_attribute_question(
        self, attribute_name: str, question: str, context: Dict[str, Any]
    ) -> LLMResponse:
        try:
            refined = self.refinement_llm.generate_refinement_question(
                question, {**context, "target_attribute": attribute_name}
            )
            return LLMResponse(success=True, result={"question": refined})
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("question_generation_failed", exc_info=exc)
            return LLMResponse(success=False, error="question_generation_failed", result={"question": None})


def create_llm_orchestrator() -> LLMOrchestrator:
    from ..llms import azure_llm_set

    relevance_llm, sql_llm, refinement_llm = azure_llm_set.create_azure_llm_set()
    return LLMOrchestrator(relevance_llm, sql_llm, refinement_llm)
