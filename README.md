# pixie-core

Minimal FastAPI service that routes product questions to Azure OpenAI. It classifies a question, optionally asks a refinement LLM for follow-up details, turns the answers into structured filters, and forwards those filters to the tabular dataset service. The conversation flow can run in the original direct mode or in the new repository-backed loop mode.

## Run

```bash
cp .env.example .env.dev
docker compose -f docker-compose.dev.yml up --build
```

Set `PIXIE_TABULAR_API_URL`, `PIXIE_TABULAR_COLLECTION` and `PIXIE_API_KEY` in your `.env.dev`
to let Pixie query the external tabular dataset (the defaults assume the dev compose stack).

## API

POST `/ask` with `{ "question": "Ik zoek een nieuwe laptop" }` to receive an answer (or a `no_results`/`error` response). The response JSON now always includes a `conversation_id` so clients can continue the dialogue. For follow-ups send:

```json
{
  "conversation_id": "<uuid-from-response>",
  "message": "Maximaal 1200 euro alsjeblieft"
}
```

Legacy clients can keep sending `pending_id`; Pixie will translate it internally.

Select the flow via `PIXIE_ACTIVE_FLOW` (`direct` by default, set to `loop` to enable the new repository-driven manager). The loop flow persists state in memory with a TTL defined by `PIXIE_CONVERSATION_TTL_MINUTES`.

## Docs

- [Conversation scenarios](docs/conversation-scenarios.md)

## TODO

- Populate the category/attribute metadata from the dataset instead of the inline placeholders.
