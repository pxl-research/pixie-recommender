import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from apps.api.main import app
from pixie.core.contracts import AskResponse
from pixie.core.pixie import FakeRAGAdapter, FakeTabularRAG, Orchestrator, Pixie

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ask_endpoint():
    # Test basic question flow - LLM now gives direct answer for "what is" questions
    r = client.post("/ask", json={"question": "Wat is Pixie?"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "answer"  # LLM considers "Wat is X?" answerable

    # Test specific question that should get direct answer
    r = client.post("/ask", json={"question": "Wat is de hoofdstad van Nederland?"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "answer"
    assert "X-Trace-Id" in r.headers

    # Test vague question that triggers ask_user flow
    r = client.post("/ask", json={"question": "vertel eens wat meer algemeen"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "ask_user"
    assert "pending_id" in data


def test_reply_flow():
    # Test unified /ask endpoint for reply flow
    # First get a real pending_id from /ask
    r1 = client.post("/ask", json={"question": "vertel eens wat algemeen"})
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["type"] == "ask_user"
    pending_id = data1["pending_id"]

    # Then use /ask endpoint with pending_id (unified flow)
    r2 = client.post(
        "/ask",
        json={"pending_id": pending_id, "message": "extra specifieke context hier"},
    )
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["type"] == "answer"

    # Test invalid pending_id on unified /ask
    r3 = client.post(
        "/ask", json={"pending_id": "invalid-123", "message": "extra context"}
    )
    assert r3.status_code == 200
    data3 = r3.json()
    assert data3["type"] == "error"


def test_pixie_core_unit():
    """Test core Pixie functionality with LLM-like decisions."""
    pixie = Pixie()

    # Test specific question that gets direct answer
    res = pixie.answer("Wat is de hoofdstad van Frankrijk?")
    assert isinstance(res, AskResponse)
    assert res.type == "answer"
    assert res.text is not None
    assert "mock" in res.text.lower()

    # Test vague question that triggers ask_user
    res = pixie.answer("vertel eens meer algemeen")  # More explicitly vague
    assert isinstance(res, AskResponse)
    assert res.type == "ask_user"
    assert res.pending_id is not None


def test_pixie_orchestrator_integration():
    """Test Pixie using orchestrator for different question types."""
    pixie = Pixie()

    # Test data question → should get combined answer
    res = pixie.answer("Geef me cijfers over verkoop")
    assert res.type == "answer"
    assert res.text is not None
    assert "mock" in res.text.lower()
    assert "cijfers" in res.text.lower()

    # Test vague question → should trigger ask_user with unique pending_id
    res = pixie.answer("Vertel eens wat algemeen")
    assert res.type == "ask_user"
    assert res.pending_id is not None
    assert res.pending_id.startswith("pending-")

    # Test simple question → should get text-only answer
    res = pixie.answer("Wat is je naam?")
    assert res.type == "answer"
    assert res.text is not None
    assert "mock" in res.text.lower()


def test_pending_id_management():
    """Test proper pending ID generation and state management."""
    pixie = Pixie()

    # Generate ask_user response
    res = pixie.answer("Vertel eens wat algemeen")
    assert res.type == "ask_user"
    pending_id = res.pending_id
    assert pending_id is not None

    # Valid reply should work
    reply_res = pixie.reply(pending_id, "Ik wil weten over verkoop cijfers")
    assert reply_res.type == "answer"
    assert reply_res.text is not None

    # Reusing same pending_id should fail (already resolved)
    error_res = pixie.reply(pending_id, "Another reply")
    assert error_res.type == "error"
    assert error_res.reason is not None
    assert "ongeldig" in error_res.reason.lower()

    # Invalid pending_id should fail
    error_res2 = pixie.reply("invalid-id", "Some reply")
    assert error_res2.type == "error"
    assert error_res2.reason is not None
    assert "ongeldig" in error_res2.reason.lower()


def test_api_error_handling():
    """Test API error handling for various edge cases."""

    # Test missing question on /ask
    r = client.post("/ask", json={})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "error"
    assert "question" in data["reason"].lower()

    # Test empty question on /ask
    r = client.post("/ask", json={"question": ""})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "error"
    assert "non-empty" in data["reason"].lower()

    # Test whitespace-only question on /ask
    r = client.post("/ask", json={"question": "   "})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "error"
    assert "non-empty" in data["reason"].lower()

    # Test pending_id on /ask (should redirect to /reply)
    r = client.post("/ask", json={"pending_id": "test", "message": "test"})
    # Test pending_id on /ask without message (should give error)
    r = client.post("/ask", json={"pending_id": "test-123"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "error"
    assert "message' is required" in data["reason"]

    # Test missing message on unified /ask with pending_id
    r = client.post("/ask", json={"pending_id": "test-123"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "error"
    assert "message' is required" in data["reason"]

    # Test empty message on unified /ask with pending_id
    r = client.post("/ask", json={"pending_id": "test-123", "message": ""})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "error"
    assert "non-empty string" in data["reason"]


def test_v02_complete_e2e_flow():
    """
    Complete E2E test for v0.2 acceptance criteria:
    vague question → ask_user → reply → answer.
    """

    # Step 1: Ask vague question, expect ask_user response
    ask_response = client.post(
        "/ask", json={"question": "Vertel eens wat meer algemeen"}
    )
    assert ask_response.status_code == 200
    ask_data = ask_response.json()

    assert ask_data["type"] == "ask_user"
    assert ask_data["prompt"] is not None
    assert "specifieke informatie" in ask_data["prompt"]
    assert ask_data["pending_id"] is not None
    assert ask_data["pending_id"].startswith("pending-")

    pending_id = ask_data["pending_id"]

    # Step 2: Reply with specific context using unified /ask endpoint
    reply_response = client.post(
        "/ask",
        json={
            "pending_id": pending_id,
            "message": "Ik wil graag informatie over verkoop cijfers en statistieken",
        },
    )
    assert reply_response.status_code == 200
    reply_data = reply_response.json()

    assert reply_data["type"] == "answer"
    assert reply_data["text"] is not None
    assert len(reply_data["text"]) > 0

    # Verify the answer contains context from both original and follow-up
    text_lower = reply_data["text"].lower()
    assert "mock" in text_lower  # Basic mock response

    # Step 3: Try to reuse same pending_id using unified /ask, expect error
    reuse_response = client.post(
        "/ask", json={"pending_id": pending_id, "message": "Another message"}
    )
    assert reuse_response.status_code == 200
    reuse_data = reuse_response.json()

    assert reuse_data["type"] == "error"
    assert "ongeldig" in reuse_data["reason"].lower()


def test_orchestrator_decision_scenarios():
    """Test orchestrator makes correct decisions for different question types."""

    # Scenario 1: Data question → direct answer with tabular data
    data_response = client.post(
        "/ask", json={"question": "Geef me cijfers over verkoop"}
    )
    assert data_response.status_code == 200
    data_json = data_response.json()

    assert data_json["type"] == "answer"
    assert "cijfers" in data_json["text"].lower()
    assert "tabeldata" in data_json["text"].lower()

    # Scenario 2: Specific factual question → direct text answer
    fact_response = client.post(
        "/ask", json={"question": "Wat is de hoofdstad van Frankrijk?"}
    )
    assert fact_response.status_code == 200
    fact_json = fact_response.json()

    assert fact_json["type"] == "answer"
    assert "frankrijk" in fact_json["text"].lower()

    # Scenario 3: Very vague question → ask_user
    vague_response = client.post("/ask", json={"question": "Vertel eens meer info"})
    assert vague_response.status_code == 200
    vague_json = vague_response.json()

    assert vague_json["type"] == "ask_user"
    assert vague_json["pending_id"] is not None


def test_api_headers_and_metadata():
    """Test that API responses include proper headers and metadata."""

    response = client.post("/ask", json={"question": "Test vraag"})

    # Check status and content type
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")

    # Check trace ID header is present
    assert "X-Trace-Id" in response.headers
    trace_id = response.headers["X-Trace-Id"]
    assert len(trace_id) > 0

    # Verify response structure matches AskResponse contract
    data = response.json()
    required_fields = ["type", "text", "prompt", "pending_id", "needed_info", "reason"]
    for field in required_fields:
        assert field in data


def test_askresponse_validation():
    """Test AskResponse validation fails with empty data."""
    with pytest.raises(ValidationError):
        AskResponse.model_validate({})


def test_fake_tabular_rag():
    """Test FakeTabularRAG component works correctly."""
    tabular = FakeTabularRAG()

    # Test with data query
    result = tabular.query("Geef me cijfers over verkoop")
    assert result["found_data"] is True
    assert "mock_data_table" in result["table"]

    # Test with non-data query
    result = tabular.query("Wat is de hoofdstad?")
    assert result["found_data"] is False


def test_orchestrator_analysis():
    """Test Orchestrator decision making logic (MCP-like)."""
    rag = FakeRAGAdapter()
    tabular = FakeTabularRAG()
    orchestrator = Orchestrator(rag, tabular)

    # Test specific question with data → LLM decides to use tabular data
    analysis = orchestrator.analyze_question("Geef me cijfers over verkoop")
    assert analysis["strategy"] == "answer_with_data"
    assert analysis["tabular_result"]["found_data"] is True

    # Test vague question → LLM decides to use ask_user tool
    analysis = orchestrator.analyze_question("Vertel eens wat meer algemeen")
    assert analysis["strategy"] == "ask_user"

    # Test specific question without data → LLM gives direct text answer
    analysis = orchestrator.analyze_question("Wat is de hoofdstad van Frankrijk?")
    assert analysis["strategy"] == "answer_text_only"
