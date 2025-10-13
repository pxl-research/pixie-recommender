"""Tiny façade that wires the individual LLMs together."""

import logging
from dataclasses import dataclass
from typing import Any, Optional, Protocol

logger = logging.getLogger(__name__)


class RelevanceLLM(Protocol):
    def is_relevant(self, question: Optional[str]) -> bool: ...

    def detect_category(self, question: Optional[str]) -> Optional[str]: ...
@dataclass
class LLMResponse:
    success: bool
    result: Any = None
    error: Optional[str] = None
    confidence: float = 1.0


class LLMOrchestrator:
    """Coordinates relevance checks for the direct conversation flow."""

    def __init__(
        self,
        relevance_llm: RelevanceLLM,
    ) -> None:
        self.relevance_llm = relevance_llm

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
                return LLMResponse(
                    success=True, result={"relevant": False, "category": None}
                )
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
        except Exception as exc:  # defensive
            logger.error("relevance_failed", exc_info=exc)
            return LLMResponse(
                success=False,
                error="llm_failure",
                result={"relevant": False, "category": None},
            )
