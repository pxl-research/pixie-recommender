from pixie.core.pixie import Pixie
from pixie.core.contracts import AskRequest


def test_pixie_answer_unit():
    q = "Wat is Pixie?"
    req = AskRequest(question=q)
    pixie = Pixie()
    res = pixie.answer(req)
    assert res.type == "answer"
    assert "(mock) antwoord op:" in res.text
    assert q in res.text
