# pixie-core

Minimal FastAPI service that routes product questions to Azure OpenAI. It classifies a question, asks the SQL LLM for a query, and forwards the SQL to the tabular dataset service.

## Run
```bash
cp .env.example .env.dev
docker compose -f docker-compose.dev.yml up --build
```

Set `PIXIE_TABULAR_API_URL`, `PIXIE_TABULAR_COLLECTION` and `PIXIE_API_KEY` in your `.env.dev`
to let Pixie query the external tabular dataset (the defaults assume the dev compose stack).

## API
POST `/ask` with `{ "question": "Ik zoek een nieuwe laptop" }` to receive an answer (or a `no_results`/`error` response). Follow-up replies are not supported in this minimal build.

## TODO
- Populate the category/attribute metadata from that dataset instead of the inline placeholders.
