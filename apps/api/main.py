from fastapi import FastAPI
from pixie.core.contracts import AskRequest, AskResponse
from pixie.core.pixie import Pixie

app = FastAPI(title="Pixie Core API", version="0.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    # v0.0: deterministisch mock-antwoord via Pixie helper
    return Pixie.answer(req.question)
