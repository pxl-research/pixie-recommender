import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from apps.api.main import app
from pixie.core.contracts import AskResponse
from pixie.core.pixie import Pixie, FakeTabularRAG, Orchestrator, FakeRAGAdapter

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ask_endpoint():
    # Test basic question flow - now triggers ask_user because orchestrator finds it vague
    r = client.post("/ask", json={"question": "Wat is Pixie?"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "ask_user"  # Orchestrator finds this too vague
    assert "pending_id" in data

    # Test specific question that should get direct answer
    r = client.post("/ask", json={"question": "Wat is de hoofdstad van Nederland?"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "answer"
    assert "X-Trace-Id" in r.headers

    # Test ask_user flow with explicit vague question
    r = client.post("/ask", json={"question": "vertel eens wat meer algemeen"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "ask_user"
    assert "pending_id" in data


def test_reply_flow():
    # Test invalid pending_id gives error (new behavior with proper validation)
    r = client.post("/ask", json={"pending_id": "invalid-123", "message": "extra context"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "error"
    assert "ongeldig" in data["reason"].lower()
    
    # Test valid flow: ask_user -> reply -> answer
    # First get a real pending_id
    r1 = client.post("/ask", json={"question": "vertel eens wat algemeen"})
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["type"] == "ask_user"
    pending_id = data1["pending_id"]
    
    # Then reply with that pending_id
    r2 = client.post("/ask", json={"pending_id": pending_id, "message": "Ik wil info over verkoop"})
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["type"] == "answer"
    assert "mock" in data2["text"].lower()


def test_pixie_core_unit():
    """Test core Pixie functionality with orchestrator decisions."""
    pixie = Pixie()
    
    # Test specific question that gets direct answer
    res = pixie.answer("Wat is de hoofdstad van Frankrijk?")
    assert isinstance(res, AskResponse)
    assert res.type == "answer"
    assert res.text is not None
    assert "mock" in res.text.lower()
    
    # Test vague question that triggers ask_user
    res = pixie.answer("Wie ben je?")  # This is now considered vague
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
    """Test Orchestrator decision making logic."""
    rag = FakeRAGAdapter()
    tabular = FakeTabularRAG()
    orchestrator = Orchestrator(rag, tabular)
    
    # Test specific question with data → high confidence  
    analysis = orchestrator.analyze_question("Geef me cijfers over verkoop")
    assert analysis["confidence"] > 0.7
    assert analysis["strategy"] == "answer_with_data"
    assert analysis["tabular_result"]["found_data"] is True
    
    # Test vague question → low confidence, ask_user
    analysis = orchestrator.analyze_question("Vertel eens wat meer")
    assert analysis["confidence"] < 0.7
    assert analysis["strategy"] == "ask_user"
    
    # Test specific question without data → text only
    analysis = orchestrator.analyze_question("Wat is de hoofdstad van Frankrijk?")
    assert analysis["strategy"] == "answer_text_only"
