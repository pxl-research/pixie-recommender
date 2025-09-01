from typing import Literal, List, Optional

from pydantic import BaseModel, Field, model_validator


# Discriminated union for AskResponse (LLM-first)
class AnswerResponse(BaseModel):
    type: Literal["answer"] = "answer"
    text: str


class AskUserResponse(BaseModel):
    type: Literal["ask_user"] = "ask_user"
    prompt: str
    pending_id: str
    needed_info: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    type: Literal["error"] = "error"
    reason: str


class AskResponse(BaseModel):
    """Discriminated union wrapper for AskResponse variants.

    This model uses the explicit `type` field as a discriminator and
    validates each variant according to the acceptance criteria in Issue 9.
    """

    # Basic fields that may appear on variants; kept optional so the
    # wrapper can accept any variant shape and the validator enforces
    # presence where required.
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
            # ensure 'text' present
            if not getattr(self, "text", None):
                raise ValueError("'text' is required for type 'answer'")
        elif t == "ask_user":
            if not getattr(self, "prompt", None):
                raise ValueError("'prompt' is required for type 'ask_user'")
            if not getattr(self, "pending_id", None):
                raise ValueError("'pending_id' is required for type 'ask_user'")
            nif = getattr(self, "needed_info", None)
            if nif is not None:
                if not isinstance(nif, list) or not all(isinstance(x, str) for x in nif):
                    raise ValueError("'needed_info' must be a list of strings if provided")
        elif t == "error":
            if not getattr(self, "reason", None):
                raise ValueError("'reason' is required for type 'error'")
        else:
            raise ValueError("invalid AskResponse type")
        return self


class ReplyRequest(BaseModel):
    pending_id: str = Field(...)
    message: str = Field(...)
