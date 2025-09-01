from typing import Literal

from pydantic import BaseModel, model_validator


class AskResponse(BaseModel):
    """Minimal response model supporting direct answers and ask-user flows.

    For ask_user responses the `payload` is a simple mapping which must
    include a non-empty `pending_id` to correlate replies.
    """

    type: Literal["answer", "ask_user"] = "answer"
    text: str | None = None
    payload: dict | None = None

    @model_validator(mode="after")
    def _validate_variant(self):
        if self.type == "answer":
            if not self.text:
                raise ValueError("'text' is required when type == 'answer'")
        elif self.type == "ask_user":
            if not self.payload or not isinstance(self.payload, dict):
                raise ValueError("'payload' dict is required when type == 'ask_user'")
            # ensure pending_id present and non-empty
            pending = self.payload.get("pending_id")
            if not pending or not isinstance(pending, str):
                raise ValueError("payload must contain a non-empty 'pending_id'")
        return self


class InteractRequest(BaseModel):
    """Unified request model for clients: either a new question or a reply."""

    pending_id: str | None = None
    question: str | None = None
    reply_text: str | None = None

    @model_validator(mode="after")
    def _validate_shape(self):
        if self.pending_id is not None:
            if not self.reply_text:
                raise ValueError("reply_text is required when pending_id is present")
        else:
            if not self.question:
                raise ValueError("question is required when pending_id is not present")
        return self
