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
