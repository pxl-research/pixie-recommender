import time
from datetime import datetime

from pixie.core.pending_store import InMemoryPendingStore


def test_save_and_get_pending():
    store = InMemoryPendingStore()
    pid = "p-1"
    question = "Wat is uw naam?"
    store.save_pending(pid, question, ttl_seconds=10)

    entry = store.get_pending(pid)
    assert entry is not None
    assert entry.pending_id == pid
    assert entry.question == question
    assert isinstance(entry.created_at, datetime)
    assert entry.created_at.tzinfo is not None


def test_resolve_pending_removes_entry():
    store = InMemoryPendingStore()
    pid = "p-2"
    store.save_pending(pid, "q", ttl_seconds=10)
    assert store.get_pending(pid) is not None
    store.resolve_pending(pid)
    assert store.get_pending(pid) is None


def test_get_pending_expired_returns_none():
    store = InMemoryPendingStore()
    pid = "p-3"
    # small TTL
    store.save_pending(pid, "expire me", ttl_seconds=1)
    assert store.get_pending(pid) is not None
    time.sleep(1.1)
    # after TTL it should be gone
    assert store.get_pending(pid) is None
