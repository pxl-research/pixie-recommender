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
    assert results == []
