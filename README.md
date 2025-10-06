# pixie-core

Minimal FastAPI service that routes product questions to Azure OpenAI. It classifies a question, asks the SQL LLM for a query, and forwards the SQL to a search stub (to be replaced by the real dataset service).

## Run
```bash
cp .env.example .env.dev
docker compose -f docker-compose.dev.yml up --build
```

## API
POST `/ask` with `{ "question": "Ik zoek een nieuwe laptop" }` to receive an answer (or a `no_results`/`error` response). Follow-up replies are not supported in this minimal build.

## TODO
- Replace the search stub with a call into the external dataset container.
- Populate the category/attribute metadata from that dataset instead of the inline placeholders.
