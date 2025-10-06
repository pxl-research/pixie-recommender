from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional


@dataclass
class PendingEntry:
    pending_id: str
    question: str
    created_at: datetime
    ttl_seconds: int = 300
    conversation_context: Optional[Dict[str, Any]] = None

    def expired(self) -> bool:
        return datetime.now(timezone.utc) > self.created_at + timedelta(
            seconds=self.ttl_seconds
        )


class InMemoryPendingStore:
    def __init__(self) -> None:
        self._store: Dict[str, PendingEntry] = {}

    def save_pending(
        self,
        pending_id: str,
        question: str,
        ttl_seconds: int = 300,
        conversation_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        entry = PendingEntry(
            pending_id=pending_id,
            question=question,
            created_at=now,
            ttl_seconds=ttl_seconds,
            conversation_context=conversation_context,
        )
        self._store[pending_id] = entry

    def get_pending(self, pending_id: str) -> Optional[PendingEntry]:
        entry = self._store.get(pending_id)
        if not entry:
            return None
        if entry.expired():
            self._store.pop(pending_id, None)
            return None
        return entry

    def resolve_pending(self, pending_id: str) -> None:
        self._store.pop(pending_id, None)
