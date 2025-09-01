from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional


@dataclass
class PendingEntry:
    pending_id: str
    question: str
    created_at: datetime
    ttl_seconds: int = 300

    def expired(self) -> bool:
        return datetime.now(timezone.utc) > self.created_at + timedelta(
            seconds=self.ttl_seconds
        )


class InMemoryPendingStore:
    """Simple in-memory pending store with TTL semantics."""

    def __init__(self):
        self._store: Dict[str, PendingEntry] = {}

    def save_pending(
        self, pending_id: str, question: str, ttl_seconds: int = 300
    ) -> None:
        now = datetime.now(timezone.utc)
        entry = PendingEntry(
            pending_id=pending_id,
            question=question,
            created_at=now,
            ttl_seconds=ttl_seconds,
        )
        self._store[pending_id] = entry

    def get_pending(self, pending_id: str) -> Optional[PendingEntry]:
        entry = self._store.get(pending_id)
        if not entry:
            return None
        if entry.expired():
            # remove expired entry
            self._store.pop(pending_id, None)
            return None
        return entry

    def resolve_pending(self, pending_id: str) -> None:
        """Remove pending entry."""
        self._store.pop(pending_id, None)
