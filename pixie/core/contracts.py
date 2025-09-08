from typing import List, Optional, Dict, Any

from pydantic import BaseModel, model_validator


class Product(BaseModel):
    """Product model for product discovery responses."""
    
    id: str
    name: str
    price: float
    brand: str
    category: str
    technology: Optional[str] = None
    description: str


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
    products: Optional[List[Product]] = None
    refinement_context: Optional[Dict[str, Any]] = None
    result_count: Optional[int] = None
    supported_domains: Optional[List[str]] = None

    @model_validator(mode="after")
    def _validate_union(self):
        t = getattr(self, "type", None)
        if t == "answer":
            if not getattr(self, "text", None):
                raise ValueError("'text' is required for type 'answer'")
        elif t == "product_list":
            products = getattr(self, "products", None)
            if not products or not isinstance(products, list):
                raise ValueError("'products' list is required for type 'product_list'")
            if not getattr(self, "text", None):
                raise ValueError("'text' is required for type 'product_list'")
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
        elif t == "not_relevant":
            if not getattr(self, "text", None):
                raise ValueError("'text' is required for type 'not_relevant'")
            if not getattr(self, "supported_domains", None):
                raise ValueError("'supported_domains' is required for type 'not_relevant'")
        elif t == "no_results":
            if not getattr(self, "text", None):
                raise ValueError("'text' is required for type 'no_results'")
        elif t == "error":
            if not getattr(self, "reason", None):
                raise ValueError("'reason' is required for type 'error'")
        else:
            raise ValueError("invalid AskResponse type")
        return self
