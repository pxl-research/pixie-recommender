"""API integration tests for product discovery flows."""

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


class TestAPIProductFlows:
    """Test product discovery flows through API endpoints."""

    def test_api_flow_1_printer_discovery(self):
        """Test Flow 1: Printer discovery through API."""
        # Start with printer request
        response = client.post("/ask", json={"question": "I'm looking for a printer"})
        assert response.status_code == 200

        data = response.json()

        if data["type"] == "ask_user":
            # Should have pending_id for continuation
            assert data["pending_id"] is not None
            pending_id = data["pending_id"]

            # Continue conversation with budget
            response = client.post(
                "/ask", json={"pending_id": pending_id, "message": "Maximum €200"}
            )
            assert response.status_code == 200
            data = response.json()

            # Continue until we get products or error out
            max_iterations = 3
            iteration = 0

            while data["type"] == "ask_user" and iteration < max_iterations:
                pending_id = data["pending_id"]
                response = client.post(
                    "/ask",
                    json={
                        "pending_id": pending_id,
                        "message": "Brother",  # Generic response
                    },
                )
                assert response.status_code == 200
                data = response.json()
                iteration += 1

            # Should eventually get some result
            assert data["type"] in ["product_list", "answer", "no_results"]

        elif data["type"] == "not_relevant":
            # Should have supported domains
            assert data["supported_domains"] is not None

        elif data["type"] == "product_list":
            # Direct product results
            assert data["products"] is not None
            assert len(data["products"]) > 0

    def test_api_flow_2_not_relevant(self):
        """Test Flow 2: Not relevant questions through API."""
        response = client.post("/ask", json={"question": "I'm looking for my mom"})
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "not_relevant"
        assert data["supported_domains"] is not None
        assert len(data["supported_domains"]) > 0

    def test_api_flow_3_no_results_scenario(self):
        """Test Flow 3: No results scenario through API."""
        # Try with very restrictive criteria
        response = client.post(
            "/ask", json={"question": "Brother laser printer under €10"}
        )
        assert response.status_code == 200

        data = response.json()

        # Might need refinement first or go directly to no results
        if data["type"] == "ask_user":
            # Go through refinement process
            max_iterations = 3
            iteration = 0

            while data["type"] == "ask_user" and iteration < max_iterations:
                pending_id = data["pending_id"]
                response = client.post(
                    "/ask",
                    json={
                        "pending_id": pending_id,
                        "message": "Under €10",  # Very low budget
                    },
                )
                assert response.status_code == 200
                data = response.json()
                iteration += 1

        # Should eventually result in no results or empty product list
        if data["type"] == "product_list":
            assert len(data["products"]) == 0
        elif data["type"] == "no_results":
            assert (
                "no" in data["text"].lower() or "unfortunately" in data["text"].lower()
            )

    def test_api_backward_compatibility(self):
        """Test that non-product questions still work through API."""
        # Test original question types
        response = client.post(
            "/ask", json={"question": "Wat is de hoofdstad van Frankrijk?"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "answer"
        assert data["text"] is not None

        # Test vague question
        response = client.post(
            "/ask", json={"question": "vertel eens wat meer algemeen"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "ask_user"
        assert data["pending_id"] is not None

    def test_api_error_handling(self):
        """Test API error handling."""
        # Test invalid pending_id
        response = client.post(
            "/ask", json={"pending_id": "invalid-id", "message": "some message"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "error"

        # Test missing required fields
        response = client.post("/ask", json={})
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "error"

        # Test empty question
        response = client.post("/ask", json={"question": ""})
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "error"

    def test_api_response_schemas(self):
        """Test that API responses match expected schemas."""
        # Test product_list response schema
        response = client.post("/ask", json={"question": "show me printers"})
        assert response.status_code == 200

        data = response.json()

        # Verify required fields exist based on response type
        assert "type" in data

        if data["type"] == "product_list":
            assert "products" in data
            assert "text" in data
            assert isinstance(data["products"], list)

            if len(data["products"]) > 0:
                product = data["products"][0]
                required_fields = [
                    "id",
                    "name",
                    "price",
                    "brand",
                    "category",
                    "description",
                ]
                for field in required_fields:
                    assert field in product

        elif data["type"] == "ask_user":
            assert "prompt" in data
            assert "pending_id" in data

        elif data["type"] == "not_relevant":
            assert "text" in data
            assert "supported_domains" in data

        elif data["type"] == "no_results":
            assert "text" in data

    def test_api_trace_id_header(self):
        """Test that trace ID header is present in responses."""
        response = client.post("/ask", json={"question": "test"})
        assert response.status_code == 200
        assert "X-Trace-Id" in response.headers

    def test_api_health_check(self):
        """Test API health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_api_multiple_conversation_turns(self):
        """Test multiple conversation turns through API."""
        # Start conversation
        response = client.post("/ask", json={"question": "I want a printer"})
        assert response.status_code == 200

        data = response.json()

        if data["type"] == "ask_user":
            pending_id = data["pending_id"]

            # First reply
            response = client.post(
                "/ask", json={"pending_id": pending_id, "message": "Between €150-€300"}
            )
            assert response.status_code == 200
            data = response.json()

            # Second reply if needed
            if data["type"] == "ask_user":
                pending_id = data["pending_id"]
                response = client.post(
                    "/ask", json={"pending_id": pending_id, "message": "HP"}
                )
                assert response.status_code == 200
                data = response.json()

                # Should eventually get some result
                assert data["type"] in ["product_list", "ask_user", "no_results"]
