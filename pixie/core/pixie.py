from pixie.core.contracts import AskResponse


class Pixie:
    """Small helper that returns deterministic mock answers.

    The function is intentionally trivial and deterministic so tests can
    assert exact output.
    """

    @staticmethod
    def answer(question: str) -> AskResponse:
        text = f"(mock) antwoord op: {question}"
        return AskResponse(type="answer", text=text)
