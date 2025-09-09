# pixie-core

Mock implementation van Pixie met vier hardgecodeerde flows: product discovery, geen resultaten, niet relevant, en te veel resultaten.

## Quick Start

### 1. Start de container

```bash
# Maak eventueel eerst een .env.dev bestand aan
cp .env.example .env.dev

# Start de API
docker compose -f docker-compose.dev.yml up --build
```

API is beschikbaar op `http://localhost:8000`

### 2. Stel vragen

**Nieuwe vraag:**

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Ik zoek een nieuwe printer"}'
```

**Reply op pending vraag:**

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"pending_id": "pending-xxxx", "message": "Minder dan 150 euro"}'
```

## Flows en voorbeeldzinnen

- **Product discovery:** `"Ik zoek een nieuwe printer"` → start conversatie (budget/merk/specs)
- **Geen resultaten:** `"Ik wil een Brother laserprinter onder de €50"` → `{"type": "no_results"}`  
- **Niet relevant:** `"Waar kan ik mijn moeder vinden?"` → `{"type": "not_relevant"}`
- **Te veel resultaten:** `"Ik heb een printer nodig"` → vraagt om verfijning

docker compose -f docker-compose.dev.yml up --build -d
docker compose -f docker-compose.dev.yml down -v
<!-- Tests are documented in .github/workflows/copilot-instructions.md -->

Lokale en CI container-smoke tests delen nu dezelfde helper. Raadpleeg
`.github/workflows/copilot-instructions.md` voor korte, up-to-date instructies.

De CI workflow gebruikt `/app/scripts/wait_for_health_container.py` en
`/app/scripts/run_in_container_tests.py` zodat lokale runs en CI sterk op
elkaar lijken.

## Running tests inside the dev container (recommended)

Use the `dev` service to run tests from a hermetic environment that uses the
project lockfile (`uv.lock`) and `uv` to create the venv. This is the
recommended way to run tests locally so they mirror CI.

Quick command:

```bash
docker compose -f docker-compose.dev.yml run --rm dev uv sync --extra dev && \
  docker compose -f docker-compose.dev.yml run --rm dev uv run python -m pytest -q
```

Or use the Makefile target `make dev-test` (added to the repo) which runs the
same commands. The Makefile now delegates to the canonical helper script so
`./scripts/dev_test.sh` is the single-source of truth for dev/test orchestration
and `make dev-test` simply calls `./scripts/dev_test.sh pytest`.
