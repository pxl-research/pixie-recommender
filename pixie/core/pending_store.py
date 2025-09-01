from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Protocol, runtime_checkable


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


@runtime_checkable
class PendingStore(Protocol):
    def save_pending(
        self,
        pending_id: str,
        question: str,
        ttl_seconds: int = 300,
    ) -> None:  # pragma: no cover - interface
        ...

    def get_pending(
        self,
        pending_id: str,
    ) -> Optional[PendingEntry]:  # pragma: no cover - interface
        ...

    def resolve_pending(
        self,
        pending_id: str,
    ) -> None:  # pragma: no cover - interface
        ...


class InMemoryPendingStore:
    """Simple in-memory pending store with TTL semantics.

    Methods:
    - save_pending(pending_id, question, ttl_seconds=300)
    - get_pending(pending_id) -> Optional[PendingEntry]
    - resolve_pending(pending_id) -> None
    """

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
            try:
                del self._store[pending_id]
            except KeyError:
                pass
            return None
        return entry

    def resolve_pending(self, pending_id: str) -> None:
    # remove entry if present
        self._store.pop(pending_id, None)


def default_pending_store() -> PendingStore:
    """Factory returning the default in-process pending store."""
    return InMemoryPendingStore()
