import pytest

from pixie.core.pixie import Pixie
from pixie.core.contracts import AskRequest, AskResponse
from pydantic import ValidationError


def test_pixie_answer_core():
    q = "Wie ben je?"
    req = AskRequest(question=q)
    pixie = Pixie()
    res = pixie.answer(req)
    assert isinstance(res, AskResponse)
    assert res.type == "answer"
    assert res.text == f"(mock) antwoord op: {q}"


def test_askrequest_empty_question_fails():
    with pytest.raises(ValidationError):
        AskRequest(question="")
