# Minimal Makefile with basic development helpers

.PHONY: up down dev-shell

up:
	docker compose -f docker-compose.dev.yml up --build -d

down:
	docker compose -f docker-compose.dev.yml down -v

dev-shell:
	# open an interactive shell in the dev image
	docker compose -f docker-compose.dev.yml run --rm dev bash
