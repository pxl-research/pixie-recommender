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


class _StubModel:
    def __init__(self, resp):
        self._resp = resp
        self.last_call = None

    def generate(self, *_args, **_kwargs):
        # record call for inspection in tests
        self.last_call = (_args, _kwargs)
        return self._resp


def test_relevance_uses_azure_shape_and_fallback():
    # instantiate the real class (safe even without langchain installed)
    r = AzureRelevanceLLM("v", "e", "k", "m")

    # Mock an Azure-style response via generations -> text
    r.model = _StubModel(_GensResp("Yes, related to printers"))
    assert r.is_relevant("irrelevant text") is True

    # Mock an Azure-style negative response
    r.model = _StubModel(_GensResp("No, not related"))
    assert r.is_relevant("something else") is False

    # Ensure heuristic fallback still works when model is absent
    r.model = None
    assert r.is_relevant("Ik zoek een printer") is True
    assert r.is_relevant("Wat is de prijs?") is False


def test_sql_prefers_azure_response_but_falls_back():
    s = AzureSQLLLM("v", "e", "k", "m")

    # Mock azure-style generations response
    s.model = _StubModel(_GensResp("SELECT * FROM printers;"))
    q = s.generate_sql("Ik zoek printers")
    # ensure the prompt sent to the model contains our expected framing
    last = s.model.last_call
    args = last[0] if last else ()
    # first positional arg is the list of messages; inspect the first message content
    sent = args[0][0]["content"] if args and args[0] and args[0][0] else ""
    assert "Generate a single concise SQL query" in sent
    assert q.strip() == "SELECT * FROM printers;"

    # Mock azure-style text response shape
    s.model = _StubModel(_TextResp("SELECT name FROM printers;"))
    q2 = s.generate_sql("Ik zoek printers")
    last2 = s.model.last_call
    args2 = last2[0] if last2 else ()
    sent2 = args2[0][0]["content"] if args2 and args2[0] and args2[0][0] else ""
    assert "Question:" in sent2
    assert q2.strip() == "SELECT name FROM printers;"

    # No model -> fallback
    s.model = None
    assert s.generate_sql("Ik zoek printers").strip() == "SELECT * FROM printers;"


def test_refinement_uses_azure_shape_and_fallback_sequence():
    rf = AzureRefinementLLM("v", "e", "k", "m")

    # Mock Azure response for empty context
    rf.model = _StubModel(_GensResp("Wat is je budget?"))
    assert rf.generate_refinement_question({}) == "Wat is je budget?"
    # check prompt framing
    last3 = rf.model.last_call
    args3 = last3[0] if last3 else ()
    sent = args3[0][0]["content"] if args3 and args3[0] and args3[0][0] else ""
    assert "Given the conversation context as JSON" in sent

    # Mock Azure response when budget present
    rf.model = _StubModel(_GensResp("Heb je een voorkeur voor een merk?"))
    assert (
        rf.generate_refinement_question({"budget": "<50"})
        == "Heb je een voorkeur voor een merk?"
    )

    # Mock Azure response for brand present
    rf.model = _StubModel(
        _GensResp("Welke technologie heeft je voorkeur (inkjet/laser)?")
    )
    assert (
        rf.generate_refinement_question({"budget": "<50", "brand": "HP"})
        == "Welke technologie heeft je voorkeur (inkjet/laser)?"
    )

    # Fallback deterministic sequence when model missing
    rf.model = None
    assert rf.generate_refinement_question({}) == "Wat is je budget?"
    assert (
        rf.generate_refinement_question({"budget": "<50"})
        == "Heb je een voorkeur voor een merk?"
    )
    assert (
        rf.generate_refinement_question({"budget": "<50", "brand": "HP"})
        == "Welke technologie heeft je voorkeur (inkjet/laser)?"
    )
    assert (
        rf.generate_refinement_question(
            {"budget": "<50", "brand": "HP", "technology": "laser"}
        )
        is None
    )


def test_create_azure_llm_set_reads_env(monkeypatch):
    # ensure the factory returns Azure*LLM instances when env vars are set
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "v")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "e")
    monkeypatch.setenv("AZURE_OPENAI_KEY", "k")
    monkeypatch.setenv("AZURE_OPENAI_MODEL", "m")

    from pixie.core.llms.azure_llm_set import create_azure_llm_set

    relevance, sql, refinement = create_azure_llm_set()
    assert isinstance(relevance, AzureRelevanceLLM)
    assert isinstance(sql, AzureSQLLLM)
    assert isinstance(refinement, AzureRefinementLLM)
