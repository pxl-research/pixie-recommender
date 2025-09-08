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

## Tests

```bash
# Lokale smoke test
docker compose -f docker-compose.dev.yml up --build -d
container=$(docker compose -f docker-compose.dev.yml ps -q api)
docker exec "$container" python /app/scripts/run_in_container_tests.py
docker compose -f docker-compose.dev.yml down -v

# Unit tests
uv run python -m pytest tests/ -v
```
