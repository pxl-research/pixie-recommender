# pixie-core

Minimal FastAPI service that routes product conversations to Azure LLMs. It collects a few attributes, generates SQL, and forwards the query to an external data service.

## Run
```bash
cp .env.example .env.dev
docker compose -f docker-compose.dev.yml up --build
```

## API
POST `/ask` with `{ "question": "Ik zoek een nieuwe laptop" }` starts a conversation. Use `{ "pending_id": "...", "message": "Minder dan 1000 euro" }` to answer follow-up questions.
