# Run tests in Docker dev container

Reminder for developer (assistant):

- Use the `dev` service from `docker-compose.dev.yml` to run tests; the dev image provides the correct Python environment and pytest.
- Typical workflow:

```bash
# build and start the dev container (one-time)
docker compose -f docker-compose.dev.yml build dev
# open an interactive shell in the dev container
docker compose -f docker-compose.dev.yml run --rm dev
# inside the container, run tests
pytest -q
# or run a single test file
pytest -q tests/test_real_search_engine.py
```

- If tests still fail because pytest is missing, check `infra/docker/Dockerfile.dev` and ensure `pytest` is included via `pyproject.toml` (as a dev dependency) so `uv sync` installs it into the dev image; then rebuild the dev image.
- Do not forget to mount the repo (volume) to allow hot-reload and test changes.

This note is for the local agent to avoid trying to run pytest directly on the host without the container.
