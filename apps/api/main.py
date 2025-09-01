from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Request

from pixie.core import logging as pixie_logging
from pixie.core.contracts import AskResponse, InteractRequest
from pixie.core.pixie import Pixie


@asynccontextmanager
async def lifespan(app: FastAPI):
    # configure structured logging once at startup
    pixie_logging.configure_logging()
    yield


app = FastAPI(title="Pixie Core API", version="0.0.0", lifespan=lifespan)


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    """Middleware that assigns a trace_id to the request and makes it
    available to the logger via the ContextVar in pixie.core.logging.
    """
    trace_id = str(uuid4())
    # set in ContextVar so logging filter can pick it up
    pixie_logging.trace_id_ctx.set(trace_id)

    # log via uvicorn.error (uvicorn.access uses a special access formatter that
    # expects tuple args which can raise when we log arbitrary messages here)
    logging.getLogger("uvicorn.error").info(
        "request_start", extra={"path": request.url.path, "trace_id": trace_id}
    )

    try:
        response = await call_next(request)
    except Exception:
        # ensure trace_id is present in error logs by re-raising after logging
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

    # Also ensure the trace_id is present in response headers for easier tracing
    try:
        # many ASGI responses have a headers mapping
        response.headers["X-Trace-Id"] = trace_id
    except Exception:
        # ignore if response doesn't support headers assignment
        pass

    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: InteractRequest):
    logger = logging.getLogger(__name__)

    # Generate a single timestamp for this request and reuse it for both
    # request and response logs so they remain consistent.
    ts = datetime.now(timezone.utc).isoformat()

    # Log the incoming /ask/interact request with timestamp
    logger.info("api.ask.request", extra={"payload": req.model_dump(), "ts": ts})

    pixie = Pixie()

    # Dispatch: if pending_id is present this is a reply, otherwise a new question
    if req.pending_id is not None:
        # InteractRequest validator guarantees reply_text is present when pending_id is set
        assert req.reply_text is not None
        resp = pixie.reply(req.pending_id, req.reply_text)
    else:
        # construct AskRequest-like object
        # InteractRequest validator guarantees question is present when pending_id is not set
        assert req.question is not None
        resp = pixie.answer(req.question)

    # Log the AskResponse being returned (reuse the same timestamp)
    logger.info(
        "api.ask.response",
        extra={
            "response_type": resp.type,
            "response_text": resp.text,
            "ts": ts,
        },
    )

    return resp


# Note: /reply endpoint removed in favor of single /ask (InteractRequest) endpoint.
