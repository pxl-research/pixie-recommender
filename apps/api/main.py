import logging

from fastapi import Body, FastAPI

from pixie.core import logging as pixie_logging
from pixie.core.contracts import AskResponse
from pixie.core.pixie import Pixie


# Configure logging at startup
app = FastAPI(title="Pixie Core API", version="0.0.0")


@app.on_event("startup")
def on_startup():
    pixie_logging.configure_logging()


# Shared Pixie instance
_pixie_instance = Pixie()


@app.get("/health")
def health():
    return {"status": "ok"}


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
