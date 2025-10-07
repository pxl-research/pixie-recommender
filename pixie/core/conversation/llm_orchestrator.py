"""Tiny façade that wires the individual LLMs together."""

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


@dataclass
class LLMResponse:
    success: bool
    result: Any = None
    error: Optional[str] = None
    confidence: float = 1.0


class LLMOrchestrator:
    """Coordinates relevance and SQL LLMs for the direct conversation flow."""
    def __init__(
        self,
        relevance_llm: RelevanceLLM,
        sql_llm: SQLLLM,
    ) -> None:
        self.relevance_llm = relevance_llm
        self.sql_llm = sql_llm

    def check_relevance_and_category(self, question: str) -> LLMResponse:
        try:
            relevant = self.relevance_llm.is_relevant(question)
            if not relevant:
                logger.info(
                    "relevance_decision",
                    extra={
                        "question": question,
                        "relevant": False,
                        "category": None,
                    },
                )
                return LLMResponse(success=True, result={"relevant": False, "category": None})
            category = self.relevance_llm.detect_category(question)
            logger.info(
                "relevance_decision",
                extra={
                    "question": question,
                    "relevant": True,
                    "category": category,
                },
            )
            return LLMResponse(
                success=True,
                result={"relevant": True, "category": category},
                confidence=0.9 if category else 0.7,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("relevance_failed", exc_info=exc)
            return LLMResponse(
                success=False,
                error="llm_failure",
                result={"relevant": False, "category": None},
            )

    def generate_search_query(
        self, question: str, context: Dict[str, Any], category: str
    ) -> LLMResponse:
        mapping = {
            "printers": "printer",
            "printer": "printer",
            "laptops": "laptop",
            "laptop": "laptop",
            "computers": "pc",
            "computer": "pc",
            "smartphones": "smartphone",
            "smartphone": "smartphone",
        }
        product_type = mapping.get(category, category)
        try:
            sql = self.sql_llm.generate_sql(question, context, product_type)
            logger.info(
                "sql_generation_success",
                extra={
                    "question": question,
                    "category": category,
                    "product_type": product_type,
                    "sql": sql,
                },
            )
            return LLMResponse(success=True, result={"sql": sql, "table": "products"})
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("sql_failed", exc_info=exc)
            fallback = (
                "SELECT p.* FROM products p "
                "JOIN product_types pt ON p.product_type_id = pt.id "
                f"WHERE pt.name = '{product_type}' LIMIT 10"
            )
            logger.info(
                "sql_generation_fallback",
                extra={
                    "question": question,
                    "category": category,
                    "product_type": product_type,
                    "sql": fallback,
                },
            )
            return LLMResponse(
                success=False,
                error="sql_generation_failed",
                result={"sql": fallback, "table": "products"},
            )
