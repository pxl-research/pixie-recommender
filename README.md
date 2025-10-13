# pixie-core

Minimal FastAPI service that routes product questions to Azure OpenAI. It classifies a question, optionally asks a refinement LLM for follow-up details, turns the answers into structured filters, and forwards those filters to the tabular dataset service. Conversation state is stored in-memory with a TTL so follow-up questions remain consistent.

## Run

```bash
cp .env.example .env.dev
docker compose -f docker-compose.dev.yml up --build
```

Set `PIXIE_TABULAR_API_URL`, `PIXIE_TABULAR_COLLECTION` and `PIXIE_API_KEY` in your `.env.dev`
to let Pixie query the external tabular dataset (the defaults assume the dev compose stack).

## API

POST `/ask` with `{ "question": "Ik zoek een nieuwe laptop" }` to receive an answer (or a `no_results`/`error` response). When a follow-up is required the response includes a `conversation_id` that clients must echo in subsequent calls. For follow-ups send:

```json
{
  "conversation_id": "<uuid-from-response>",
  "message": "Maximaal 1200 euro alsjeblieft"
}
```

Set the environment variables `PIXIE_RESULT_THRESHOLD`, `PIXIE_MAX_REFINE_QUESTIONS`, and `PIXIE_CONVERSATION_TTL_MINUTES` to control how aggressively the service asks follow-up questions and how long conversations remain active.

## Docs

- [Conversation scenarios](docs/conversation-scenarios.md)

## TODO

- Populate the category/attribute metadata from the dataset instead of the inline placeholders.
