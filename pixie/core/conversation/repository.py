from __future__ import annotations

from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Dict, Optional

from .state import ConversationState


class ConversationRepository:
    """Simple in-memory store with TTL-based eviction."""

    def __init__(self, ttl: timedelta) -> None:
        if ttl <= timedelta(0):
            raise ValueError("Conversation TTL must be positive")
        self._ttl = ttl
        self._items: Dict[str, ConversationState] = {}
        self._lock = RLock()

    def create(self, state: ConversationState) -> ConversationState:
        with self._lock:
            state.touch()
            self._items[state.conversation_id] = state
        return state

    def get(self, conversation_id: str) -> Optional[ConversationState]:
        with self._lock:
            state = self._items.get(conversation_id)
            if not state:
                return None
            if self._is_expired(state):
                self._items.pop(conversation_id, None)
                return None
            return state

    def update(self, state: ConversationState) -> ConversationState:
        with self._lock:
            if state.conversation_id not in self._items:
                raise KeyError(f"Conversation '{state.conversation_id}' does not exist")
            state.touch()
            self._items[state.conversation_id] = state
        return state

    def delete(self, conversation_id: str) -> None:
        with self._lock:
            self._items.pop(conversation_id, None)

    def expire_stale(self) -> None:
        with self._lock:
            expired = [
                key for key, state in self._items.items() if self._is_expired(state)
            ]
            for key in expired:
                self._items.pop(key, None)

    def count(self) -> int:
        with self._lock:
            self.expire_stale()
            return len(self._items)

    def _is_expired(self, state: ConversationState) -> bool:
        return datetime.now(UTC) - state.updated_at > self._ttl
