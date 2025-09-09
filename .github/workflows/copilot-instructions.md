## Tests
## Run & test (Docker-first)
Deze repo wordt ontwikkeld en getest in een ontwikkelcontainer. Gebruik altijd de dev Dockerfile / compose flow
om de applicatie te proberen en om pytest binnen de container te draaien — dat voorkomt lokale interpreter- of dependency-mismatch.
### 1) App snel uitproberen
1. Build en start de dev container (detach):
```bash
docker compose -f docker-compose.dev.yml up --build -d
```
2. Controleer de health endpoint:
```bash
curl -fsS http://localhost:${PORT_API:-8012}/health
```
3. Stuur een voorbeeldvraag:
```bash
curl -s -X POST "http://localhost:${PORT_API:-8012}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Ik zoek een nieuwe printer"}' | jq
```
4. Stop en ruim op als je klaar bent:
```bash
docker compose -f docker-compose.dev.yml down -v
```
### 2) Tests draaien binnen de container (aanbevolen)
Gebruik de service naam `api` om commands in de container te draaien. Zo weet je zeker dat je tests met dezelfde Python/venv en dependencies lopen als de app.
- Smoke tests (repository bevat een helper):
```bash
docker compose -f docker-compose.dev.yml up --build -d
container=$(docker compose -f docker-compose.dev.yml ps -q api)
docker exec -it "$container" /bin/bash -lc "python /app/scripts/run_in_container_tests.py"
docker compose -f docker-compose.dev.yml down -v
```
- Pytest (hele test-suite):
```bash
# optioneel: start container first
docker compose -f docker-compose.dev.yml up --build -d
docker compose -f docker-compose.dev.yml exec api /bin/bash -lc "uv run python -m pytest -q"
docker compose -f docker-compose.dev.yml down -v
```
- Pytest voor één testbestand of testcase:
```bash
docker compose -f docker-compose.dev.yml exec api /bin/bash -lc "uv run python -m pytest tests/test_logging.py::test_some_case -q -k some_name"
```
### 3) Controleer of pytest beschikbaar is in de container
Probleem: soms is pytest niet aanwezig in de container (bijvoorbeeld wanneer dev-extras niet zijn geïnstalleerd). Controleer zo:
```bash
docker compose -f docker-compose.dev.yml up --build -d
docker compose -f docker-compose.dev.yml exec api /bin/bash -lc "which pytest || (echo 'pytest missing' && python -m pip list | grep -E 'pytest|uv')"
```
Als pytest ontbreekt, zijn mogelijke oorzaken en oplossingen:
- Oorzaak: de dev extras (project optional-dependencies dev) zijn niet geïnstalleerd tijdens image build.
  - Oplossing: zorg dat de dev build-stap `uv sync --extra dev` wordt uitgevoerd (Dockerfile.dev doet dit standaard). Herbuild expliciet:
```bash
docker compose -f docker-compose.dev.yml build --no-cache api
```
- Oorzaak: oude image / cache; Oplossing: forceer een rebuild en herstart (zie boven).
- Oorzaak: container draait niet in de venv; Oplossing: gebruik `uv run` of controleer PATH in container. Voor consistente runs raden we `uv run python -m pytest ...` aan.
### 4) Snelle non-interactieve runs (CI style)
Je kunt in CI of scripts de container éénmalig starten, tests runnen en verwijderen met `docker compose run --rm`:
```bash
docker compose -f docker-compose.dev.yml run --rm api /bin/bash -lc "uv run python -m pytest -q"
```
Dit start de service image, voert het command uit en verwijdert de container daarna.
### 5) Tips en best practices
- Gebruik altijd de `api` service uit `docker-compose.dev.yml` om tests en debug-commands uit te voeren.
- Gebruik `uv run` zodat de image's venv en PATH consistent zijn met de runtime van de app.
- Voeg in CI dezelfde build-step toe die dev-extras installeert wanneer je tests wil draaien.
- Overweeg een korte Makefile of script (bv. `scripts/dev_test.sh`) die de voorbeeld-commando's bundelt zodat contributors niet telkens hoeven te onthouden welke flags.

---

Deze instructies minimaliseren fouten door lokaal verschillende Pythons of missende dev dependencies. Als je wilt, voeg ik een kleine `scripts/dev_test.sh` helper en een `Makefile` target toe zodat teams één commando hoeven te onthouden.

### Developer helper script

We voegen een helper script `scripts/dev_test.sh` dat veelvoorkomende flows automatiseert:

