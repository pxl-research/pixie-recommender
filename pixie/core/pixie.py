from __future__ import annotations

import logging
from datetime import datetime, timezone

from pixie.core.contracts import AskResponse


class FakeRAGAdapter:
    """A fake RAG adapter that deterministically answers questions.

    This stands in for a real retrieval-augmented generation layer during
    initial development and tests.
    """

    def answer(self, question: str) -> str:
        return f"(mock) antwoord op: {question}"


class Pixie:
    """Small helper service that returns deterministic mock answers.

    The `answer` method accepts an `AskRequest` and returns an `AskResponse`.
    Internally it uses a (mock) RAG adapter so the implementation can be
    swapped out later without changing the public surface.
    """

    def __init__(self, rag_adapter: FakeRAGAdapter | None = None):
        self._rag = rag_adapter or FakeRAGAdapter()

    def answer(self, question: str) -> AskResponse:
        """Return a deterministic AskResponse for the provided question string."""
        logger = logging.getLogger(__name__)

        # Generate a single timestamp for this logical operation so both
        # request and response logs share the exact same timestamp.
        ts = datetime.now(timezone.utc).isoformat()

        # Log the incoming question with the shared timestamp to make it
        # easy to correlate in plain-text or JSON logs.
        logger.info("pixie.answer.request", extra={"question": question, "ts": ts})

        # For testing/demo purposes: if the question contains 'meer info'
        # simulate a situation where Pixie needs to ask the user for more data.
        if "meer info" in question.lower():
            # craft a pending ask asking an open question the user can answer
            pending_id = "pending-1234"
            payload = {
                "question": "Kunt u iets meer context geven? (open antwoord)",
                "pending_id": pending_id,
            }
            resp = AskResponse(type="ask_user", payload=payload)  # type: ignore[arg-type]
        else:
            text = self._rag.answer(question)
            resp = AskResponse(type="answer", text=text)

        # Log the response that will be returned (reuse the same timestamp)
        logger.info(
            "pixie.answer.response",
            extra={
                "response_type": resp.type,
                "response_text": resp.text,
                "ts": ts,
            },
        )

        return resp

    def reply(self, pending_id: str, reply_text: str) -> AskResponse:
        """Handle a follow-up reply to a pending ask and return a final answer.

        This is a minimal implementation for tests: it validates the pending_id
        and returns a deterministic confirmation string.
        """
        logger = logging.getLogger(__name__)
        ts = datetime.now(timezone.utc).isoformat()

        logger.info(
            "pixie.reply.request",
            extra={"pending_id": pending_id, "reply_text": reply_text, "ts": ts},
        )

        # In a real implementation we'd merge the reply_text into a context
        # and continue the RAG flow. For tests, return a simple acknowledgement.
        text = f"(mock) received reply for {pending_id}: {reply_text}"
        resp = AskResponse(type="answer", text=text)

        logger.info(
            "pixie.reply.response",
            extra={"response_type": resp.type, "response_text": resp.text, "ts": ts},
        )

        return resp
