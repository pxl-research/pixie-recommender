import logging

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_trace_id_in_logs(caplog):
    caplog.set_level(logging.INFO)
    r = client.post("/ask", json={"question": "log this"})
    assert r.status_code == 200

    # at least one captured record should have a trace_id attribute set
    has_trace = any(getattr(rec, "trace_id", None) for rec in caplog.records)
    assert has_trace
