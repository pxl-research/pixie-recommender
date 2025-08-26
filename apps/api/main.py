import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request

from pixie.core import logging as pixie_logging
from pixie.core.contracts import AskRequest, AskResponse
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

    logging.getLogger("uvicorn.access").info(
        "request_start", extra={"path": request.url.path, "trace_id": trace_id}
    )

    try:
        response = await call_next(request)
    except Exception:
        # ensure trace_id is present in error logs by re-raising after logging
        logging.exception("unhandled_exception")
        raise

    logging.getLogger("uvicorn.access").info(
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
def ask(req: AskRequest):
    # v0.0: deterministisch mock-antwoord via Pixie helper
    return Pixie.answer(req.question)
