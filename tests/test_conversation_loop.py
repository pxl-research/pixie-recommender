from pixie.core.conversation_loop import ConversationLoopManager
from pixie.core.mock_llm_set import create_mock_llm_set


def test_basic_success_path():
    relevance, sql, refinement = create_mock_llm_set()

    def search_fn(sql_query, attrs):
        return [{"id": 1, "name": "Printer A"}]

    mgr = ConversationLoopManager(relevance, sql, refinement, search_fn)
    resp = mgr.handle_new_question("Ik zoek een nieuwe printer")
    assert resp.type == "answer"


def test_refinement_then_answer():
    relevance, sql, refinement = create_mock_llm_set()

    # first search returns empty
    calls = {"count": 0}

    def search_fn(sql_query, attrs):
        calls["count"] += 1
        if calls["count"] == 1:
            return []
        return [{"id": 2, "name": "Brother XC 2570"}]

    mgr = ConversationLoopManager(relevance, sql, refinement, search_fn)
    first = mgr.handle_new_question("Ik zoek een nieuwe printer")
    assert first.type == "ask_user"
    pending_id = first.pending_id
    # reply to ask_budget
    second = mgr.handle_reply(pending_id, "minder dan 150€")
    assert second.type == "ask_user"
    # reply to ask_brand
    third = mgr.handle_reply(pending_id, "Brother")
    assert third.type == "ask_user"
    # reply to ask_tech -> now search should return results
    fourth = mgr.handle_reply(pending_id, "laser")
    assert fourth.type == "answer"


def test_invalid_pending_id():
    relevance, sql, refinement = create_mock_llm_set()

    def search_fn(sql_query, attrs):
        return []

    mgr = ConversationLoopManager(relevance, sql, refinement, search_fn)
    resp = mgr.handle_reply("non-existent", "anything")
    assert resp.type == "error"
