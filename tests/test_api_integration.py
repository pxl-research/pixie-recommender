from fastapi.testclient import TestClient

from apps.api.main import app


class TestAPIIntegration:
    """Integration tests for API endpoints with database backend."""

    def test_health_endpoint(self):
        """Test the health endpoint."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_metrics_endpoint(self):
        """Test the metrics endpoint."""
        client = TestClient(app)
        response = client.get("/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "active_conversations" in data

    def test_ask_endpoint_missing_question(self):
        """Test ask endpoint with missing question."""
        client = TestClient(app)
        response = client.post("/ask", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "error"
        assert "question" in data["reason"].lower()

    def test_ask_endpoint_invalid_question(self):
        """Test ask endpoint with invalid question type."""
        client = TestClient(app)
        response = client.post("/ask", json={"question": 123})

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "error"
        assert "question" in data["reason"].lower()

    def test_ask_endpoint_with_question(self):
        """Test ask endpoint with a valid question."""
        client = TestClient(app)
        response = client.post(
            "/ask", json={"question": "I need a printer under 500 euros"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should either return an answer or ask for more information
        assert data["type"] in ["answer", "ask_user", "error"]

        if data["type"] == "ask_user":
            # Should have a prompt for the next attribute
            assert "prompt" in data
            assert isinstance(data["prompt"], str)
            assert "pending_id" in data

    def test_reply_endpoint_missing_message(self):
        """Test reply endpoint with missing message."""
        client = TestClient(app)
        response = client.post("/ask", json={"pending_id": "test-id"})

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "error"
        assert "message" in data["reason"].lower()

    def test_reply_endpoint_invalid_message(self):
        """Test reply endpoint with invalid message type."""
        client = TestClient(app)
        response = client.post("/ask", json={"pending_id": "test-id", "message": 123})

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "error"
        assert "message" in data["reason"].lower()

    def test_conversation_flow_with_database(self):
        """Test a complete conversation flow that uses database attributes."""
        client = TestClient(app)

        # Start with a question about printers
        response1 = client.post(
            "/ask", json={"question": "I want to buy a printer for home use"}
        )

        assert response1.status_code == 200
        data1 = response1.json()

        # Should ask for the first attribute (budget)
        if data1["type"] == "ask_user":
            assert (
                "budget" in data1["prompt"].lower()
                or "vraag" in data1["prompt"].lower()
            )
            pending_id = data1["pending_id"]

            # Reply with budget information
            response2 = client.post(
                "/ask", json={"pending_id": pending_id, "message": "500 euros"}
            )

            assert response2.status_code == 200
            data2 = response2.json()

            # Should either ask for next attribute or provide answer
            assert data2["type"] in ["answer", "ask_user", "error"]

            if data2["type"] == "ask_user":
                # Should ask for brand preference
                assert (
                    "merk" in data2["prompt"].lower()
                    or "brand" in data2["prompt"].lower()
                )

    def test_trace_id_middleware(self):
        """Test that trace ID is added to response headers."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert "X-Trace-Id" in response.headers
        trace_id = response.headers["X-Trace-Id"]
        assert isinstance(trace_id, str)
        assert len(trace_id) > 0
