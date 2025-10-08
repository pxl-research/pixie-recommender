from __future__ import annotations

from enum import Enum, auto


class ConversationAction(Enum):
    """Enumerates the high-level actions the conversation loop can take."""

    ASK_ATTRIBUTE = auto()
    REFINE_RESULTS = auto()
    SHOW_RESULTS = auto()
    END = auto()
