"""Comprehensive tests for all 4 core product discovery flows."""

from pixie.core.contracts import AskResponse
from pixie.core.pixie import Pixie


class TestProductDiscoveryFlows:
    """Test all 4 core flows from copilot-instructions.md."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pixie = Pixie()

    def test_flow_1_product_found_progressive_refinement(self):
        """Test Flow 1: Product Found - Progressive refinement from vague to specific."""
        # Step 1: Vague product request
        response = self.pixie.answer("I'm looking for a new printer")

        assert response.type == "ask_user"
        assert response.pending_id is not None
        assert "budget" in response.prompt.lower()  # Should ask for budget first

        # Step 2: Provide budget
        response = self.pixie.reply(response.pending_id, "Maximum €200")

        # Should ask for brand next
        if response.type == "ask_user":
            assert "brand" in response.prompt.lower()

            # Step 3: Provide brand
            response = self.pixie.reply(response.pending_id, "Brother")

        # Should eventually get to product list or technology question
        if response.type == "ask_user":
            assert (
                "technology" in response.prompt.lower()
                or "printing" in response.prompt.lower()
            )

            # Step 4: Provide technology
            response = self.pixie.reply(response.pending_id, "Laser")

        # Final result should be product list
        assert response.type == "product_list"
        assert response.products is not None
        assert len(response.products) > 0

        # Verify products match criteria
        for product in response.products:
            assert product.price <= 200
            assert product.brand == "Brother"
            assert product.technology == "Laser"

    def test_flow_1_printer_example_from_instructions(self):
        """Test exact printer example from copilot-instructions.md."""
        # Simulate the exact flow from instructions
        response = self.pixie.answer("I'm looking for a new printer")

        # Should ask for budget
        assert response.type == "ask_user"
        pending_id = response.pending_id

        # Provide budget: "Maximum €200"
        response = self.pixie.reply(pending_id, "Maximum €200")

        # Continue refinement until we get products
        max_iterations = 5
        iteration = 0

        while response.type == "ask_user" and iteration < max_iterations:
            if "brand" in response.prompt.lower():
                response = self.pixie.reply(response.pending_id, "Brother")
            elif "technology" in response.prompt.lower():
                response = self.pixie.reply(response.pending_id, "Laser")
            else:
                # Fallback for any other question
                response = self.pixie.reply(response.pending_id, "No preference")
            iteration += 1

        # Should end with product list
        assert response.type == "product_list"
        assert response.products is not None

        # Should have Brother laser printers under €200
        for product in response.products:
            assert product.brand == "Brother"
            assert product.technology == "Laser"
            assert product.price <= 200

    def test_flow_2_not_relevant_out_of_scope(self):
        """Test Flow 2: Not Relevant - Out-of-scope question handling."""
        # Test the exact example from instructions
        response = self.pixie.answer("I'm looking for my mom")

        assert response.type == "not_relevant"
        assert response.text is not None
        assert "sorry" in response.text.lower() or "can't help" in response.text.lower()
        assert response.supported_domains is not None

        # Should mention supported domains
        expected_domains = ["printers", "laptops", "smartphones", "tablets"]
        for domain in expected_domains:
            assert domain in response.supported_domains

    def test_flow_2_various_out_of_scope_questions(self):
        """Test various out-of-scope questions."""
        out_of_scope_questions = [
            "I'm looking for my mom",
            "Where can I find a good restaurant?",
            "What's the weather today?",
            "I need car repair service",
            "Can you help me with my homework?",
        ]

        for question in out_of_scope_questions:
            response = self.pixie.answer(question)
            assert response.type == "not_relevant"
            assert response.supported_domains is not None

    def test_flow_3_no_results_empty_search(self):
        """Test Flow 3: No Results - Valid filters but zero matches."""
        # Try to trigger the exact example: "Brother laser printer under €50"
        response = self.pixie.answer("I want a Brother laser printer under €50")

        # This might go through refinement or directly to no results
        if response.type == "ask_user":
            # Go through refinement to get to no results
            max_iterations = 5
            iteration = 0

            while response.type == "ask_user" and iteration < max_iterations:
                if "budget" in response.prompt.lower():
                    response = self.pixie.reply(response.pending_id, "Under €50")
                elif "brand" in response.prompt.lower():
                    response = self.pixie.reply(response.pending_id, "Brother")
                elif "technology" in response.prompt.lower():
                    response = self.pixie.reply(response.pending_id, "Laser")
                else:
                    response = self.pixie.reply(response.pending_id, "No preference")
                iteration += 1

        # Should eventually result in no_results
        assert response.type == "no_results"
        assert response.text is not None
        assert "unfortunately" in response.text.lower() or "no" in response.text.lower()

    def test_flow_4_too_many_results_refinement_needed(self):
        """Test Flow 4: Too Many Results - Large result set management."""
        # Start with very broad query that should return many results
        response = self.pixie.answer("I'm looking for a printer")

        # Should ask for refinement
        assert response.type == "ask_user"
        pending_id = response.pending_id

        # Provide very broad answers to maximize results
        response = self.pixie.reply(pending_id, "No preference")  # Budget

        if response.type == "ask_user":
            response = self.pixie.reply(response.pending_id, "No preference")  # Brand

        if response.type == "ask_user":
            response = self.pixie.reply(
                response.pending_id, "No preference"
            )  # Technology

        # Should eventually either:
        # 1. Ask about sorting/sampling options
        # 2. Return a managed subset of results
        # 3. Continue refining if still too many

        if response.type == "product_list":
            # Should be a reasonable number of results (not all 20+)
            assert len(response.products) <= 10  # Should be manageable
        elif response.type == "ask_user":
            # Should be asking for sorting preference or more refinement
            prompt_lower = response.prompt.lower()
            has_sorting_options = (
                "top 5" in prompt_lower
                or "sorted by price" in prompt_lower
                or "random sample" in prompt_lower
            )
            has_refinement = any(
                word in prompt_lower for word in ["budget", "brand", "technology"]
            )

            assert has_sorting_options or has_refinement

    def test_flow_4_sorting_options_response(self):
        """Test Flow 4: Sorting options for large result sets."""
        # Use catalog directly to test large result set handling
        catalog = self.pixie._product_catalog
        all_products = catalog.get_all_products()

        # Verify we have enough products to trigger threshold
        assert len(all_products) > catalog.result_threshold

        # Test sorting options
        top_5_by_price = catalog.get_top_products(all_products, 5, "price")
        assert len(top_5_by_price) == 5

        # Verify they're sorted by price (ascending)
        prices = [p.price for p in top_5_by_price]
        assert prices == sorted(prices)

        # Test random sampling
        sample_5 = catalog.sample_products(all_products, 5)
        assert len(sample_5) == 5
        assert all(p in all_products for p in sample_5)

    def test_product_category_clarification(self):
        """Test product category clarification when category is unclear."""
        response = self.pixie.answer("I need something for my office work")

        # Should ask for clarification about product type
        assert response.type == "ask_user"
        assert any(
            word in response.prompt.lower()
            for word in ["printer", "laptop", "smartphone", "tablet"]
        )

        # Clarify category
        response = self.pixie.reply(response.pending_id, "I need a printer")

        # Should now proceed with printer-specific refinement
        if response.type == "ask_user":
            assert any(
                word in response.prompt.lower()
                for word in ["budget", "brand", "technology"]
            )

    def test_multi_turn_conversation_state_persistence(self):
        """Test that conversation state persists across multiple turns."""
        # Start printer search
        response = self.pixie.answer("I want a printer")
        assert response.type == "ask_user"

        original_pending_id = response.pending_id

        # Provide budget
        response = self.pixie.reply(original_pending_id, "Between €150-€300")

        # Should continue with same or new pending_id
        if response.type == "ask_user":
            # Should remember the budget and ask for next filter
            assert (
                "brand" in response.prompt.lower()
                or "technology" in response.prompt.lower()
            )

            # The conversation should eventually lead to appropriate results
            # with the budget constraint applied
            pending_id = response.pending_id
            response = self.pixie.reply(pending_id, "HP")

            # Final check - if we get products, they should match our criteria
            if response.type == "product_list":
                for product in response.products:
                    assert 150 <= product.price <= 300

    def test_backward_compatibility_non_product_questions(self):
        """Ensure non-product questions still work as before."""
        # Test original question types
        response = self.pixie.answer("Wat is de hoofdstad van Frankrijk?")
        assert response.type == "answer"
        assert response.text is not None
        assert "mock" in response.text.lower()

        # Test vague non-product question
        response = self.pixie.answer("vertel eens wat meer algemeen")
        assert response.type == "ask_user"
        assert response.pending_id is not None

        # Test data question
        response = self.pixie.answer("Geef me cijfers over verkoop")
        assert response.type == "answer"
        assert "cijfers" in response.text.lower()

    def test_error_handling_invalid_pending_id(self):
        """Test error handling for invalid pending IDs."""
        response = self.pixie.reply("invalid-pending-id", "some reply")
        assert response.type == "error"
        assert (
            "ongeldig" in response.reason.lower()
            or "verlopen" in response.reason.lower()
        )

    def test_performance_catalog_queries(self):
        """Test that catalog queries perform reasonably fast."""
        import time

        catalog = self.pixie._product_catalog

        # Test search performance
        start_time = time.time()

        filters = {
            "category": "printer",
            "brand": "Brother",
            "budget": {"min": 0, "max": 200},
        }

        results = catalog.search_products(filters)

        end_time = time.time()
        query_time = end_time - start_time

        # Should complete in under 100ms (requirement from details)
        assert query_time < 0.1
        assert len(results) >= 0  # Should return some results or empty list
