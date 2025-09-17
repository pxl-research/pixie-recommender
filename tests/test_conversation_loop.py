from pixie.core.conversation.conversation_loop import ConversationLoopManager


def test_basic_success_path(mock_llm_set):
    def search_fn(sql_query, attrs):
        return [{"id": 1, "name": "Printer A"}]

    mgr = ConversationLoopManager(search_fn, llm_set=mock_llm_set)
    resp = mgr.handle_new_question("Ik zoek een nieuwe printer")
    assert resp.type == "ask_user"
    assert resp.prompt is not None
    # More flexible check - LLM might ask about budget in different ways
    budget_keywords = ["budget", "prijs", "kosten", "geld", "uitgeven", "hoeveel"]
    prompt_lower = resp.prompt.lower()
    assert any(
        keyword in prompt_lower for keyword in budget_keywords
    ), f"Expected budget question, got: {resp.prompt}"
    pending_id = resp.pending_id
    assert pending_id is not None

    # Reply with budget
    resp2 = mgr.handle_reply(pending_id, "minder dan 150€")
    assert resp2.type == "ask_user"
    assert resp2.prompt is not None
    # More flexible check for brand question
    brand_keywords = ["merk", "brand", "voorkeur"]
    prompt2_lower = resp2.prompt.lower()
    assert any(
        keyword in prompt2_lower for keyword in brand_keywords
    ), f"Expected brand question, got: {resp2.prompt}"

    # Reply with brand
    resp3 = mgr.handle_reply(pending_id, "Brother")
    assert resp3.type == "ask_user"
    assert resp3.prompt is not None
    # More flexible check for technology question
    tech_keywords = [
        "technologie",
        "printtechnologie",
        "inkjet",
        "laser",
        "soort",
        "type",
    ]
    prompt3_lower = resp3.prompt.lower()
    assert any(
        keyword in prompt3_lower for keyword in tech_keywords
    ), f"Expected technology question, got: {resp3.prompt}"

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


def test_invalid_pending_id(mock_llm_set):
    def search_fn(sql_query, attrs):
        return []

    mgr = ConversationLoopManager(search_fn, llm_set=mock_llm_set)
    resp = mgr.handle_reply("non-existent", "anything")
    assert resp.type == "error"


def test_max_iterations_reached(mock_llm_set):
    # search always returns empty -> manager should eventually return
    # no_results after max iterations
    def search_fn(sql_query, attrs):
        return []

    mgr = ConversationLoopManager(search_fn, max_iterations=2, llm_set=mock_llm_set)
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
    # Use a mock search function that returns results after view selection
    calls = {"count": 0}

    def search_fn(sql_query, attrs):
        calls["count"] += 1
        # Return empty for initial search after all attributes collected
        if calls["count"] <= 1:  # Empty for initial search
            return []
        # Return mock results for view selection
        return [
            {"name": "HP LaserJet", "price": 299.99, "brand": "HP"},
            {"name": "Brother MFC", "price": 349.99, "brand": "Brother"},
        ]

    mgr = ConversationLoopManager(search_fn, max_iterations=6, llm_set=mock_llm_set)
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
    # reply to ask_technology
    fourth = mgr.handle_reply(pending_id, "laser")
    assert fourth.type == "ask_user"
    # reply to ask_color
    fifth = mgr.handle_reply(pending_id, "zwart-wit")
    assert fifth.type == "ask_user"
    # reply to ask_pages_per_minute -> should reach choose_result_view
    sixth = mgr.handle_reply(pending_id, "20")
    assert sixth.type == "ask_user"
    # now choose a view (e.g., sorted by price)
    seventh = mgr.handle_reply(pending_id, "gesorteerd op prijs")
    assert seventh.type == "answer"


def test_ttl_integration(mock_llm_set):
    from pixie.core.storage.pending_store import InMemoryPendingStore

    store = InMemoryPendingStore()

    # use a search that returns empty so pending is created
    def search_fn(sql_query, attrs):
        return []

    mgr = ConversationLoopManager(search_fn, pending_store=store, llm_set=mock_llm_set)
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
    # integration: ConversationLoopManager with SearchEngine
    from pixie.core.search import SearchEngine

    engine = SearchEngine()
    mgr = ConversationLoopManager(engine.search, llm_set=mock_llm_set)

    resp = mgr.handle_new_question("Ik zoek een nieuwe printer")
    # SearchEngine returns many items for attributes None -> ask_user
    assert resp.type == "ask_user"


def test_conversation_refinement_then_answer_with_real_search(mock_llm_set):
    from pixie.core.search import SearchEngine

    engine = SearchEngine()

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
