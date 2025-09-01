import pytest
from pydantic import ValidationError

from pixie.core.contracts import AskResponse
from pixie.core.pixie import Pixie


def test_pixie_answer_core():
    q = "Wie ben je?"
    pixie = Pixie()
    res = pixie.answer(q)
    assert isinstance(res, AskResponse)
    assert res.type == "answer"
    # response should include the deterministic mock text
    assert getattr(res, "text", None) == f"(mock) antwoord op: {q}"


def test_askresponse_validation():
    # empty AskResponse dict should fail validation
    with pytest.raises(ValidationError):
        AskResponse.model_validate({})
