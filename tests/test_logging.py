import logging
import os

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


@pytest.fixture(autouse=True)
def force_mocks():
    """Force mock usage for all tests in this file to avoid Azure LLM initialization."""
    original_value = os.environ.get("PIXIE_FORCE_MOCKS")
    os.environ["PIXIE_FORCE_MOCKS"] = "1"
    yield
    # Restore original value
    if original_value is not None:
        os.environ["PIXIE_FORCE_MOCKS"] = original_value
    else:
        os.environ.pop("PIXIE_FORCE_MOCKS", None)

client = TestClient(app)


def test_trace_id_in_logs(caplog):
    caplog.set_level(logging.INFO)
    r = client.post("/ask", json={"question": "log this"})
    assert r.status_code == 200

    # at least one captured record should have a trace_id attribute set
    has_trace = any(getattr(rec, "trace_id", None) for rec in caplog.records)
    assert has_trace
