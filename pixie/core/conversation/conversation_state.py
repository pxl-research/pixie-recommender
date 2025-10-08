"""Lightweight conversation state dataclass."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo


_BRUSSELS_TZ = ZoneInfo("Europe/Brussels")


def _now_brussels() -> datetime:
    return datetime.now(tz=_BRUSSELS_TZ)


@dataclass
class ConversationState:
    conversation_id: UUID
    turns: list[str] = field(default_factory=list)
    active_filters: list[dict[str, Any]] = field(default_factory=list)
    requested_attributes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    category: str | None = None
    pending_attribute: dict[str, Any] | None = None
    last_prompt: str | None = None
    question_count: int = 0
    last_action: str | None = None
    status: str = "new"
    created_at: datetime = field(default_factory=_now_brussels)
    updated_at: datetime = field(default_factory=_now_brussels)
