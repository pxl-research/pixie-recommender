from __future__ import annotations

import logging

from pixie.core.contracts import AskResponse


class FakeRAGAdapter:
    """A fake RAG adapter that deterministically answers questions."""

    def answer(self, question: str) -> str:
        return f"(mock) antwoord op: {question}"


class Pixie:
    """Small helper service that returns deterministic mock answers."""

    def __init__(self, rag_adapter: FakeRAGAdapter | None = None):
        self._rag = rag_adapter or FakeRAGAdapter()

    def answer(self, question: str) -> AskResponse:
        """Return a deterministic AskResponse for the provided question string."""
        logger = logging.getLogger(__name__)
        logger.info("pixie.answer", extra={"question": question})

        if "meer info" in question.lower():
            pending_id = "pending-1234"
            resp = AskResponse(
                type="ask_user",
                prompt=("Kunt u iets meer context geven? (open antwoord)"),
                pending_id=pending_id,
            )
        else:
            text = self._rag.answer(question)
            resp = AskResponse(type="answer", text=text)

        return resp

    def reply(self, pending_id: str, reply_text: str) -> AskResponse:
        """Handle a follow-up reply to a pending ask and return a final answer."""
        logger = logging.getLogger(__name__)
        logger.info("pixie.reply", extra={"pending_id": pending_id, "reply_text": reply_text})

        text = f"(mock) received reply for {pending_id}: {reply_text}"
        resp = AskResponse(type="answer", text=text)

        return resp
