# pixie-core

[![Container smoke test](https://github.com/pxl-research/pixie-core/actions/workflows/container-smoke-test.yml/badge.svg)](https://github.com/pxl-research/pixie-core/actions/workflows/container-smoke-test.yml)

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

Note on checks:

- `CI` (github) runs lint and unit tests in the runner.
- `Container smoke` builds the dev image and runs integration smoke tests (PRs of manual dispatch).

Recommended local test command: `./scripts/dev_test.sh pytest` (or `make dev-test`).

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

Quick command (recommended):

```bash
./scripts/dev_test.sh pytest
```

Or use the Makefile target `make dev-test` which delegates to the canonical
helper script `./scripts/dev_test.sh`.

## Configuration

### Environment Variables

Pixie Core uses simple environment variable configuration with sensible defaults for development.

### Azure OpenAI Configuration

- `AZURE_OPENAI_API_VERSION`: API version for Azure OpenAI (default: "2024-02-01")
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL (default: `https://example.openai.azure.com/`)
- `AZURE_OPENAI_KEY`: Azure OpenAI API key (default: "dummy-key-for-development")
- `AZURE_OPENAI_MODEL`: Azure OpenAI model deployment name (default: "gpt-4")

### Search Configuration

- `PIXIE_PRINTER_DATA`: Path to printer data JSON file (default: "pixie/core/data/printers.json")
- `PIXIE_DEFAULT_PAGE_SIZE`: Default page size for search results (default: 10)

### Configuration Examples

```bash
# Development (default - uses dummy values)
export AZURE_OPENAI_ENDPOINT=https://your-dev-endpoint.openai.azure.com/
export AZURE_OPENAI_KEY=your-dev-key

# Production
export AZURE_OPENAI_ENDPOINT=https://your-prod-endpoint.openai.azure.com/
export AZURE_OPENAI_KEY=your-production-key
export PIXIE_DEFAULT_PAGE_SIZE=20
```

## Azure OpenAI configuration

To run the application with real Azure OpenAI LLMs, set the following
environment variables in your `.env.dev` file (or your environment):

- `AZURE_OPENAI_API_VERSION`: e.g. `2024-10-01`
- `AZURE_OPENAI_ENDPOINT`: your Azure OpenAI endpoint, e.g. `https://<your-resource>.openai.azure.com/`
- `AZURE_OPENAI_KEY`: your Azure OpenAI API key
- `AZURE_OPENAI_MODEL`: deployed model name (deployment id), e.g. `gpt-5-chat`

You can copy the example file and update the values:

```bash
cp .env.example .env.dev
# edit .env.dev and add the Azure values
```
