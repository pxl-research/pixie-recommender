#!/usr/bin/env bash

set -euo pipefail

# Helper to run dev test workflows inside the repo's docker-compose dev environment.
# Usage:
#   ./scripts/dev_test.sh smoke   # runs run_in_container_tests.py smoke helper
#   ./scripts/dev_test.sh pytest  # runs pytest inside the api container
#   ./scripts/dev_test.sh all     # smoke then pytest

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
COMPOSE_FILE="$REPO_ROOT/docker-compose.dev.yml"
SERVICE=api

usage() {
  echo "Usage: $0 {smoke|pytest|all}" >&2
  exit 2
}

if [ ${#} -lt 1 ]; then
  usage
fi

cmd=$1
shift || true

# Ensure compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
  echo "docker-compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

start() {
  echo "Starting dev containers..."
  docker compose -f "$COMPOSE_FILE" up --build -d
}

stop() {
  echo "Tearing down dev containers..."
  docker compose -f "$COMPOSE_FILE" down -v
}

run_smoke() {
  echo "Running smoke helper inside container..."
  # Use docker compose exec to run a short python-based health probe inside the service
  echo "Polling internal HTTP /health inside service '$SERVICE' until ready..."
  HOST_PORT=${PORT_API:-8012}
  echo "Polling http://localhost:$HOST_PORT/health until ready..."
  tries=0
  max_tries=120
  until curl -fsS "http://localhost:$HOST_PORT/health" >/dev/null 2>&1; do
    tries=$((tries+1))
    if [ $tries -ge $max_tries ]; then
      echo "Service did not become ready after $max_tries attempts" >&2
      docker compose -f "$COMPOSE_FILE" logs --no-color --tail 200 "$SERVICE" || true
      exit 1
    fi
    sleep 1
  done
  docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE" /bin/bash -lc "python /app/scripts/run_in_container_tests.py"
}

run_pytest() {
  echo "Running pytest inside container... this may take a while"
  docker compose -f "$COMPOSE_FILE" exec "$SERVICE" /bin/bash -lc "uv run python -m pytest -q"
}

case "$cmd" in
  smoke)
    start
    run_smoke
    stop
    ;;
  pytest)
    start
    run_pytest
    stop
    ;;
  all)
    start
    run_smoke
    run_pytest
    stop
    ;;
  *)
    usage
    ;;
esac
