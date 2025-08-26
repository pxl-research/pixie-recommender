from pixie.core.pixie import Pixie


def test_pixie_answer_unit():
    q = "Wat is Pixie?"
    res = Pixie.answer(q)
    assert res.type == "answer"
    assert "(mock) antwoord op:" in res.text
    assert q in res.text
