# pixie-core

[![Container smoke test](https://github.com/pxl-research/pixie-core/actions/workflows/container-smoke-test.yml/badge.svg)](https://github.com/pxl-research/pixie-core/actions/workflows/container-smoke-test.yml)

> **🚨 FOR COPILOT/AI AGENTS:** This is a CONTAINER-FIRST project. NEVER run tests locally!  
> **✅ ONLY use:** `./scripts/dev_test.sh pytest`  
> **See:** `.github/workflows/copilot-instructions.md` for full details.

AI-powered product recommendation system supporting multiple categories: printers, laptops, computers, and smartphones. Uses Azure OpenAI LLMs for intelligent conversation flows and category-aware product recommendations.

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

**Nieuwe vraag (verschillende categorieën):**

```bash
# Printer
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Ik zoek een nieuwe printer"}'

# Laptop
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Ik zoek een nieuwe laptop"}'

# Smartphone
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Ik zoek een nieuwe smartphone"}'

# Computer
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Ik zoek een nieuwe computer"}'
```

**Reply op pending vraag:**

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"pending_id": "pending-xxxx", "message": "Minder dan 150 euro"}'
```

## Flows en voorbeeldzinnen

Pixie Core ondersteunt intelligente productaanbevelingen voor vier categorieën:

### Printers

- **Product discovery:** `"Ik zoek een nieuwe printer"` → budget → merk → technologie (inkjet/laser)
- **Specifieke zoekopdracht:** `"Ik wil een Brother laserprinter onder de €150"`

### Laptops

- **Product discovery:** `"Ik zoek een nieuwe laptop"` → budget → merk → schermgrootte
- **Specifieke zoekopdracht:** `"Ik wil een Dell laptop met 13 inch scherm"`

### Smartphones

- **Product discovery:** `"Ik zoek een nieuwe smartphone"` → budget → merk → schermgrootte
- **Specifieke zoekopdracht:** `"Ik wil een Samsung telefoon onder de €500"`

### Computers

- **Product discovery:** `"Ik zoek een nieuwe computer"` → budget → merk → processor
- **Specifieke zoekopdracht:** `"Ik wil een gaming computer met Intel i7"`

### Algemene flows

- **Geen resultaten:** Specifieke eisen die niet matchen → `{"type": "no_results"}`
- **Niet relevant:** `"Waar kan ik mijn moeder vinden?"` → `{"type": "not_relevant"}`
- **Te veel resultaten:** Vage query → vraagt om verfijning

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

## Multi-Category Product Support

Pixie Core intelligently detects product categories from user questions and provides category-specific conversation flows:

### Category Detection

The system automatically detects the product category from natural language questions:

- **Printers**: Keywords like "printer", "print", "drukker", "laser", "inkjet"
- **Laptops**: Keywords like "laptop", "notebook", "macbook", "chromebook"
- **Smartphones**: Keywords like "smartphone", "phone", "telefoon", "iphone", "android"
- **Computers**: Keywords like "computer", "pc", "desktop", "workstation"

### Category-Specific Attributes

Each product category has tailored attributes for precise recommendations:

| Category | Key Attributes |
|----------|----------------|
| Printers | budget, brand, technology, has_color, is_multifunction |
| Laptops | budget, brand, screen_size, processor, ram, storage |
| Smartphones | budget, brand, screen_size, storage, operating_system |
| Computers | budget, brand, processor, ram, storage, form_factor |

### Intelligent SQL Generation

The system generates category-aware SQL queries with:

- Proper table selection based on detected category
- Category-specific filtering logic
- Fallback mechanisms for robust operation
- Support for both Azure OpenAI and mock LLM implementations

### Conversation Flow

1. **Category Detection**: Automatically identify product type from question
2. **Attribute Collection**: Ask category-relevant questions in optimal order
3. **SQL Generation**: Create targeted database queries
4. **Result Filtering**: Apply category-specific business logic
5. **Response Generation**: Provide personalized recommendations

## Architecture Overview

### Core Components

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Layer     │    │  Conversation     │    │   LLM Layer     │
│   (FastAPI)     │◄──►│   Loop Manager    │◄──►│  (Azure OpenAI) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Data Access    │    │   Attribute       │    │   Schema        │
│   (JSON/SQL)    │◄──►│   Management      │◄──►│   Management    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Features

- **🔍 Intelligent Category Detection**: Automatic product category identification
- **💬 Dynamic Conversation Flows**: Category-specific question sequences
- **⚡ High Performance**: Sub-second response times with robust fallbacks
- **🔧 Flexible Configuration**: Environment-based configuration for different deployments
- **🧪 Comprehensive Testing**: Full test coverage for all components and categories
- **📊 Multi-Category Support**: Unified system handling printers, laptops, computers, smartphones

### Data Flow

1. User submits question via API
2. Relevance LLM determines if question is product-related
3. Category detection LLM identifies specific product category
4. Attribute manager loads category-specific question flow
5. Conversation loop collects user preferences through targeted questions
6. SQL generation LLM creates category-aware database queries
7. Search engine applies category-specific filtering and ranking
8. Results are returned with personalized recommendations

### Azure OpenAI Configuration

- `AZURE_OPENAI_API_VERSION`: API version for Azure OpenAI (default: "2024-02-01")
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL (default: `https://example.openai.azure.com/`)
- `AZURE_OPENAI_KEY`: Azure OpenAI API key (default: "dummy-key-for-development")
- `AZURE_OPENAI_MODEL`: Azure OpenAI model deployment name (default: "gpt-4")

### Search Configuration

- `PIXIE_PRINTER_DATA`: Path to printer data JSON file (default: "pixie/core/data/printers.json")
- `PIXIE_LAPTOP_DATA`: Path to laptop data JSON file (default: "pixie/core/data/laptops.json")
- `PIXIE_SMARTPHONE_DATA`: Path to smartphone data JSON file (default: "pixie/core/data/smartphones.json")
- `PIXIE_COMPUTER_DATA`: Path to computer data JSON file (default: "pixie/core/data/computers.json")
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
