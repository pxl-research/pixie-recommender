from fastapi.testclient import TestClient
from apps.api.main import app


client = TestClient(app)


def test_ask_e2e():
    question = "Hoe werkt dit?"
    r = client.post("/ask", json={"question": question})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "answer"
    assert question in data["text"]
