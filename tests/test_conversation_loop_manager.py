from __future__ import annotations

from datetime import timedelta

from pixie.core.conversation.conversation_loop_manager import ConversationLoopManager
from pixie.core.conversation.repository import ConversationRepository


class DummyFilterLLM:
    def build_filters(self, reply, attribute):
        return []


class DummyRefinementLLM:
    def generate_question(self, context=None):
        return None


class DummyOrchestrator:
    def check_relevance_and_category(self, question):
        raise RuntimeError("not used in this test")


class AcceptingOrchestrator:
    def __init__(self, category: str = "printers") -> None:
        self.category = category

    def check_relevance_and_category(self, question):
        return type(
            "Resp",
            (),
            {
                "success": True,
                "result": {"relevant": True, "category": self.category},
            },
        )()


class HelpfulRefinementLLM:
    def generate_question(self, context=None):
        attribute = (context or {}).get("attribute", {})
        label = attribute.get("label") or attribute.get("name") or "attribuut"
        return f"Kun je iets vertellen over {label}?"


def test_build_filters_ignores_unknown_reply():
    # Repository is required but not used in this test; provide a short TTL.
    repo = ConversationRepository(ttl=timedelta(minutes=1))
    manager = ConversationLoopManager(
        search_fn=lambda *_args, **_kwargs: {},
        llm_orchestrator=DummyOrchestrator(),
        refinement_llm=DummyRefinementLLM(),
        filter_llm=DummyFilterLLM(),
        repository=repo,
    )

    attribute = {"name": "merk", "type": "categorical", "values": ["hp", "canon"]}

    for answer in ["Geen idee", "Ik weet het niet", "Maakt niet uit"]:
        filters = manager._build_filters_from_answer(attribute, answer)
        assert filters == [], f"Answer '{answer}' should not yield filters"


class EchoFilterLLM:
    def __init__(self, payload):
        self.payload = payload

    def build_filters(self, reply, attribute):
        return self.payload


class BrandFilterLLM:
    def build_filters(self, reply, attribute):
        if attribute.get("name") == "merk" and "brother" in (reply or "").lower():
            return [{"name": "merk", "type": "exact", "value": "Brother"}]
        return []


def test_build_filters_uses_llm_output():
    repo = ConversationRepository(ttl=timedelta(minutes=1))
    expected = [{"name": "merk", "type": "exact", "value": "HP"}]
    manager = ConversationLoopManager(
        search_fn=lambda *_args, **_kwargs: {},
        llm_orchestrator=DummyOrchestrator(),
        refinement_llm=DummyRefinementLLM(),
        filter_llm=EchoFilterLLM(expected),
        repository=repo,
    )

    attribute = {"name": "merk", "type": "categorical", "values": ["HP"]}
    filters = manager._build_filters_from_answer(attribute, "HP graag")
    assert filters == expected


def test_select_attribute_skips_single_remaining_option():
    repo = ConversationRepository(ttl=timedelta(minutes=1))
    manager = ConversationLoopManager(
        search_fn=lambda *_args, **_kwargs: {},
        llm_orchestrator=DummyOrchestrator(),
        refinement_llm=HelpfulRefinementLLM(),
        filter_llm=DummyFilterLLM(),
        repository=repo,
    )

    metadata = {
        "attribute_options": [
            {
                "name": "merk",
                "type": "categorical",
                "values": ["Brother"],
            }
        ]
    }
    items = [{"merk": "Brother"}]

    attribute = manager._select_attribute(metadata, set(), items)
    assert attribute is None


def test_select_attribute_uses_metadata_when_multiple_values():
    repo = ConversationRepository(ttl=timedelta(minutes=1))
    manager = ConversationLoopManager(
        search_fn=lambda *_args, **_kwargs: {},
        llm_orchestrator=DummyOrchestrator(),
        refinement_llm=HelpfulRefinementLLM(),
        filter_llm=DummyFilterLLM(),
        repository=repo,
    )

    metadata = {
        "attribute_options": [
            {
                "name": "merk",
                "type": "categorical",
                "values": ["Brother", "HP"],
            }
        ]
    }
    items = [{"merk": "Brother"}]

    attribute = manager._select_attribute(metadata, set(), items)
    assert attribute is not None
    assert attribute.get("values") == ["Brother", "HP"]


def test_build_refinement_prompt_limits_options_to_remaining_values():
    repo = ConversationRepository(ttl=timedelta(minutes=1))
    manager = ConversationLoopManager(
        search_fn=lambda *_args, **_kwargs: {},
        llm_orchestrator=DummyOrchestrator(),
        refinement_llm=HelpfulRefinementLLM(),
        filter_llm=DummyFilterLLM(),
        repository=repo,
    )

    metadata = {
        "product_name": "printers",
        "attribute_options": [
            {
                "name": "merk",
                "type": "categorical",
                "values": ["Brother", "HP", "Canon"],
            }
        ],
    }
    items = [
        {"merk": "Brother"},
        {"merk": "HP"},
    ]

    prompt, attribute = manager._build_refinement_prompt(
        "printers", metadata, items, count=len(items), asked=set(), filters=[]
    )

    assert prompt is not None
    assert attribute is not None
    assert attribute.get("values") == ["Brother", "HP"]
    assert attribute.get("options")[:2] == ["Brother", "HP"]


def test_handle_new_question_derives_initial_filters():
    repo = ConversationRepository(ttl=timedelta(minutes=1))
    calls: list[list[dict] | None] = []

    inventory = [
        {"naam": "Brother Laser 1", "merk": "Brother"},
        {"naam": "Brother Laser 2", "merk": "Brother"},
        {"naam": "HP OfficeJet", "merk": "HP"},
    ]

    def search_fn(_sql, context):
        filters = (context or {}).get("filters")
        calls.append(filters)
        results = inventory
        if filters:
            for flt in filters:
                if flt.get("name") == "merk":
                    results = [item for item in results if item.get("merk") == flt.get("value")]
        return {
            "product_name": "printers",
            "results": results,
            "count": len(results),
            "total": len(results),
            "attribute_options": [
                {"name": "merk", "type": "categorical", "values": ["Brother", "HP"]},
                {
                    "name": "printtechnologie",
                    "type": "categorical",
                    "values": ["laser", "inkjet", "led"],
                },
            ],
        }

    manager = ConversationLoopManager(
        search_fn=search_fn,
        llm_orchestrator=AcceptingOrchestrator(),
        refinement_llm=HelpfulRefinementLLM(),
        filter_llm=BrandFilterLLM(),
        repository=repo,
        result_threshold=1,
    )

    response = manager.handle_new_question("Ik zoek een Brother printer")

    assert len(calls) == 2
    assert calls[0] in (None, [])
    assert calls[1] and calls[1][0]["name"] == "merk"
    assert response.type == "ask_user"
    assert response.conversation_id is not None

    state = manager.repository.get(response.conversation_id)
    assert state is not None
    assert state.filters == [{"name": "merk", "type": "exact", "value": "Brother"}]
    assert "merk" in state.asked_attributes
