"""
Unit tests for SimplifiedConversationManager

Tests the refactored conversation management with dependency injection
to verify functionality and demonstrate improved testability.
"""

from unittest.mock import Mock

from pixie.core.conversation.attribute_collector import AttributeCollector
from pixie.core.conversation.flow_config import ConversationFlowManager
from pixie.core.conversation.llm_orchestrator import LLMOrchestrator, LLMResponse
from pixie.core.conversation.simplified_conversation_manager import (
    SimplifiedConversationManager,
)
from pixie.core.storage.pending_store import InMemoryPendingStore


class TestSimplifiedConversationManager:
    """Test suite demonstrating improved testability of refactored code."""

    def setup_method(self):
        """Setup clean test environment for each test."""
        self.search_fn = Mock(return_value=[{"id": "1", "name": "Test Product"}])
        self.pending_store = InMemoryPendingStore()

        # Create a mock LLM orchestrator with proper interface
        self.llm_orchestrator = Mock(spec=LLMOrchestrator)
        self.llm_orchestrator.check_relevance_and_category.return_value = LLMResponse(
            success=True, result={"relevant": True, "category": "printers"}
        )
        self.llm_orchestrator.should_collect_attributes.return_value = LLMResponse(
            success=True, result={"should_collect": True}
        )
        self.llm_orchestrator.generate_search_query.return_value = LLMResponse(
            success=True, result={"sql": "SELECT * FROM products", "table": "products"}
        )

        # flow_manager is now optional for backward compatibility
        self.flow_manager = ConversationFlowManager()

        self.manager = SimplifiedConversationManager(
            search_fn=self.search_fn,
            pending_store=self.pending_store,
            llm_orchestrator=self.llm_orchestrator,
            flow_manager=self.flow_manager,
        )

    def test_handle_new_question_relevant_printer(self):
        """Test new question flow for printer category."""
        question = "Ik zoek een nieuwe printer"

        response = self.manager.handle_new_question(question)

        # Should start attribute collection
        assert response.type == "ask_user"
        assert response.prompt is not None
        assert response.pending_id is not None
        assert "budget" in response.prompt.lower()

    def test_handle_new_question_not_relevant(self):
        """Test handling of non-relevant questions."""
        # Mock LLM to return not relevant
        self.llm_orchestrator.check_relevance_and_category = Mock(
            return_value=LLMResponse(
                success=True, result={"relevant": False, "category": None}
            )
        )

        response = self.manager.handle_new_question("Where is my mother?")

        assert response.type == "not_relevant"

    def test_handle_reply_budget_collection(self):
        """Test handling budget reply in conversation flow."""
        # Start a conversation first
        question = "Ik zoek een nieuwe printer"
        initial_response = self.manager.handle_new_question(question)
        pending_id = initial_response.pending_id

        # Reply with budget
        reply_response = self.manager.handle_reply(pending_id, "€150")

        # Should ask next question (brand)
        assert reply_response.type == "ask_user"
        assert reply_response.prompt is not None
        # Check for brand-related keywords in Dutch (either "merk" or "brand")
        prompt_lower = reply_response.prompt.lower()
        assert "merk" in prompt_lower or "brand" in prompt_lower

    def test_handle_reply_completion_flow(self):
        """Test complete conversation flow to results."""
        # Start conversation
        question = "Ik zoek een nieuwe printer"
        initial_response = self.manager.handle_new_question(question)
        pending_id = initial_response.pending_id

        # Reply with budget
        self.manager.handle_reply(pending_id, "€150")

        # Reply with brand
        self.manager.handle_reply(pending_id, "HP")

        # Should complete and return results
        final_response = self.manager.handle_reply(pending_id, "laser")

        assert final_response.type == "answer"
        # Verify search was called
        self.search_fn.assert_called()

    def test_max_iterations_fallback(self):
        """Test that max iterations triggers search fallback."""
        # Set low max iterations
        self.manager.max_iterations = 2

        # Start conversation
        question = "Ik zoek een nieuwe printer"
        initial_response = self.manager.handle_new_question(question)
        pending_id = initial_response.pending_id

        # Reply twice to reach max iterations
        self.manager.handle_reply(pending_id, "€150")
        final_response = self.manager.handle_reply(pending_id, "HP")

        # Should generate results after max iterations
        assert final_response.type == "answer"

    def test_invalid_pending_id(self):
        """Test handling of invalid pending ID."""
        response = self.manager.handle_reply("invalid-id", "test reply")

        assert response.type == "error"
        assert response.reason == "invalid_pending_id"

    def test_search_failure_handling(self):
        """Test graceful handling of search failures."""
        # Mock search to raise exception
        self.search_fn.side_effect = Exception("Search failed")

        # Complete a conversation flow
        question = "Ik zoek een nieuwe printer"
        initial_response = self.manager.handle_new_question(question)
        pending_id = initial_response.pending_id

        self.manager.handle_reply(pending_id, "€150")
        self.manager.handle_reply(pending_id, "HP")
        final_response = self.manager.handle_reply(pending_id, "laser")

        assert final_response.type == "error"
        assert final_response.reason == "search_failed"

    def test_no_results_found(self):
        """Test handling when search returns no results."""
        # Mock search to return empty list
        self.search_fn.return_value = []

        # Complete conversation flow
        question = "Ik zoek een nieuwe printer"
        initial_response = self.manager.handle_new_question(question)
        pending_id = initial_response.pending_id

        self.manager.handle_reply(pending_id, "€150")
        self.manager.handle_reply(pending_id, "HP")
        final_response = self.manager.handle_reply(pending_id, "laser")

        assert final_response.type == "no_results"


