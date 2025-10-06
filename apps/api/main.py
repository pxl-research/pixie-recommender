import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Body, FastAPI

from pixie.core.conversation.pixie import Pixie
from pixie.core.utils import logging as pixie_logging
from pixie.core.utils.contracts import AskResponse
from pixie.core.utils.logging import configure_logging, trace_id_ctx

# Prepare structured logging as soon as the module loads.
pixie_logging.configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(level=logging.INFO)
    logging.info("Starting Pixie Core API without embedded database")
    yield


app = FastAPI(title="Pixie Core API", version="0.0.0", lifespan=lifespan)


@app.middleware("http")
async def add_trace_id(request, call_next):
    token = trace_id_ctx.set(str(uuid4()))
    try:
        response = await call_next(request)
        response.headers.setdefault("X-Trace-Id", trace_id_ctx.get())
        return response
    finally:
        trace_id_ctx.reset(token)


_pixie_instance = Pixie()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    import time

    return {
        "timestamp": int(time.time()),
        "status": "healthy",
        "version": "0.6.0",
        "active_conversations": 0,
    }


@app.post("/ask")
def ask(req: dict = Body(...)):
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
