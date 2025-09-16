import os

import pytest

from pixie.core.llms.azure_refinement_llm import AzureRefinementLLM
from pixie.core.llms.azure_relevance_llm import AzureRelevanceLLM
from pixie.core.llms.azure_sql_llm import AzureSQLLLM


class _Gen:
    def __init__(self, text: str):
        self.text = text


class _GensResp:
    def __init__(self, text: str):
        # langchain-like shape: generations -> [[genobj]]
        self.generations = [[_Gen(text)]]


class _TextResp:
    def __init__(self, text: str):
        self.text = text


class _InvokeResp:
    def __init__(self, text: str):
        # Modern langchain-like shape: content attribute
        self.content = text


class _StubModel:
    def __init__(self, resp):
        self._resp = resp
        self.last_call = None

    def generate(self, *_args, **_kwargs):
        # record call for inspection in tests
        self.last_call = (_args, _kwargs)
        return self._resp

    def invoke(self, *_args, **_kwargs):
        # record call for inspection in tests
        self.last_call = (_args, _kwargs)
        return self._resp


def test_relevance_uses_azure_shape_and_fallback():
    # instantiate the real class (safe even without langchain installed)
    r = AzureRelevanceLLM("v", "e", "k", "m")

    # Mock an Azure-style response via invoke -> content
    r.model = _StubModel(_InvokeResp("Yes, related to printers"))
    assert r.is_relevant("irrelevant text") is True

    # Mock an Azure-style negative response
    r.model = _StubModel(_InvokeResp("No, not related"))
    assert r.is_relevant("something else") is False

    # When model is absent, expect error (no fallback in current implementation)
    r.model = None
    try:
        r.is_relevant("Ik zoek een printer")
        assert False, "Expected ValueError when model is None"
    except ValueError as e:
        assert "Azure model is not available" in str(e)


def test_detect_category_uses_azure_shape():
    # instantiate the real class (safe even without langchain installed)
    r = AzureRelevanceLLM("v", "e", "k", "m")

    # Mock Azure response for printer category
    r.model = _StubModel(_InvokeResp("printers"))
    assert r.detect_category("Ik zoek een printer") == "printers"

    # Mock Azure response for laptop category
    r.model = _StubModel(_InvokeResp("laptops"))
    assert r.detect_category("Ik wil een laptop kopen") == "laptops"

    # Mock Azure response for smartphone category
    r.model = _StubModel(_InvokeResp("smartphones"))
    assert r.detect_category("Welke telefoon is goed?") == "smartphones"

    # Mock Azure response for none
    r.model = _StubModel(_InvokeResp("none"))
    assert r.detect_category("Hoe is het weer?") is None

    # When model is absent, expect error
    r.model = None
    try:
        r.detect_category("Ik zoek een printer")
        assert False, "Expected ValueError when model is None"
    except ValueError as e:
        assert "Azure model is not available" in str(e)


def test_mock_detect_category():
    from pixie.core.llms.mock_llm_set import MockRelevance

    mock_relevance = MockRelevance()

    # Test printer detection
    assert mock_relevance.detect_category("Ik zoek een printer") == "printers"
    assert mock_relevance.detect_category("Welke laserprinter is goed?") == "printers"

    # Test laptop detection
    assert mock_relevance.detect_category("Ik wil een laptop kopen") == "laptops"
    assert mock_relevance.detect_category("MacBook voor werk") == "laptops"

    # Test computer detection
    assert mock_relevance.detect_category("Nieuwe desktop computer") == "computers"
    assert mock_relevance.detect_category("Gaming PC nodig") == "computers"

    # Test smartphone detection
    assert mock_relevance.detect_category("Welke telefoon is goed?") == "smartphones"
    assert mock_relevance.detect_category("iPhone kopen") == "smartphones"

    # Test non-product question
    assert mock_relevance.detect_category("Hoe is het weer?") is None


def test_sql_prefers_azure_response_but_falls_back():
    s = AzureSQLLLM("v", "e", "k", "m")

    # Mock azure-style invoke response
    s.model = _StubModel(_InvokeResp("SELECT * FROM printers;"))
    q = s.generate_sql("Ik zoek printers")
    # ensure the response is parsed correctly
    assert q.strip() == "SELECT * FROM printers;"

    # Mock azure-style response with markdown formatting
    s.model = _StubModel(_InvokeResp("```sql\nSELECT name FROM printers;\n```"))
    q2 = s.generate_sql("Ik zoek printers")
    assert q2.strip() == "SELECT name FROM printers;"

    # No model -> expect error (no fallback in current implementation)
    s.model = None
    try:
        s.generate_sql("Ik zoek printers")
        assert False, "Expected ValueError when model is None"
    except ValueError as e:
        assert "Azure model is not available" in str(e)


def test_refinement_uses_azure_shape_and_fallback_sequence():
    rf = AzureRefinementLLM("v", "e", "k", "m")

    # Mock Azure response for empty context
    rf.model = _StubModel(_InvokeResp("Wat is je budget?"))
    assert rf.generate_refinement_question({}) == "Wat is je budget?"

    # Mock Azure response when budget present
    rf.model = _StubModel(_InvokeResp("Heb je een voorkeur voor een merk?"))
    assert (
        rf.generate_refinement_question({"budget": "<50"})
        == "Heb je een voorkeur voor een merk?"
    )

    # Mock Azure response for brand present
    rf.model = _StubModel(
        _InvokeResp("Welke technologie heeft je voorkeur (inkjet/laser)?")
    )
    assert (
        rf.generate_refinement_question({"budget": "<50", "brand": "HP"})
        == "Welke technologie heeft je voorkeur (inkjet/laser)?"
    )

    # When model is missing, expect error (no fallback in current implementation)
    rf.model = None
    try:
        rf.generate_refinement_question({})
        assert False, "Expected ValueError when model is None"
    except ValueError as e:
        assert "Azure model is not available" in str(e)


@pytest.mark.skip(reason="Config caching makes this test unreliable")
def test_create_azure_llm_set_reads_env(monkeypatch):
    # ensure the factory returns Azure*LLM instances when env vars are set
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "v")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "e")
    monkeypatch.setenv("AZURE_OPENAI_KEY", "k")
    monkeypatch.setenv("AZURE_OPENAI_MODEL", "m")

    from pixie.core.llms.azure_llm_set import create_azure_llm_set
    from pixie.core.llms.mock_llm_set import MockRefinement, MockRelevance, MockSQL

    relevance, sql, refinement = create_azure_llm_set()

    # Check if mocks are forced
    force_mocks = os.getenv("PIXIE_FORCE_MOCKS", "0") == "1"

    if force_mocks:
        # Should return mock instances when PIXIE_FORCE_MOCKS=1
        assert isinstance(relevance, MockRelevance)
        assert isinstance(sql, MockSQL)
        assert isinstance(refinement, MockRefinement)
    else:
        # Should return real Azure LLM instances when not forced
        assert isinstance(relevance, AzureRelevanceLLM)
        assert isinstance(sql, AzureSQLLLM)
        assert isinstance(refinement, AzureRefinementLLM)
