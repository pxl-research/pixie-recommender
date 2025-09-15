from pixie.core.conversation.conversation_loop import ConversationLoopManager


def test_basic_success_path(mock_llm_set):
    def search_fn(sql_query, attrs):
        return [{"id": 1, "name": "Printer A"}]

    mgr = ConversationLoopManager(search_fn, llm_set=mock_llm_set)
    resp = mgr.handle_new_question("Ik zoek een nieuwe printer")
    assert resp.type == "ask_user"
    assert resp.prompt == "Wat is je budget?"
    pending_id = resp.pending_id
    assert pending_id is not None

    # Reply with budget
    resp2 = mgr.handle_reply(pending_id, "minder dan 150€")
    assert resp2.type == "ask_user"
    assert resp2.prompt == "Heb je een voorkeur voor een merk?"

    # Reply with brand
    resp3 = mgr.handle_reply(pending_id, "Brother")
    assert resp3.type == "ask_user"
    assert resp3.prompt == "Welke technologie heeft je voorkeur (inkjet/laser)?"

    # Reply with tech
    resp4 = mgr.handle_reply(pending_id, "laser")
    assert resp4.type == "answer"


def test_refinement_then_answer(mock_llm_set):
    # first search returns empty
    calls = {"count": 0}

    def search_fn(sql_query, attrs):
        calls["count"] += 1
        return [{"id": 2, "name": "Brother Printer XC 2570"}]

    mgr = ConversationLoopManager(search_fn, llm_set=mock_llm_set)
    first = mgr.handle_new_question("Ik zoek een nieuwe printer")
    assert first.type == "ask_user"
    pending_id = first.pending_id
    assert pending_id is not None
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
    def search_fn(sql_query, attrs):
        return []

    mgr = ConversationLoopManager(search_fn)
    resp = mgr.handle_reply("non-existent", "anything")
    assert resp.type == "error"


def test_max_iterations_reached():
    # search always returns empty -> manager should eventually return
    # no_results after max iterations
    def search_fn(sql_query, attrs):
        return []

    mgr = ConversationLoopManager(search_fn, max_iterations=2)
    first = mgr.handle_new_question("Ik zoek een nieuwe printer")
    assert first.type == "ask_user"
    assert first.pending_id is not None
    pending_id = first.pending_id
    assert pending_id is not None

    # reply to ask_budget
    second = mgr.handle_reply(pending_id, "minder dan 150€")
    assert second.type == "ask_user"

    # reply to ask_brand
    third = mgr.handle_reply(pending_id, "Brother")
    assert third.type == "ask_user"

    # reply to ask_tech -> search still empty, iterations reaches max -> no_results
    fourth = mgr.handle_reply(pending_id, "laser")
    assert fourth.type in ("no_results",)


def test_choose_result_view_large_results(mock_llm_set):
    # Use RealSearchEngine so initial search (attributes None) returns many results
    from pixie.core.search.search_engine import RealSearchEngine

    engine = RealSearchEngine()
    # make the sql model generate SQL that will return empty until refinements are provided
    mgr = ConversationLoopManager(engine.search, llm_set=mock_llm_set)

    # initial new question -> first search returns many results (attributes None) -> ask_user
    first = mgr.handle_new_question("Ik zoek een nieuwe printer")
    assert first.type == "ask_user"

    # But to test the choose_result_view flow, simulate a flow where initial search is empty.
    # We'll create a search_fn that returns [] initially and then returns many when view chosen.
    calls = {"count": 0}

    def search_fn(sql_query, attrs):
        # first call (initial) empty, subsequent calls return many
        calls["count"] += 1
        # return empty for the first call (after ask_tech)
        # this makes the manager reach the choose_result_view stage
        if calls["count"] <= 1:
            return []
        return engine.search(sql_query, attrs)

    mgr2 = ConversationLoopManager(search_fn, max_iterations=5, llm_set=mock_llm_set)
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
    from pixie.core.storage.pending_store import InMemoryPendingStore

    store = InMemoryPendingStore()

    # use a search that returns empty so pending is created
    def search_fn(sql_query, attrs):
        return []

    mgr = ConversationLoopManager(search_fn, pending_store=store)
    first = mgr.handle_new_question("Ik zoek een nieuwe printer")
    assert first.type == "ask_user"
    assert first.pending_id is not None
    pending_id = first.pending_id
    assert pending_id is not None

    # shorten TTL to simulate expiry
    entry = store.get_pending(pending_id)
    assert entry is not None
    # directly overwrite created_at to simulate expiry
    from datetime import datetime, timedelta, timezone

    entry.created_at = datetime.now(timezone.utc) - timedelta(seconds=1000)

    # now replying should yield invalid_pending_id
    resp = mgr.handle_reply(pending_id, "minder dan 50€")
    assert resp.type == "error"


def test_conversation_with_real_search_initial_answer(mock_llm_set):
    # integration: ConversationLoopManager with RealSearchEngine
    from pixie.core.search.search_engine import RealSearchEngine

    engine = RealSearchEngine()
    mgr = ConversationLoopManager(engine.search, llm_set=mock_llm_set)

    resp = mgr.handle_new_question("Ik zoek een nieuwe printer")
    # RealSearchEngine returns many items for attributes None -> ask_user
    assert resp.type == "ask_user"


def test_conversation_refinement_then_answer_with_real_search(mock_llm_set):
    from pixie.core.search.search_engine import RealSearchEngine

    engine = RealSearchEngine()

    calls = {"count": 0}

    def search_fn(sql_query, attrs):
        calls["count"] += 1
        return engine.search(sql_query, attrs)

    mgr = ConversationLoopManager(search_fn, llm_set=mock_llm_set)
    first = mgr.handle_new_question("Ik zoek een nieuwe printer")
    assert first.type == "ask_user"
    pending_id = first.pending_id
    assert pending_id is not None

    second = mgr.handle_reply(pending_id, "minder dan 150€")
    assert second.type == "ask_user"

    third = mgr.handle_reply(pending_id, "Brother")
    assert third.type == "ask_user"

    fourth = mgr.handle_reply(pending_id, "laser")
    assert fourth.type == "answer"
