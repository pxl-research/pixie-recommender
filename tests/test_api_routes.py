import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from apps.api.main import app
from pixie.core.contracts import AskResponse
from pixie.core.pixie import Pixie, FakeTabularRAG

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ask_endpoint():
    # Test basic question flow
    r = client.post("/ask", json={"question": "Wat is Pixie?"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "answer"
    assert "mock" in data["text"]
    assert "X-Trace-Id" in r.headers

    # Test ask_user flow
    r = client.post("/ask", json={"question": "meer info please"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "ask_user"
    assert "pending_id" in data


def test_reply_flow():
    # Test reply flow
    r = client.post("/ask", json={"pending_id": "test-123", "message": "extra context"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "answer"
    assert "received reply" in data["text"]


def test_pixie_core_unit():
    """Test core Pixie functionality directly."""
    q = "Wie ben je?"
    pixie = Pixie()
    res = pixie.answer(q)
    assert isinstance(res, AskResponse)
    assert res.type == "answer"
    assert getattr(res, "text", None) == f"(mock) antwoord op: {q}"


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
