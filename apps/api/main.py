import asyncio
import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Body, FastAPI

from pixie.core.conversation.pixie import Pixie
from pixie.core.utils import logging as pixie_logging
from pixie.core.utils.contracts import AskResponse
from pixie.core.utils.logging import configure_logging, trace_id_ctx

# Also configure logging at import time so test runners that create a
# TestClient during module import (common in test files) have the LogRecord
# factory and filters installed before any requests are processed.
pixie_logging.configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler with database initialization."""
    # Initialize logging
    configure_logging(level=logging.INFO)
    logging.info("Starting Pixie Core API...")

    # Initialize database with retry logic for container startup
    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            from pixie.core.database.seed import seed_database

            logging.info(f"Database initialization attempt {attempt + 1}/{max_retries}")

            # Seed database (migrations are handled by init.sql in Docker)
            seed_database()
            logging.info("Database seeding completed")
            break

        except Exception as e:
            logging.warning(
                f"Database initialization attempt {attempt + 1} failed: {e}"
            )
            if attempt == max_retries - 1:
                logging.error("Database initialization failed after all retries")
                # Continue anyway - the app might still work with existing data
                break
            else:
                logging.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)

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


@app.get("/debug/db-status")
def debug_db_status():
    """Debug endpoint to check database seeding status."""
    try:
        from sqlalchemy import text

        from pixie.core.database.connection import get_db_session
        from pixie.core.utils.config import get_config

        # Debug: log the actual database URL being used
        config = get_config()
        db_url = config.database.url

        with get_db_session() as session:
            # Check products
            result = session.execute(text("SELECT COUNT(*) FROM products"))
            product_count = result.scalar()

            # Check attribute definitions
            result = session.execute(text("SELECT COUNT(*) FROM attribute_definitions"))
            attr_def_count = result.scalar()

            # Check attribute values
            result = session.execute(
                text("SELECT COUNT(*) FROM product_attribute_values")
            )
            attr_val_count = result.scalar()

            return {
                "database_status": "connected",
                "database_url": db_url,  # Add for debugging
                "product_count": product_count,
                "attribute_definition_count": attr_def_count,
                "product_attribute_value_count": attr_val_count,
                "seeding_complete": (product_count or 0) > 0
                and (attr_def_count or 0) > 0
                and (attr_val_count or 0) > 0,
            }
    except Exception as e:
        return {"database_status": "error", "error": str(e), "seeding_complete": False}


@app.post("/debug/reset-db-connection")
def debug_reset_db_connection():
    """Debug endpoint to reset database configuration and engine cache."""
    try:
        from pixie.core.database.connection import reset_engine
        from pixie.core.utils.config import reset_config

        # Reset cached configuration and engine
        reset_config()
        reset_engine()

        # Test new connection
        from pixie.core.utils.config import get_config

        config = get_config()

        return {
            "status": "success",
            "message": "Database configuration and engine reset",
            "new_database_url": config.database.url,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


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
