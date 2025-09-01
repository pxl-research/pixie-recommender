from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Request

from pixie.core import logging as pixie_logging
from pixie.core.contracts import AskResponse, ReplyRequest
from pixie.core.pixie import Pixie


@asynccontextmanager
async def lifespan(app: FastAPI):
    # configure logging once at startup
    pixie_logging.configure_logging()
    yield


app = FastAPI(title="Pixie Core API", version="0.0.0", lifespan=lifespan)


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    """Assign a trace_id and make it available to structured logs."""
    trace_id = str(uuid4())
    pixie_logging.trace_id_ctx.set(trace_id)

    logging.getLogger("uvicorn.error").info(
        "request_start", extra={"path": request.url.path, "trace_id": trace_id}
    )

    try:
        response = await call_next(request)
    except Exception:
        logging.exception("unhandled_exception")
        raise

    logging.getLogger("uvicorn.error").info(
        "request_end",
        extra={
            "path": request.url.path,
            "status_code": getattr(response, "status_code", None),
            "trace_id": trace_id,
        },
    )

    try:
        response.headers["X-Trace-Id"] = trace_id
    except Exception:
        pass

    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: dict):
    logger = logging.getLogger(__name__)

    # single timestamp for request/response logs
    ts = datetime.now(timezone.utc).isoformat()
    logger.info("api.ask.request", extra={"payload": req, "ts": ts})

    pixie = Pixie()

    # Dispatch: reply (has pending_id) or new question (has question)
    if "pending_id" in req:
        rr = ReplyRequest.model_validate(req)
        resp = pixie.reply(rr.pending_id, rr.message)
    else:
        question = req.get("question")
        if not question:
            raise ValueError("'question' is required for new asks")
        resp = pixie.answer(question)

    # Log a compact summary of the response
    logger.info(
        "api.ask.response",
        extra={"response_type": getattr(resp, "type", None), "ts": ts},
    )

    return resp


# Note: /reply endpoint removed in favor of single /ask endpoint.