class TestAttributeCollector:
    """Test suite for the extracted AttributeCollector."""

    def test_get_next_question_printers(self):
        """Test getting next question for printers."""
        collector = AttributeCollector("printers")

        question = collector.get_next_question()

        assert question is not None
        assert question.name == "budget"
        assert "budget" in question.question.lower()

    def test_collect_attribute_normal_response(self):
        """Test collecting normal attribute response."""
        collector = AttributeCollector("printers")

        attr_value = collector.collect_attribute("budget", "€150")

        assert attr_value.name == "budget"
        assert attr_value.value == "€150"
        assert not attr_value.is_skipped

    def test_collect_attribute_skip_response(self):
        """Test collecting skipped attribute response."""
        collector = AttributeCollector("printers")

        attr_value = collector.collect_attribute("brand", "weet ik niet")

        assert attr_value.name == "brand"
        assert attr_value.is_skipped
        assert attr_value.confidence == 0.5

    def test_collection_completion(self):
        """Test determining when collection is complete."""
        collector = AttributeCollector("printers")

        # Not complete without budget
        assert not collector.is_collection_complete()

        # Collect budget and one other attribute
        collector.collect_attribute("budget", "€150")
        collector.collect_attribute("brand", "HP")

        # With default max_attributes=3 we need a third attribute (or iterations)
        # so the collector should NOT be complete yet after only two attributes.
        assert not collector.is_collection_complete()

        # After collecting one more attribute it should be complete
        collector.collect_attribute("technology", "laser")
        assert collector.is_collection_complete()

    def test_budget_normalization(self):
        """Test budget response normalization."""
        collector = AttributeCollector("printers")

        # Test different budget formats
        attr1 = collector.collect_attribute("budget", "150")
        assert attr1.value == "€150"

        attr2 = collector.collect_attribute("budget", "minder dan 200€")
        assert "minder dan" in attr2.value

    def test_get_collection_summary(self):
        """Test getting collection summary for search."""
        collector = AttributeCollector("printers")

        collector.collect_attribute("budget", "€150")
        collector.collect_attribute("brand", "HP")
        collector.collect_attribute("technology", "weet ik niet")  # skipped

        summary = collector.get_collection_summary()

        assert summary["category"] == "printers"
        assert summary["total_collected"] == 3
        assert len(summary["attributes"]) == 2  # Only non-skipped
        assert "budget" in summary["attributes"]
        assert "brand" in summary["attributes"]
        assert "technology" not in summary["attributes"]  # Skipped


"""
Benefits of the refactored architecture:

1. **Easy Mocking**: Clean interfaces make dependency injection simple
2. **Isolated Testing**: Each component can be tested independently  
3. **Clear Responsibilities**: Single-purpose classes are easier to understand
4. **Improved Maintainability**: Changes to one component don't ripple everywhere
5. **Better Error Handling**: Centralized error responses and logging

The refactored code demonstrates significant improvements in:
- Code clarity and readability (150 lines vs 447 lines)
- Testability through dependency injection
- Maintainability through separation of concerns
- Error handling through centralized response patterns


Benefits of the refactored testing approach:

1. **Easy Mocking**: Clean interfaces make dependency injection simple
2. **Isolated Testing**: Each component can be tested independently  
3. **Clear Test Structure**: Tests focus on specific behaviors
4. **Comprehensive Coverage**: All edge cases easily testable
5. **Fast Execution**: No real LLM calls needed for unit tests
6. **Maintainable**: Changes to implementation don't break all tests

The original conversation_loop.py was nearly impossible to unit test
due to tight coupling and complex state management. These refactored
components enable proper test-driven development.
"""
