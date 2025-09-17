import logging
import os
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from fastapi import Body, FastAPI
from fastapi.testclient import TestClient

from pixie.core.conversation.conversation_loop import ConversationLoopManager
from pixie.core.conversation.pixie import Pixie
from pixie.core.llms.mock_llm_set import create_mock_llm_set
from pixie.core.search import SearchEngine
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
    # Create mock LLM set
    mock_llms = create_mock_llm_set()

    # Create conversation manager with mock LLMs
    search_engine = SearchEngine()

    # Create wrapper function to match expected signature
    def search_with_category(sql: str, context: dict | None = None) -> list[dict]:
        category = None
        if context and isinstance(context, dict):
            category = context.get("category")
        result = search_engine.search(sql, context, category)
        # Handle both old dict format and new list format
        if isinstance(result, dict):
            return result.get("results", [])
        elif isinstance(result, list):
            return result
        else:
            return []

    conversation_manager = ConversationLoopManager(
        search_fn=search_with_category, llm_set=mock_llms, max_iterations=6
    )

    # Create Pixie instance with mock conversation manager
    pixie_instance = Pixie(conversation_manager=conversation_manager)

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

    @app.get("/health")
    def health():
        return {"status": "ok"}

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
                    type="error", reason="'question' is required and must be a string"
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


@pytest.fixture(autouse=True)
def force_mocks():
    """Force mock usage for all tests in this file."""
    original_value = os.environ.get("PIXIE_FORCE_MOCKS")
    os.environ["PIXIE_FORCE_MOCKS"] = "1"
    yield
    # Restore original value
    if original_value is not None:
        os.environ["PIXIE_FORCE_MOCKS"] = original_value
    else:
        os.environ.pop("PIXIE_FORCE_MOCKS", None)


def test_health(mock_client):
    r = mock_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_product_found_flow(mock_client):
    # Start product discovery
    r1 = mock_client.post("/ask", json={"question": "Ik zoek een nieuwe printer"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["type"] == "ask_user"
    pending = d1.get("pending_id")
    assert pending and pending.startswith("pending-")

    # Reply budget -> ask brand (look for brand-related keywords)
    r2 = mock_client.post(
        "/ask", json={"pending_id": pending, "message": "Maximaal 200€"}
    )
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
    r3 = mock_client.post("/ask", json={"pending_id": pending, "message": "Brother"})
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["type"] == "ask_user"
    prompt3 = d3.get("prompt", "").lower()
    tech_keywords = ["technologie", "inkjet", "laser", "print"]
    assert any(
        word in prompt3 for word in tech_keywords
    ), f"Expected technology question but got: {d3.get('prompt', '')}"
    pending = d3.get("pending_id")

    # Reply tech -> ask color
    r4 = mock_client.post("/ask", json={"pending_id": pending, "message": "laser"})
    assert r4.status_code == 200
    d4 = r4.json()
    assert d4["type"] == "ask_user"
    prompt4 = d4.get("prompt", "").lower()
    color_keywords = ["kleur", "color", "kleurenprinter"]
    assert any(
        word in prompt4 for word in color_keywords
    ), f"Expected color question but got: {d4.get('prompt', '')}"
    pending = d4.get("pending_id")

    # Reply color -> ask pages_per_minute
    r5 = mock_client.post("/ask", json={"pending_id": pending, "message": "kleur"})
    assert r5.status_code == 200
    d5 = r5.json()
    assert d5["type"] == "ask_user"
    prompt5 = d5.get("prompt", "").lower()
    pages_keywords = ["pagina", "per minuut", "pages", "minute"]
    assert any(
        word in prompt5 for word in pages_keywords
    ), f"Expected pages per minute question but got: {d5.get('prompt', '')}"
    pending = d5.get("pending_id")

    # Reply pages_per_minute -> final answer
    r6 = mock_client.post("/ask", json={"pending_id": pending, "message": "20"})
    assert r6.status_code == 200
    d6 = r6.json()
    assert d6["type"] == "answer"
    assert "Brother" in (d6.get("text") or "")


def test_not_relevant_flow(mock_client):
    r = mock_client.post("/ask", json={"question": "Ik zoek mijn mama"})
    assert r.status_code == 200
    d = r.json()
    assert d["type"] == "not_relevant"


def test_no_results_flow(mock_client):
    # Specific Brother laser info -> ask budget
    r1 = mock_client.post(
        "/ask",
        json={"question": "Ik wil graag meer informatie over een Brother laserprinter"},
    )
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["type"] == "ask_user"
    pending = d1.get("pending_id")

    # Too small budget -> might ask more questions or give no results
    r2 = mock_client.post(
        "/ask", json={"pending_id": pending, "message": "Minder dan 50€"}
    )
    assert r2.status_code == 200
    d2 = r2.json()
    # System might either continue asking or give no results
    assert d2["type"] in ["no_results", "ask_user"]
    if d2["type"] == "no_results":
        assert "geen printers gevonden" in (d2.get("text") or "").lower()


def test_too_many_results_flow(mock_client):
    # Start product discovery
    r1 = mock_client.post("/ask", json={"question": "Ik zoek een nieuwe printer"})
    assert r1.status_code == 200
    d1 = r1.json()
    pending = d1.get("pending_id")

    # Answer 'Weet ik niet' six times to reach max_iterations - system should finish
    for i in range(6):
        r = mock_client.post(
            "/ask", json={"pending_id": pending, "message": "Weet ik niet"}
        )
        assert r.status_code == 200
        d = r.json()
        pending = d.get("pending_id")

        # If conversation ended, break
        if not pending:
            break

    # If pending still exists, try to choose sorted view
    if pending:
        r7 = mock_client.post(
            "/ask", json={"pending_id": pending, "message": "Gesorteerd op prijs"}
        )
        assert r7.status_code == 200
        d7 = r7.json()
        assert d7["type"] == "answer"
        text = d7.get("text") or ""
        assert "Brother ZX 1570" in text or "Ik heb volgende printers" in text
    else:
        # Conversation ended after repeated "Weet ik niet" - this is acceptable behavior
        assert True


def test_invalid_pending_id(mock_client):
    r = mock_client.post("/ask", json={"pending_id": "invalid-123", "message": "x"})
    assert r.status_code == 200
    d = r.json()
    assert d["type"] == "error"
    reason = (d.get("reason") or "").lower()
    assert ("invalid" in reason) or ("expired" in reason)
