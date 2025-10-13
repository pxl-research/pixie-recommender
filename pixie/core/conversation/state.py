from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Set


@dataclass
class ConversationState:
    conversation_id: str
    category: str
    filters: List[Dict[str, Any]] = field(default_factory=list)
    asked_attributes: Set[str] = field(default_factory=set)
    question_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    current_attribute: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)
