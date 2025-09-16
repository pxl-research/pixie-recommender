import logging
import os
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from fastapi import Body, FastAPI
from fastapi.testclient import TestClient

from pixie.core.conversation.pixie import Pixie
from pixie.core.utils import logging as pixie_logging
from pixie.core.utils.contracts import AskResponse
from pixie.core.utils.logging import trace_id_ctx


@asynccontextmanager
async def _test_lifespan(app: FastAPI):
    # Configure logging at startup
    pixie_logging.configure_logging()
    yield


@pytest.fixture
def mock_client():
    """Create a TestClient with mock LLMs for testing."""
    # Force mock usage before importing anything that creates Pixie
    original_force_mocks = os.environ.get("PIXIE_FORCE_MOCKS")
    os.environ["PIXIE_FORCE_MOCKS"] = "1"

    try:
        # Create Pixie instance with forced mocks
        pixie_instance = Pixie()

        # Create FastAPI app
        app = FastAPI(title="Pixie Core API", version="0.0.0", lifespan=_test_lifespan)

        @app.middleware("http")
        async def add_trace_id(request, call_next):
            """Attach a per-request trace_id to the ContextVar."""
            token = trace_id_ctx.set(str(uuid4()))
            try:
                response = await call_next(request)
                response.headers.setdefault("X-Trace-Id", trace_id_ctx.get())
                return response
            finally:
                trace_id_ctx.reset(token)

        @app.post("/ask")
        def ask(req: dict = Body(...)):
            """Unified endpoint for both new questions and replies."""
            logger = logging.getLogger(__name__)
            logger.info("api.ask", extra={"payload": req})

            try:
                pending_id = req.get("pending_id")
                if pending_id:
                    message = req.get("message")
                    if not message or not isinstance(message, str):
                        return AskResponse(
                            type="error",
                            reason="'message' is required and must be a string",
                        ).dict()

                    resp = pixie_instance.reply(pending_id.strip(), message.strip())
                    return resp.dict()

                question = req.get("question")
                if not question or not isinstance(question, str):
                    return AskResponse(
                        type="error",
                        reason="'question' is required and must be a string",
                    ).dict()

                resp = pixie_instance.answer(question.strip())
                return resp.dict()

            except Exception:
                logger.exception("Unexpected error in /ask endpoint")
                return AskResponse(
                    type="error", reason="Internal server error occurred"
                ).dict()

        # Configure logging for tests
        pixie_logging.configure_logging()

        return TestClient(app)

    finally:
        # Restore original environment variable
        if original_force_mocks is not None:
            os.environ["PIXIE_FORCE_MOCKS"] = original_force_mocks
        else:
            os.environ.pop("PIXIE_FORCE_MOCKS", None)


def test_trace_id_in_logs(mock_client, caplog):
    caplog.set_level(logging.INFO)
    r = mock_client.post("/ask", json={"question": "log this"})
    assert r.status_code == 200

    # at least one captured record should have a trace_id attribute set
    has_trace = any(getattr(rec, "trace_id", None) for rec in caplog.records)
    assert has_trace
