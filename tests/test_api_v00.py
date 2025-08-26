from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_ask_mock():
    r = client.post("/ask", json={"question": "Wat is Pixie?"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "answer"
    assert "mock" in data["text"]