import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Body, FastAPI

from pixie.core.conversation.pixie import Pixie
from pixie.core.utils import logging as pixie_logging
from pixie.core.utils.contracts import AskResponse
from pixie.core.utils.logging import trace_id_ctx

# Also configure logging at import time so test runners that create a
# TestClient during module import (common in test files) have the LogRecord
# factory and filters installed before any requests are processed.
pixie_logging.configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure logging at startup using the lifespan handler (replacement for on_event)
    pixie_logging.configure_logging()

    # Initialize database and seed data on startup
    try:
        from pixie.core.database.init import create_tables

        # Create tables if they don't exist
        create_tables()
        logging.info("Database tables created/verified successfully")

        # Try simple database seeding for critical data (printers)
        try:
            import sys

            sys.path.append("/app")
            from scripts.init_database import init_database_simple

            init_database_simple()
        except Exception as e:
            logging.warning(f"Simple database seeding failed, trying full seeding: {e}")
            # Fallback to full seeding
            try:
                from pixie.core.database.seed import seed_database

                seed_database()
                logging.info("Full database seeding completed successfully")
            except Exception as e2:
                logging.error(f"Full database seeding also failed: {e2}")

    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        # Continue anyway - the app might still work with existing data

    yield


# Configure FastAPI app with explicit lifespan handler to avoid on_event deprecation
app = FastAPI(title="Pixie Core API", version="0.0.0", lifespan=lifespan)


@app.middleware("http")
async def add_trace_id(request, call_next):
    """Attach a per-request trace_id to the ContextVar used by logging.TraceIdFilter.

    This ensures all LogRecords created while handling the request have a
    trace_id attribute and makes it available in response headers as
    X-Trace-Id for downstream correlation.
    """
    token = trace_id_ctx.set(str(uuid4()))
    try:
        response = await call_next(request)
        # expose trace id to client for correlation
        response.headers.setdefault("X-Trace-Id", trace_id_ctx.get())
        return response
    finally:
        trace_id_ctx.reset(token)


# Shared Pixie instance
_pixie_instance = Pixie()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    """Basic metrics endpoint for monitoring."""
    import time

    # Get basic conversation statistics
    if hasattr(_pixie_instance, "_pending_store"):
        pending_count = len(_pixie_instance._pending_store._store)
    else:
        pending_count = 0

    return {
        "timestamp": int(time.time()),
        "status": "healthy",
        "version": "0.6.0",
        "active_conversations": pending_count,
    }


@app.post("/ask")
def ask(req: dict = Body(...)):
    """Unified endpoint for both new questions and replies to pending questions.

    - If `pending_id` is present we treat the payload as a reply (requires `message`).
    - Otherwise `question` must be provided for a new ask.
    """
    logger = logging.getLogger(__name__)
    logger.info("api.ask", extra={"payload": req})

    try:
        pixie = _pixie_instance

        pending_id = req.get("pending_id")
        if pending_id:
            message = req.get("message")
            if not message or not isinstance(message, str):
                return AskResponse(
                    type="error", reason="'message' is required and must be a string"
                ).dict()

            resp = pixie.reply(pending_id.strip(), message.strip())
            return resp.dict()

        question = req.get("question")
        if not question or not isinstance(question, str):
            return AskResponse(
                type="error", reason="'question' is required and must be a string"
            ).dict()

        resp = pixie.answer(question.strip())
        return resp.dict()

    except Exception:
        logger.exception("Unexpected error in /ask endpoint")
        return AskResponse(type="error", reason="Internal server error occurred").dict()
