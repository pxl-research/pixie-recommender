import logging
import time
from contextlib import asynccontextmanager
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, Request
from pydantic import BaseModel

from pixie.core.conversation.pixie import Pixie
from pixie.core.utils import logging as pixie_logging
from pixie.core.utils.contracts import AskResponse
from pixie.core.utils.logging import configure_logging, trace_id_ctx

# Prepare structured logging as soon as the module loads.
pixie_logging.configure_logging()


class AskPayload(BaseModel):
    question: Optional[str] = None
    pending_id: Optional[str] = None
    message: Optional[str] = None
    conversation_id: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(level=logging.INFO)
    logging.info("Starting Pixie Core API")
    app.state.pixie = Pixie()
    try:
        yield
    finally:
        app.state.pop("pixie", None)


def create_app() -> FastAPI:
    application = FastAPI(title="Pixie Core API", version="0.0.0", lifespan=lifespan)

    @application.middleware("http")
    async def add_trace_id(request, call_next):  # type: ignore[override]
        token = trace_id_ctx.set(str(uuid4()))
        try:
            response = await call_next(request)
            response.headers.setdefault("X-Trace-Id", trace_id_ctx.get())
            return response
        finally:
            trace_id_ctx.reset(token)

    return application


app = create_app()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return {
        "timestamp": int(time.time()),
        "status": "healthy",
        "version": "0.6.0",
        "active_conversations": 0,
    }


@app.post("/ask")
async def ask(payload: AskPayload, request: Request):
    logger = logging.getLogger(__name__)
    logger.info("api.ask", extra={"payload": payload.model_dump(exclude_none=True)})

    pixie: Pixie | None = getattr(request.app.state, "pixie", None)
    if pixie is None:
        logger.error("pixie_not_initialised")
        return AskResponse(type="error", reason="service_unavailable").dict()

    try:
        if payload.pending_id or payload.conversation_id:
            message = (payload.message or "").strip()
            if not message:
                return AskResponse(
                    type="error", reason="'message' is required when replying"
                ).dict()
            identifier = (payload.conversation_id or payload.pending_id or "").strip()
            if not identifier:
                return AskResponse(
                    type="error",
                    reason="'conversation_id' is required when replying",
                ).dict()
            resp = pixie.reply(identifier, message)
            return resp.dict()

        question = (payload.question or "").strip()
        if not question:
            return AskResponse(
                type="error", reason="'question' is required and must be a string"
            ).dict()

        resp = pixie.answer(question)
        return resp.dict()

    except Exception:
        logger.exception("unexpected_error_in_ask")
        return AskResponse(type="error", reason="Internal server error occurred").dict()
