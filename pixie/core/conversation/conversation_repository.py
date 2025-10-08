"""In-memory repository for conversation state management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from .conversation_state import ConversationState


_BRUSSELS_TZ = ZoneInfo("Europe/Brussels")


def _now_brussels() -> datetime:
    return datetime.now(tz=_BRUSSELS_TZ)


@dataclass
class _StoredConversation:
    state: ConversationState
    expires_at: datetime


class ConversationRepository:
    def __init__(self, ttl: timedelta | None = None) -> None:
        default_ttl = ttl or timedelta(hours=24)
        self._ttl: timedelta = default_ttl
        self._store: Dict[UUID, _StoredConversation] = {}

    def create(self, state: ConversationState) -> None:
        self._store[state.conversation_id] = _StoredConversation(
            state=state,
            expires_at=self._compute_expiry(),
        )

    def get(self, conversation_id: UUID) -> tuple[Optional[ConversationState], bool]:
        stored = self._store.get(conversation_id)
        if not stored:
            return None, False

        is_expired = stored.expires_at <= _now_brussels()
        return stored.state, is_expired

    def update(self, state: ConversationState) -> None:
        if state.conversation_id not in self._store:
            raise KeyError(f"Conversation {state.conversation_id} not found")

        stored = self._store[state.conversation_id]
        stored.state = state
        stored.expires_at = self._compute_expiry()

    def expire_stale(self, now: datetime | None = None) -> list[UUID]:
        current_time = now or _now_brussels()
        expired_ids: list[UUID] = []
        for conversation_id, stored in self._store.items():
            if stored.expires_at <= current_time and stored.state.status != "expired":
                stored.state.status = "expired"
                stored.state.updated_at = current_time
                expired_ids.append(conversation_id)
        return expired_ids

    def _compute_expiry(self) -> datetime:
        return _now_brussels() + self._ttl
