# Minimal Makefile with developer test helpers

.PHONY: dev-test-smoke dev-test-pytest dev-test-all

dev-test-smoke:
	./scripts/dev_test.sh smoke

dev-test-pytest:
	./scripts/dev_test.sh pytest

dev-test-all:
	./scripts/dev_test.sh all

.PHONY: up down dev-shell dev-test

up:
	docker compose -f docker-compose.dev.yml up --build -d

down:
	docker compose -f docker-compose.dev.yml down -v

dev-shell:
	# open an interactive shell in the dev image
	docker compose -f docker-compose.dev.yml run --rm dev bash

dev-test:
	# run canonical dev/test script (single-source of truth)
	./scripts/dev_test.sh pytest
