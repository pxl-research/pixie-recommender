"""
Simplified LLM Orchestration

Replaces scattered LLM calls throughout conversation_loop.py 
with a clean orchestrator that coordinates the 3 Azure LLMs.
"""

import logging
from typing import Protocol, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Protocol definitions for clean dependency injection
class RelevanceLLM(Protocol):
    """Protocol for relevance checking LLM."""
    
    def is_relevant(self, question: str) -> bool:
        """Check if question is product-related."""
        ...
    
    def detect_category(self, question: str) -> Optional[str]:
        """Detect product category from question."""
        ...


class SQLLLM(Protocol):
    """Protocol for SQL generation LLM."""
    
    def generate_sql(self, question: str, context: Dict[str, Any], table_name: str) -> str:
        """Generate SQL query from question and context."""
        ...


class RefinementLLM(Protocol):
    """Protocol for conversation refinement LLM."""
    
    def should_ask_question(self, question: str, context: Dict[str, Any]) -> bool:
        """Determine if we should ask clarifying questions."""
        ...
    
    def generate_refinement_question(self, question: str, context: Dict[str, Any]) -> str:
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
        refinement_llm: RefinementLLM
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
                    success=True,
                    result={"relevant": False, "category": None}
                )
            
            # Detect category if relevant
            category = self.relevance_llm.detect_category(question)
            
            return LLMResponse(
                success=True,
                result={"relevant": True, "category": category},
                confidence=0.9 if category else 0.7
            )
            
        except Exception as e:
            logger.error(f"Failed relevance/category check: {e}")
            return LLMResponse(
                success=False,
                error="llm_failure",
                result={"relevant": False, "category": None}
            )
    
    def should_collect_attributes(self, question: str, context: Dict[str, Any]) -> LLMResponse:
        """
        Determine if we should ask clarifying questions vs direct search.
        
        Centralizes refinement decision logic.
        """
        try:
            should_refine = self.refinement_llm.should_ask_question(question, context)
            
            return LLMResponse(
                success=True,
                result={"should_collect": should_refine}
            )
            
        except Exception as e:
            logger.error(f"Failed refinement decision: {e}")
            # Default to collecting attributes on error
            return LLMResponse(
                success=True,
                result={"should_collect": True}
            )
    
    def generate_search_query(
        self, 
        question: str, 
        context: Dict[str, Any], 
        category: str
    ) -> LLMResponse:
        """
        Generate SQL query for search.
        
        Centralizes SQL generation with proper error handling.
        """
        try:
            # Map category to table name
            table_mapping = {
                "printers": "printers",
                "laptops": "laptops", 
                "computers": "computers",
                "smartphones": "smartphones"
            }
            
            table_name = table_mapping.get(category, "products")
            
            sql_query = self.sql_llm.generate_sql(question, context, table_name)
            
            return LLMResponse(
                success=True,
                result={"sql": sql_query, "table": table_name}
            )
            
        except Exception as e:
            logger.error(f"Failed SQL generation: {e}")
            # Fallback to simple query
            fallback_sql = f"SELECT * FROM products WHERE product_type_id = (SELECT id FROM product_types WHERE name = '{category}')"
            
            return LLMResponse(
                success=False,
                error="sql_generation_failed",
                result={"sql": fallback_sql, "table": "products"}
            )
    
    def generate_attribute_question(
        self, 
        attribute_name: str,
        question: str,
        context: Dict[str, Any]
    ) -> LLMResponse:
        """
        Generate contextual attribute questions.
        
        Optional enhancement - can fallback to static questions.
        """
        try:
            # Use refinement LLM to generate contextual question
            refined_question = self.refinement_llm.generate_refinement_question(
                question, 
                {**context, "target_attribute": attribute_name}
            )
            
            return LLMResponse(
                success=True,
                result={"question": refined_question}
            )
            
        except Exception as e:
            logger.warning(f"Failed to generate contextual question for {attribute_name}: {e}")
            # Fallback to static questions handled by AttributeCollector
            return LLMResponse(
                success=False,
                error="question_generation_failed",
                result={"question": None}
            )


class MockLLMOrchestrator(LLMOrchestrator):
    """
    Mock implementation for testing and development.
    
    Provides predictable responses without Azure LLM calls.
    """
    
    def __init__(self):
        # Don't call super().__init__ since we don't need real LLMs
        pass
    
    def check_relevance_and_category(self, question: str) -> LLMResponse:
        """Mock relevance and category detection."""
        question_lower = question.lower()
        
        # Simple keyword-based detection
        categories = {
            "printer": "printers",
            "laptop": "laptops", 
            "computer": "computers",
            "smartphone": "smartphones",
            "telefoon": "smartphones"
        }
        
        category = None
        for keyword, cat in categories.items():
            if keyword in question_lower:
                category = cat
                break
        
        relevant = category is not None
        
        return LLMResponse(
            success=True,
            result={"relevant": relevant, "category": category},
            confidence=0.8
        )
    
    def should_collect_attributes(self, question: str, context: Dict[str, Any]) -> LLMResponse:
        """Mock refinement decision - always collect attributes."""
        return LLMResponse(
            success=True,
            result={"should_collect": True}
        )
    
    def generate_search_query(
        self, 
        question: str, 
        context: Dict[str, Any], 
        category: str
    ) -> LLMResponse:
        """Mock SQL generation."""
        sql = f"SELECT * FROM products WHERE product_type_id = (SELECT id FROM product_types WHERE name = '{category}')"
        
        return LLMResponse(
            success=True,
            result={"sql": sql, "table": "products"}
        )


def create_llm_orchestrator(use_mocks: bool = False) -> LLMOrchestrator:
    """
    Factory function for LLM orchestrator with dependency injection.
    
    Makes testing easy and reduces coupling.
    """
    if use_mocks:
        return MockLLMOrchestrator()
    
    # Import real LLMs only when needed
    from ..llms import azure_llm_set
    
    try:
        relevance_llm, sql_llm, refinement_llm = azure_llm_set.create_azure_llm_set()
        return LLMOrchestrator(relevance_llm, sql_llm, refinement_llm)
    except Exception as e:
        logger.warning(f"Failed to create Azure LLMs, falling back to mocks: {e}")
        return MockLLMOrchestrator()


"""
Benefits of this orchestration pattern:

1. **Dependency Injection**: Easy to test with mocks
2. **Centralized Error Handling**: Consistent error responses  
3. **Protocol-Based Design**: Clear interfaces, loose coupling
4. **Single Responsibility**: Only handles LLM coordination
5. **Fallback Support**: Graceful degradation to mocks
6. **Consistent Response Format**: LLMResponse standardizes outputs

Replaces scattered try/catch blocks and LLM calls throughout conversation_loop.py
with clean, testable, reusable orchestration logic.
"""
