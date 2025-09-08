# pixie-core

Simplified, API-first rebuild of Pixie with a mock-first approach

## Features

### v0.2 Ask-User Flow with Unified API

The system intelligently handles questions through a single `/ask` endpoint that:

- **Auto-detects Request Type**: New question vs. reply to pending question based on request structure
- **FakeRAGAdapter**: Quick semantic retrieval
- **FakeTabularRAG**: Structured data analysis  
- **Confidence Scoring**: Smart decision-making when to ask users for clarification
- **Seamless UX**: No endpoint complexity for clients - one endpoint for all interactions

## Quick Start

### Development Setup

```bash
# Install dependencies
uv install

# Run development server
# pixie-core

Eenvoudige, API-first mock van Pixie gericht op een paar hardgecodeerde voorbeeldflows.

## Wat is er veranderd

Deze repository bevat nu een zeer eenvoudige, dependency-vrije mock-implementatie die exact de vier voorbeeldflows volgt:

- Product discovery multi-turn: startzinnen zoals `"I'm looking for a new printer"` voeren een korte conversatie (budget → merk → technologie → resultaten).
- Geen resultaten: zinnen zoals `"I want a Brother laser printer under €50"` geven meteen een `no_results` respons.
- Niet relevant: zinnen zoals `"I'm looking for my mom"` worden als buiten scope afgewezen (`not_relevant`).
- Te veel resultaten: wanneer de matchset groter is dan de drempel, vraagt het systeem of je wilt "sorted by price" of een "random sample" van 5.

De implementatie staat in `pixie/core/pixie.py`. De response-contracten zitten in `pixie/core/contracts.py`. De tijdelijke multi-turn staat wordt bewaard in `pixie/core/pending_store.py`.

## Kort: gebruik en voorbeelden

De API biedt één endpoint `/ask` (zie `apps/api/main.py`). De code is zo geschreven dat je de `ask`-functie ook direct kunt importeren en gebruiken zonder FastAPI te installeren.


# pixie-core

Eenvoudige, API-first mock van Pixie met focus op een paar hardgecodeerde voorbeeldflows.

## Wat is er veranderd

Deze repository bevat nu een kleine, dependency-vrije mock-implementatie die exact de vier voorbeeldflows volgt:

- Product discovery multi-turn: startzinnen zoals "I'm looking for a new printer" voeren een korte conversatie (budget → merk → technologie → resultaten).
- Geen resultaten: zinnen zoals "I want a Brother laser printer under €50" geven meteen een `no_results` respons.
- Niet relevant: zinnen zoals "I'm looking for my mom" worden als buiten scope afgewezen (`not_relevant`).
- Te veel resultaten: wanneer de matchset groter is dan de drempel, vraagt het systeem of je wilt "sorted by price" of een "random sample" van 5.

De implementatie staat in `pixie/core/pixie.py`. De response-contracten zitten in `pixie/core/contracts.py`. De tijdelijke multi-turn staat wordt bewaard in `pixie/core/pending_store.py`.

## Kort: gebruik en voorbeelden

De API biedt één endpoint `/ask` (zie `apps/api/main.py`). De code is zo geschreven dat je de `ask`-functie ook direct kunt importeren en gebruiken zonder FastAPI te installeren.

Voorbeeld: nieuwe vraag (curl)

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "I\'m looking for a new printer"}'
```

Voorbeeld: reply naar een pending vraag (gebruik de `pending_id` uit de vorige response)

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"pending_id": "pending-1a2b3c4d", "message": "No preference"}'
```

Specifieke voorbeeldzinnen (deze worden letterlijk herkend door de mock):

- "I'm looking for a new printer" → start product discovery multi-turn
- "I want a Brother laser printer under €50" → `no_results`
- "I'm looking for my mom" → `not_relevant`

Antwoorden zijn eenvoudige JSON-dicts, bijvoorbeeld:

```json
{ "type": "ask_user", "prompt": "What is your budget for a printer? ...", "pending_id": "pending-xxxx" }
```

of

```json
{ "type": "answer", "text": "Here are matching printers:\n1. ..." }
```

Direct lokaal gebruiken zonder FastAPI

```python
from pixie.core.pixie import Pixie

pixie = Pixie()
resp = pixie.answer("I'm looking for a new printer")
print(resp.dict())

# Voor een follow-up reply:
# resp = pixie.reply(pending_id, 'Less than €150')
```

Run server (optioneel, als je FastAPI + uvicorn hebt)

```bash
# start de API op poort 8000
uv run uvicorn apps.api.main:app --reload
```

Tests

```bash
uv run python -m pytest tests/ -v
```

## Waar te vinden

- `apps/api/main.py` — eenvoudige HTTP wrapper; route-registratie is voorwaardelijk zodat je de `ask`-functie ook zonder FastAPI kunt importeren.
- `pixie/core/pixie.py` — de hardgecodeerde mock en de vier flows.
- `pixie/core/contracts.py` — eenvoudige dataclass-response contracten (geen Pydantic vereist).
- `pixie/core/pending_store.py` — in-memory pending store voor multi-turn state.

## Notities

Dit is een deliberately small mock bedoeld voor demonstratie en development; het is geen productiesservice. Als je wilt dat ik dit uitbreid met extra voorbeelden, i18n (Nederlands), of echte RAG-adapters, zeg het dan.

## Run in Docker (aanbevolen)

Deze repository is bedoeld om in containers te draaien in plaats van rechtstreeks op het lokale systeem. Gebruik de meegeleverde docker-compose configuratie om de API te bouwen en te starten.

Voorbeeld met Docker Compose (development):

```bash
# bouw en start de services
docker compose -f docker-compose.dev.yml up --build

# of (oude syntax)
docker-compose -f docker-compose.dev.yml up --build
```

Na het opstarten is de API normaal beschikbaar op `http://localhost:8000`. Je kunt hetzelfde curl-voorbeeld als hierboven gebruiken om de `/ask` endpoint aan te roepen.

Voorbeeld curl (nieuw vraag):

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Ik zoek een nieuwe printer"}'
```

Als je wil dat ik de docker-compose of Dockerfile aanpas (bijv. andere poort, healthchecks, of een klein Makefile) dan maak ik die wijziging graag.

## Container smoke test (CI)

Er is een GitHub Actions workflow toegevoegd (`.github/workflows/container-smoke-test.yml`) die bij PR's:

- de dev compose stack bouwt en start
- wacht op de `/health` endpoint
- voert het container-side testscript `/app/scripts/run_in_container_tests.py` uit
- uploadt `pixie_test_output.json` als artifact

Je kunt dezelfde smoke test lokaal uitvoeren met:

```bash
# start services
docker compose -f docker-compose.dev.yml up --build -d

# run the test script inside the api container
container=$(docker compose -f docker-compose.dev.yml ps -q api)
docker exec "$container" python /app/scripts/run_in_container_tests.py

# fetch the output
docker cp "$container":/app/pixie_test_output.json ./pixie_test_output.json

# teardown
docker compose -f docker-compose.dev.yml down -v
```

Het `pixie_test_output.json` bestand bevat de JSON-antwoorden van de vier voorbeeldflows en wordt ook als artifact in CI geüpload.

