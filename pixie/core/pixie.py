from __future__ import annotations

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
        text = self._rag.answer(request.question)
        return AskResponse(type="answer", text=text)
