from pixie.core.conversation_loop import ConversationLoopManager
from pixie.core.mock_llm_set import create_mock_llm_set
from pixie.core.search_engine import RealSearchEngine


def test_conversation_with_real_search_initial_answer():
    relevance, sql, refinement = create_mock_llm_set()
    engine = RealSearchEngine()
    mgr = ConversationLoopManager(relevance, sql, refinement, engine.search)

    resp = mgr.handle_new_question("Ik zoek een nieuwe printer")
    # RealSearchEngine returns many items for attributes None -> immediate answer
    assert resp.type == "answer"


def test_conversation_refinement_then_answer_with_real_search():
    relevance, sql, refinement = create_mock_llm_set()
    engine = RealSearchEngine()

    calls = {"count": 0}

    def search_fn(sql_query, attrs):
        calls["count"] += 1
        if calls["count"] == 1:
            return []
        return engine.search(sql_query, attrs)

    mgr = ConversationLoopManager(relevance, sql, refinement, search_fn)
    first = mgr.handle_new_question("Ik zoek een nieuwe printer")
    assert first.type == "ask_user"
    pending_id = first.pending_id

    second = mgr.handle_reply(pending_id, "minder dan 150€")
    assert second.type == "ask_user"

    third = mgr.handle_reply(pending_id, "Brother")
    assert third.type == "ask_user"

    fourth = mgr.handle_reply(pending_id, "laser")
    assert fourth.type == "answer"
