"""Backward compatibility validation tests."""

from pixie.core.pixie import Pixie


class TestBackwardCompatibility:
    """Ensure all existing functionality continues to work without regression."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pixie = Pixie()

    def test_original_question_patterns_still_work(self):
        """Test that original question patterns from existing tests still work."""
        # These are the patterns from the original test_api_routes.py
        test_cases = [
            ("Wat is de hoofdstad van Frankrijk?", "answer"),
            ("vertel eens wat meer algemeen", "ask_user"),
            ("Geef me cijfers over verkoop", "answer"),
            ("Help me met informatie", "ask_user"),
            ("Hoeveel kost dit product?", "answer"),
            ("meer details graag", "ask_user"),
        ]

        for question, expected_type in test_cases:
            result = self.pixie.answer(question)

            # The type should match expectations or be compatible
            if expected_type == "answer":
                assert result.type in ["answer", "answer_with_data"]
                assert result.text is not None
            elif expected_type == "ask_user":
                assert result.type == "ask_user"
                assert result.pending_id is not None
                assert result.prompt is not None

    def test_original_ask_reply_flow_unchanged(self):
        """Test that original ask/reply flow works unchanged for non-product questions."""
        # Start with vague non-product question
        response = self.pixie.answer("vertel eens wat meer algemeen")
        assert response.type == "ask_user"
        assert response.pending_id is not None

        # Reply to it
        reply_response = self.pixie.reply(
            response.pending_id, "extra specifieke context hier"
        )
        assert reply_response.type == "answer"
        assert reply_response.text is not None

    def test_original_data_questions_unchanged(self):
        """Test that data-based questions still work as before."""
        response = self.pixie.answer("Geef me cijfers over verkoop")

        # Should get answer (possibly with data)
        assert response.type in ["answer", "answer_with_data"]
        assert response.text is not None
        assert "cijfers" in response.text.lower()

    def test_original_specific_questions_unchanged(self):
        """Test that specific questions get direct answers as before."""
        specific_questions = [
            "Wat is de hoofdstad van Frankrijk?",
            "Wanneer is de eerste wereldoorlog begonnen?",
            "Hoeveel is 2 + 2?",
            "Wie is de president van Amerika?",
        ]

        for question in specific_questions:
            response = self.pixie.answer(question)
            assert response.type == "answer"
            assert response.text is not None
            assert "mock" in response.text.lower()

    def test_original_error_handling_unchanged(self):
        """Test that error handling works as before."""
        # Test invalid pending_id
        response = self.pixie.reply("invalid-pending-id-12345", "some reply")
        assert response.type == "error"
        assert (
            "ongeldig" in response.reason.lower()
            or "verlopen" in response.reason.lower()
        )

    def test_original_orchestrator_decision_patterns_still_work(self):
        """Test that original orchestrator decision patterns are preserved."""
        # Test vague patterns -> ask_user
        vague_questions = [
            "meer info",
            "vertel eens",
            "wat meer",
            "help",
            "uitleg",
            "informatie",
            "details",
        ]

        for question in vague_questions:
            response = self.pixie.answer(question)
            # Should still trigger ask_user for vague non-product questions
            assert response.type == "ask_user"

    def test_original_tabular_rag_integration_unchanged(self):
        """Test that tabular RAG integration still works."""
        # These should trigger the tabular RAG
        data_questions = [
            "Geef me cijfers over verkoop",
            "Toon me data over gebruikers",
            "Wat zijn de statistieken van dit jaar?",
        ]

        for question in data_questions:
            response = self.pixie.answer(question)
            assert response.type == "answer"
            assert response.text is not None
            # Should include both mock text and tabular data
            assert "mock" in response.text.lower()
            assert (
                "cijfers" in response.text.lower()
                or "data" in response.text.lower()
                or "statistieken" in response.text.lower()
            )

    def test_performance_impact_minimal(self):
        """Test that performance impact is minimal for non-product queries."""
        import time

        # Test a bunch of non-product questions for performance
        questions = [
            "Wat is de hoofdstad van Frankrijk?",
            "vertel eens wat meer algemeen",
            "Geef me cijfers over verkoop",
            "Help me met informatie",
            "Hoeveel kost dit product?",
            "meer details graag",
        ]

        start_time = time.time()

        for question in questions:
            self.pixie.answer(question)

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete all 6 questions in reasonable time
        # Requirement: < 10ms overhead for non-product queries
        # With 6 questions, should be under 100ms total
        assert total_time < 0.1

    def test_original_pending_store_functionality_preserved(self):
        """Test that original pending store functionality is preserved."""
        # Create a non-product ask_user situation
        response = self.pixie.answer("help me with something")
        assert response.type == "ask_user"

        pending_id = response.pending_id

        # Test that we can retrieve and resolve as before
        pending_entry = self.pixie._pending_store.get_pending(pending_id)
        assert pending_entry is not None
        assert pending_entry.question == "help me with something"

        # Test reply works
        reply_response = self.pixie.reply(pending_id, "I need help with work")
        assert reply_response.type == "answer"

        # Test that pending entry is resolved
        resolved_entry = self.pixie._pending_store.get_pending(pending_id)
        assert resolved_entry is None

    def test_api_contracts_unchanged(self):
        """Test that API response contracts haven't broken existing clients."""
        # Test that all original response types still have required fields

        # Test answer response
        response = self.pixie.answer("Wat is de hoofdstad van Nederland?")
        if response.type == "answer":
            assert hasattr(response, "text")
            assert response.text is not None

        # Test ask_user response
        response = self.pixie.answer("help me")
        if response.type == "ask_user":
            assert hasattr(response, "prompt")
            assert hasattr(response, "pending_id")
            assert response.prompt is not None
            assert response.pending_id is not None

        # Test error response
        response = self.pixie.reply("invalid", "test")
        if response.type == "error":
            assert hasattr(response, "reason")
            assert response.reason is not None

    def test_original_imports_and_dependencies_unchanged(self):
        """Test that original imports and dependencies still work."""
        # Test that we can still import and use original classes
        from pixie.core.pixie import FakeRAGAdapter, FakeTabularRAG, Orchestrator, Pixie
        from pixie.core.contracts import AskResponse
        from pixie.core.pending_store import InMemoryPendingStore

        # Test that original constructor signatures still work
        rag = FakeRAGAdapter()
        tabular = FakeTabularRAG()
        orchestrator = Orchestrator(rag, tabular)
        store = InMemoryPendingStore()
        pixie = Pixie(rag, tabular, store)

        # Test basic functionality
        response = pixie.answer("test")
        assert isinstance(response, AskResponse)

    def test_logging_functionality_preserved(self):
        """Test that logging functionality is preserved."""
        import logging

        # Capture log messages
        log_messages = []

        class TestHandler(logging.Handler):
            def emit(self, record):
                log_messages.append(record.getMessage())

        logger = logging.getLogger("pixie.core.pixie")
        handler = TestHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        try:
            # Make some calls
            self.pixie.answer("test question")

            # Should have logged something
            assert len(log_messages) > 0

        finally:
            logger.removeHandler(handler)
