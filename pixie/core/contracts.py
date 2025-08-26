from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    question: str = Field(min_length=1)

class AskResponse(BaseModel):
    type: str = "answer" 
    text: str