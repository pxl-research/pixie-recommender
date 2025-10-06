from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AskResponse:

    type: str  # answer, ask_user, not_relevant, error
    text: Optional[str] = None
    prompt: Optional[str] = None
    pending_id: Optional[str] = None
    reason: Optional[str] = None

    # Provide attribute-style access like Pydantic models had
    def dict(self) -> dict:
        return {
            "type": self.type,
            "text": self.text,
            "prompt": self.prompt,
            "pending_id": self.pending_id,
            "reason": self.reason,
        }
