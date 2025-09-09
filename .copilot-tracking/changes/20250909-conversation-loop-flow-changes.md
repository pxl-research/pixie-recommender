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

