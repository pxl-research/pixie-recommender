from __future__ import annotations

import logging
from datetime import datetime, timezone

from pixie.core.contracts import AskRequest, AskResponse


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

    def answer(self, request: AskRequest) -> AskResponse:
        """Return a deterministic AskResponse for the provided AskRequest."""
        logger = logging.getLogger(__name__)

        # Generate a single timestamp for this logical operation so both
        # request and response logs share the exact same timestamp.
        ts = datetime.now(timezone.utc).isoformat()

        # Log the incoming question with the shared timestamp to make it
        # easy to correlate in plain-text or JSON logs.
        logger.info(
            "pixie.answer.request",
            extra={
                "question": request.question,
                "ts": ts,
            },
        )

        text = self._rag.answer(request.question)
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