- `./scripts/dev_test.sh smoke` — build + start container, run smoke tests helper, teardown
- `./scripts/dev_test.sh pytest` — build + start container, run full pytest suite, teardown
- `./scripts/dev_test.sh all` — smoke then pytest

Of gebruik de Makefile shortcuts:

```bash
make dev-test-smoke
make dev-test-pytest
make dev-test-all
```

Het script is idempotent en ruimt op na voltooiing (down -v). Gebruik het als de canonical developer entrypoint voor lokale test runs.
# PiXie Agent - Copilot Instructions

## Project Overview

PiXie is an AI-powered conversational shopping assistant that helps customers find products through natural language interaction. The system uses internally accessible business information to understand, analyze complex product questions, and generate relevant recommendations.

## Core Concept

The system works as a digital sales assistant that:

- **Understands customer questions** in natural language, no matter how complex or vague they are formulated
- **Asks intelligent follow-up questions** to refine product specifications
- **Searches product catalogs** with both structured data and unstructured documentation
- **Provides personalized recommendations** with explanations and source references

## Technical Architecture

The system facilitates **natural product discovery** by guiding customers from vague intentions to specific product matches. It manages **complex conversations** that develop over multiple interactions, maintaining context and preferences.

The architecture supports **multi-source information retrieval**, making both structured product data and unstructured documentation searchable for accurate and complete answers.

## Business Value

PiXie automates the product advisory process by conducting human-like conversations while simultaneously having access to complete product catalogs and documentation. This results in better customer experience and increased conversion without the overhead of human customer service agents.

## Core Flows

Pixie supports several conversation patterns. A number of flows are illustrated with a simplified example dialogue. These flows summarize the most typical user interactions with Pixie and are representative of how the assistant behaves in practice.

### 1. Product found
A vague product request is gradually refined through follow-up questions until a concrete product list can be returned.

**Example**
- **Q:** I’m looking for a new printer  
- **A:** What is your budget for a printer? Less than €150, between €150–€300, more than €300, or no preference?  
- **Q:** Maximum €200  
- **A:** Which brand do you prefer? Brother, BenQ, HP, Kyocera, … or no preference?  
- **Q:** Brother  
- **A:** Which printing technology? Inkjet, laser, thermal inkjet, or no preference?  
- **Q:** Laser  
- **A:** Here are matching printers:  
  1. Brother XC 2570 – €199 – short description  
  2. Brother XT 3560 – €159 – short description  

### 2. Not relevant
When the question falls outside supported domains, Pixie gives a clear early exit.

**Example**
- **Q:** I’m looking for my mom  
- **A:** Sorry, I can’t help with that. I only have information about printers, laptops, smartphones, …

### 3. No results
Valid filters are applied but the query yields zero matches. Pixie responds gracefully and suggests alternatives.

**Example**
- **Q:** I want a Brother laser printer under €50  
- **A:** Unfortunately, no printers match your criteria. Please try again with a broader budget or contact support for assistance.

### 4. Too many results
When the query returns more than N results, Pixie offers refinement strategies or provides a manageable subset.

**Example**
- **Q:** I’m looking for a new printer  
- **A:** What is your budget?  
- **Q:** No preference  
- **A:** Which brand?  
- **Q:** No preference  
- **A:** Which printing technology?  
- **Q:** No preference  
- **A:** I found 152 printers. Would you like to see the top 5 sorted by price, or a random sample of 5?  
- **Q:** Sorted by price  
- **A:** Here are the top 5 printers:  
  1. Brother ZX 1570 – €69 – short description  
  2. HP Inkjet 234 – €79 – short description  
  3. Kyocera T70 – €99 – short description  
  4. Brother XT 3560 – €99 – short description  
  5. HP Inkjet 1234 – €109 – short description

## Vision and Long-term Goal

Pixie is designed to evolve into a modular and extensible system that can integrate with different data sources and reasoning engines. In the current version, adapters are mocked, but the long-term goal is to connect them as independent services through the Model Context Protocol (MCP).

The assistant should ultimately be able to:
- Seamlessly combine information from multiple adapters such as RAG, TabularRAG, and future specialized modules
- Reliably decide when more information is needed and phrase natural follow-up questions
- Provide transparent answers with traceable origins
- Function as a plug-and-play component that can be embedded in various user interfaces

## Development Approach

Pixie is intentionally built in incremental milestones.  
We start with a fully mocked prototype to validate flows and contracts, and gradually replace mocked components with real adapters and services.  
This step-by-step approach ensures that the system remains testable, understandable, and stable while steadily increasing functionality and realism.
