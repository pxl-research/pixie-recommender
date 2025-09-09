# Changes: conversation-loop-flow

- 2025-09-09: Started Task 1.1 (validated `LLM`), no changes made to code.

## Task 1.2: MockLLMs specification (planned)

Planned files: `pixie/core/mock_relevance_llm.py`, `pixie/core/mock_sql_llm.py`, `pixie/core/mock_refinement_llm.py` (do not create without approval)

Rationale:
- Prefer specialised mock classes per responsibility so we can later swap in different real models per task (e.g. GPT-5 for relevance, Sonnet-4 for SQL).

Specifications:

- Class: MockRelevanceLLM(LLM)
  - Constructor: def __init__(self, model_name: str = "mock-relevance-llm", deterministic: bool = True)
  - Methods:
    - is_relevant(question: str) -> bool
      - Detects presence of words "printer" or "printers" (case-insensitive)
      - Returns True on match, False otherwise
    - Behavior: deterministic=True returns a strict boolean; deterministic=False may add a small probability of false/true to simulate model noise

- Class: MockSQLLLM(LLM)
  - Constructor: def __init__(self, model_name: str = "mock-sql-llm", deterministic: bool = True)
  - Methods:
    - generate_sql(question: str, attributes: dict | None = None) -> str
      - Returns a canonical query for the product domain. For the initial scope always return: "SELECT * FROM printers;"
    - Behavior: deterministic=True returns exact string; deterministic=False may vary whitespace or add a harmless ORDER BY clause

- Class: MockRefinementLLM(LLM)
  - Constructor: def __init__(self, model_name: str = "mock-refinement-llm", deterministic: bool = True)
  - Methods:
    - generate_refinement_question(context: dict) -> str | None
      - Question sequencing: ask about `budget` first, then `brand`, then `technology`.
      - If `budget` missing -> ask budget-related question; else if `brand` missing -> ask brand; else if `technology` missing -> ask technology; else return None
    - Behavior: deterministic=True returns consistent phrasing; deterministic=False may pick from a small set of paraphrases

Orchestration:
- Later we will provide a thin factory or composite adapter (`MockLLMSet`) that groups these three classes so `ConversationLoopManager` can request the appropriate model for each subtask.

Error modes / behavior:
- Default deterministic=True. When deterministic=False slight randomized variations are allowed for realism.
- Methods should be side-effect free and fast.

Testing notes:
- Unit tests will assert exact outputs when deterministic=True for each specialized class.


## Progress
- [x] Task 1.1 validated (no code changes)
- [x] Task 1.2 planned and implemented (mock LLM classes + helper + tests)

Notes / impact on next tasks:
- ConversationLoopManager will accept explicit model instances in its constructor (we will implement with simple DI, no factory) to keep the design minimal.
- Tests and subsequent planning (Task 2.1/2.2) should assume the three-role injection pattern.
- No changes to abstract `LLM` required.

## Dev environment: minimal dev container (planning-only)

Rationale:
- Some developers run tools inside containers; earlier we observed PATH/shebang mismatches for host-installed tools. A minimal dev container standardizes tooling (python, pytest, black, ruff) and ensures consistent CI/dev behavior.

Planned artifacts (do not create without approval):
- `infra/docker/dev.Dockerfile` — small image (python:3.12-slim) with pip, ruff, black, pytest installed
- `docker-compose.dev.yml` (or extend existing) — service `dev` mounting the repo and exposing a tiny command entrypoint for running linters/tests

Minimal dev image spec (summary):
- Base: `python:3.12-slim`
- Install: `pip install --upgrade pip && pip install ruff black pytest`
- Workdir: `/workspace` with a mounted volume from host
- Entrypoint: none (use `docker compose run dev <cmd>`)

Example dev-compose usage (for docs):
```
docker compose -f docker-compose.dev.yml run --rm dev python -m pytest
docker compose -f docker-compose.dev.yml run --rm dev python -m ruff check . --fix
docker compose -f docker-compose.dev.yml run --rm dev python -m black .
```

Impact on workflow:
- Low risk, provides reproducible dev tooling. Implementation can be done once Task 2.2 wiring is stable.
- Next action when approved: add `infra/docker/Dockerfile.dev`, update `docker-compose.dev.yml`, and add a brief README snippet explaining commands.

## Status update (2025-09-09)

- Branch: `v0.3_pixie_mock_real_flow`
- Latest local commit: `32fed90` (feat(core): add ConversationLoopManager, integrate into Pixie, tests and dev container plan)
- Tests: the newly-added tests for the mock LLMs and the ConversationLoopManager pass when run selectively (`tests/test_mock_llms.py` and `tests/test_conversation_loop.py`).
- Full test-suite note: running `pytest` for the whole repo currently fails during collection due to a missing optional dependency (`fastapi`). This is an environment issue, not a logic failure in the new code.

Immediate next recommended steps:

- Install dev/test dependencies locally and run the full test suite:

```bash
python3 -m pip install -r requirements-dev.txt  # or install fastapi/tests deps manually
python3 -m pytest -q
```

- Or: create the planned dev-container and run the full tests inside it for a hermetic run.

If you want, I can either install the missing dev deps here and re-run the full test-suite, or I can add the dev-container artifacts and run tests inside the container — tell me which you prefer and I'll do it.

- 2025-09-09 (revert): Reverted transient `deterministic` flag changes to
  `mock_*_llm.py` and `mock_llm_set.py` after review — the defaults and tests
  are unchanged and behavior remains stable. Kept this note for audit/history.

