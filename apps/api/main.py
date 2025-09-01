import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request, HTTPException

from pixie.core import logging as pixie_logging
from pixie.core.contracts import AskResponse, ReplyRequest
from pixie.core.pixie import Pixie


@asynccontextmanager
async def lifespan(app: FastAPI):
    # configure logging once at startup
    pixie_logging.configure_logging()
    yield


app = FastAPI(title="Pixie Core API", version="0.0.0", lifespan=lifespan)

# Shared Pixie instance to maintain state across requests
_pixie_instance = Pixie()


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
    logger.info("api.ask", extra={"payload": req})

    try:
        # Use shared Pixie instance to maintain pending state
        pixie = _pixie_instance

        # Validate this is a question request, not reply
        if "pending_id" in req:
            return AskResponse(
                type="error",
                reason="Use /reply endpoint for responding to pending questions"
            )

        question = req.get("question")
        if question is None:
            return AskResponse(
                type="error",
                reason="'question' is required for new asks"
            )
        if not isinstance(question, str) or len(question.strip()) == 0:
            return AskResponse(
                type="error",
                reason="'question' must be a non-empty string"
            )
        
        resp = pixie.answer(question.strip())
        return resp
        
    except Exception:
        logger.exception("Unexpected error in /ask endpoint")
        return AskResponse(
            type="error",
            reason="Internal server error occurred"
        )


@app.post("/reply", response_model=AskResponse)
def reply(req: dict):
    logger = logging.getLogger(__name__)
    logger.info("api.reply", extra={"payload": req})

    try:
        # Use shared Pixie instance to maintain pending state
        pixie = _pixie_instance

        # Validate and parse reply request
        try:
            rr = ReplyRequest.model_validate(req)
        except Exception as e:
            logger.error("Reply validation error", extra={"error": str(e)})
            return AskResponse(
                type="error", 
                reason=f"Invalid reply request: {str(e)}"
            )

        # Process the reply
        resp = pixie.reply(rr.pending_id, rr.message)
        return resp
        
    except Exception:
        logger.exception("Unexpected error in /reply endpoint")
        return AskResponse(
            type="error",
            reason="Internal server error occurred"
        )
