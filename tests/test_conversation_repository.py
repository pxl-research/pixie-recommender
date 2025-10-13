from __future__ import annotations

import time
from datetime import timedelta
from uuid import uuid4

from pixie.core.conversation.repository import ConversationRepository
from pixie.core.conversation.state import ConversationState


def _state() -> ConversationState:
    return ConversationState(
        conversation_id=str(uuid4()),
        category="laptops",
    )


def test_create_and_get_roundtrip():
    repo = ConversationRepository(ttl=timedelta(minutes=5))
    state = _state()
    repo.create(state)

    fetched = repo.get(state.conversation_id)
    assert fetched is state
    assert fetched.category == "laptops"


def test_update_persists_changes_and_refreshes_timestamp():
    repo = ConversationRepository(ttl=timedelta(minutes=5))
    state = _state()
    repo.create(state)
    original_updated_at = state.updated_at

    state.filters.append({"name": "prijs", "type": "range", "min_value": 1000, "max_value": 1500})
    repo.update(state)
    fetched = repo.get(state.conversation_id)
    assert fetched.filters[0]["name"] == "prijs"
    assert fetched.updated_at > original_updated_at


def test_expire_stale_removes_old_conversations():
    repo = ConversationRepository(ttl=timedelta(milliseconds=10))
    state = _state()
    repo.create(state)
    time.sleep(0.05)

    repo.expire_stale()
    assert repo.get(state.conversation_id) is None
    assert repo.count() == 0
