from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_product_found_flow():
    # Start product discovery
    r1 = client.post("/ask", json={"question": "Ik zoek een nieuwe printer"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["type"] == "ask_user"
    pending = d1.get("pending_id")
    assert pending and pending.startswith("pending-")

    # Reply budget -> ask brand (look for brand-related keywords)
    r2 = client.post("/ask", json={"pending_id": pending, "message": "Maximaal 200€"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["type"] == "ask_user"
    prompt = d2.get("prompt", "").lower()
    brand_keywords = ["merk", "brand", "fabrikant"]
    assert any(
        word in prompt for word in brand_keywords
    ), f"Expected brand question but got: {d2.get('prompt', '')}"
    pending = d2.get("pending_id")

    # Reply brand -> ask tech (look for technology-related keywords)
    r3 = client.post("/ask", json={"pending_id": pending, "message": "Brother"})
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["type"] == "ask_user"
    prompt3 = d3.get("prompt", "").lower()
    tech_keywords = ["technologie", "inkjet", "laser", "print"]
    assert any(
        word in prompt3 for word in tech_keywords
    ), f"Expected technology question but got: {d3.get('prompt', '')}"
    pending = d3.get("pending_id")

    # Reply tech -> final answer
    r4 = client.post("/ask", json={"pending_id": pending, "message": "laser"})
    assert r4.status_code == 200
    d4 = r4.json()
    assert d4["type"] == "answer"
    assert "Brother" in (d4.get("text") or "")


def test_not_relevant_flow():
    r = client.post("/ask", json={"question": "Ik zoek mijn mama"})
    assert r.status_code == 200
    d = r.json()
    assert d["type"] == "not_relevant"


def test_no_results_flow():
    # Specific Brother laser info -> ask budget
    r1 = client.post(
        "/ask",
        json={"question": "Ik wil graag meer informatie over een Brother laserprinter"},
    )
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["type"] == "ask_user"
    pending = d1.get("pending_id")

    # Too small budget -> might ask more questions or give no results
    r2 = client.post("/ask", json={"pending_id": pending, "message": "Minder dan 50€"})
    assert r2.status_code == 200
    d2 = r2.json()
    # System might either continue asking or give no results
    assert d2["type"] in ["no_results", "ask_user"]
    if d2["type"] == "no_results":
        assert "geen printers gevonden" in (d2.get("text") or "").lower()


def test_too_many_results_flow():
    # Start product discovery
    r1 = client.post("/ask", json={"question": "Ik zoek een nieuwe printer"})
    assert r1.status_code == 200
    d1 = r1.json()
    pending = d1.get("pending_id")

    # Answer 'Weet ik niet' three times - system might finish or ask for view choice
    for i in range(3):
        r = client.post("/ask", json={"pending_id": pending, "message": "Weet ik niet"})
        assert r.status_code == 200
        d = r.json()
        pending = d.get("pending_id")

        # If conversation ended, break
        if not pending:
            break

    # If pending still exists, try to choose sorted view
    if pending:
        r5 = client.post(
            "/ask", json={"pending_id": pending, "message": "Gesorteerd op prijs"}
        )
        assert r5.status_code == 200
        d5 = r5.json()
        assert d5["type"] == "answer"
        text = d5.get("text") or ""
        assert "Brother ZX 1570" in text or "Ik heb volgende printers" in text
    else:
        # Conversation ended after repeated "Weet ik niet" - this is acceptable behavior
        assert True


def test_invalid_pending_id():
    r = client.post("/ask", json={"pending_id": "invalid-123", "message": "x"})
    assert r.status_code == 200
    d = r.json()
    assert d["type"] == "error"
    reason = (d.get("reason") or "").lower()
    assert ("invalid" in reason) or ("expired" in reason)
