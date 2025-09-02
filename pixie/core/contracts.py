from typing import List, Optional

from pydantic import BaseModel, model_validator


class AskResponse(BaseModel):
    """Discriminated union wrapper for AskResponse variants.

    This model uses the explicit `type` field as a discriminator and
    validates each variant according to the acceptance criteria in Issue 9.
    """

    type: str
    text: Optional[str] = None
    prompt: Optional[str] = None
    pending_id: Optional[str] = None
    needed_info: Optional[List[str]] = None
    reason: Optional[str] = None

    @model_validator(mode="after")
    def _validate_union(self):
        t = getattr(self, "type", None)
        if t == "answer":
            if not getattr(self, "text", None):
                raise ValueError("'text' is required for type 'answer'")
        elif t == "ask_user":
            if not getattr(self, "prompt", None):
                raise ValueError("'prompt' is required for type 'ask_user'")
            if not getattr(self, "pending_id", None):
                raise ValueError("'pending_id' is required for type 'ask_user'")
            nif = getattr(self, "needed_info", None)
            if nif is not None:
                if not isinstance(nif, list) or not all(
                    isinstance(x, str) for x in nif
                ):
                    raise ValueError(
                        "'needed_info' must be a list of strings if provided"
                    )
        elif t == "error":
            if not getattr(self, "reason", None):
                raise ValueError("'reason' is required for type 'error'")
        else:
            raise ValueError("invalid AskResponse type")
        return self
