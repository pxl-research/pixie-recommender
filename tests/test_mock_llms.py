from pixie.core.mock_llm_set import create_mock_llm_set


def test_relevance_detects_printer():
    relevance, sql, refinement = create_mock_llm_set()
    assert relevance.is_relevant("Ik zoek een printer") is True
    assert relevance.is_relevant("Wat is de prijs?") is False


def test_sql_always_returns_select_all():
    relevance, sql, refinement = create_mock_llm_set()
    q = sql.generate_sql("Ik zoek printers")
    assert q.strip() == "SELECT * FROM printers;"


def test_refinement_sequence():
    relevance, sql, refinement = create_mock_llm_set()
    # no context -> ask budget
    assert refinement.generate_refinement_question({}) == "Wat is je budget?"
    # budget present -> ask brand
    assert (
        refinement.generate_refinement_question({"budget": "<50"})
        == "Heb je een voorkeur voor een merk?"
    )
    # budget+brand -> ask technology
    assert (
        refinement.generate_refinement_question({"budget": "<50", "brand": "HP"})
        == "Welke technologie heeft je voorkeur (inkjet/laser)?"
    )
    # all present -> None
    assert (
        refinement.generate_refinement_question(
            {
                "budget": "<50",
                "brand": "HP",
                "technology": "laser",
            }
        )
        is None
    )
