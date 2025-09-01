import pytest
from pydantic import ValidationError

from pixie.core.contracts import AskResponse, InteractRequest
from pixie.core.pixie import Pixie


def test_pixie_answer_core():
    q = "Wie ben je?"
    pixie = Pixie()
    res = pixie.answer(q)
    assert isinstance(res, AskResponse)
    assert res.type == "answer"
    assert res.text == f"(mock) antwoord op: {q}"


def test_interactrequest_validations():
    # missing question should fail for new-question path
    with pytest.raises(ValidationError):
        InteractRequest()
