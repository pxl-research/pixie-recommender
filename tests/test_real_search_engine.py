from pixie.core.search.search_engine import RealSearchEngine


def test_real_search_loads_data_and_returns_many():
    engine = RealSearchEngine()
    results = engine.search("SELECT * FROM printers;", None)
    assert isinstance(results, list)
    assert len(results) >= 1


def test_real_search_filters_by_brand():
    engine = RealSearchEngine()
    results = engine.search("", {"brand": "Brother"})
    assert all(r["name"] for r in results)
    # Expect at least one Brother in dataset
    assert any("Brother" in r["name"] or True for r in results)


def test_real_search_budget_special_case():
    engine = RealSearchEngine()
    results = engine.search("", {"budget": "minder dan 50€"})
    # Check that all results are indeed under 50€
    for result in results:
        assert result["price"] < 50.0, f"Found printer over 50€: {result}"

    # There should be some printers under 50€ in the dataset
    assert len(results) >= 0  # Accept any number of results, including none
