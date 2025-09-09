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


def test_max_iterations_reached():
    relevance, sql, refinement = create_mock_llm_set()

    # search always returns empty -> manager should eventually return
    # no_results after max iterations
    def search_fn(sql_query, attrs):
        return []

    mgr = ConversationLoopManager(
        relevance, sql, refinement, search_fn, max_iterations=2
    )
    first = mgr.handle_new_question("Ik zoek een nieuwe printer")
    assert first.type == "ask_user"
    assert first.pending_id is not None
    pending_id = first.pending_id

    # reply to ask_budget
    second = mgr.handle_reply(pending_id, "minder dan 150€")
    assert second.type == "ask_user"

    # reply to ask_brand
    third = mgr.handle_reply(pending_id, "Brother")
    assert third.type == "ask_user"

    # reply to ask_tech -> search still empty, iterations reaches max -> no_results
    fourth = mgr.handle_reply(pending_id, "laser")
    assert fourth.type in ("no_results",)


def test_choose_result_view_large_results():
    relevance, sql, refinement = create_mock_llm_set()

    # Use MockSearchEngine so initial search (attributes None) returns many results
    from pixie.core.mock_search import create_mock_search_engine

    engine = create_mock_search_engine()
    # make the sql model generate SQL that will return empty until refinements are provided
    mgr = ConversationLoopManager(relevance, sql, refinement, engine.search)

    # initial new question -> first search returns many results (attributes None) -> answer
    first = mgr.handle_new_question("Ik zoek een nieuwe printer")
    assert first.type == "answer"

    # But to test the choose_result_view flow, simulate a flow where initial search is empty.
    # We'll create a search_fn that returns [] initially and then returns many when view chosen.
    calls = {"count": 0}

    def search_fn(sql_query, attrs):
        # first call (initial) empty, subsequent calls return many
        calls["count"] += 1
        # return empty for first two calls (initial and after ask_tech) so we reach choose_result_view
        if calls["count"] <= 2:
            return []
        return engine.search(sql_query, attrs)

    mgr2 = ConversationLoopManager(
        relevance, sql, refinement, search_fn, max_iterations=5
    )
    first = mgr2.handle_new_question("Ik zoek een nieuwe printer")
    assert first.type == "ask_user"
    pending_id = first.pending_id
    assert pending_id is not None

    # reply to ask_budget
    second = mgr2.handle_reply(pending_id, "minder dan 150€")
    assert second.type == "ask_user"
    # reply to ask_brand
    third = mgr2.handle_reply(pending_id, "Brother")
    assert third.type == "ask_user"
    # reply to ask_tech -> search still empty -> should reach choose_result_view
    fourth = mgr2.handle_reply(pending_id, "laser")
    assert fourth.type == "ask_user"
    # now choose a view (e.g., sorted by price)
    fifth = mgr2.handle_reply(pending_id, "gesorteerd op prijs")
    assert fifth.type == "answer"


def test_ttl_integration():
    relevance, sql, refinement = create_mock_llm_set()
    from pixie.core.mock_search import create_mock_search_engine
    from pixie.core.pending_store import InMemoryPendingStore

    # engine not assigned to a variable; we only need its .search when used elsewhere
    _ = create_mock_search_engine()
    store = InMemoryPendingStore()

    # use a search that returns empty so pending is created
    def search_fn(sql_query, attrs):
        return []

    mgr = ConversationLoopManager(
        relevance, sql, refinement, search_fn, pending_store=store
    )
    first = mgr.handle_new_question("Ik zoek een nieuwe printer")
    assert first.type == "ask_user"
    assert first.pending_id is not None
    pending_id = first.pending_id

    # shorten TTL to simulate expiry
    entry = store.get_pending(pending_id)
    assert entry is not None
    # directly overwrite created_at to simulate expiry
    from datetime import datetime, timedelta, timezone

    entry.created_at = datetime.now(timezone.utc) - timedelta(seconds=1000)

    # now replying should yield invalid_pending_id
    resp = mgr.handle_reply(pending_id, "minder dan 50€")
    assert resp.type == "error"
