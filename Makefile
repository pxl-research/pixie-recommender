# Minimal Makefile with developer test helpers

.PHONY: dev-test-smoke dev-test-pytest dev-test-all

dev-test-smoke:
	./scripts/dev_test.sh smoke

dev-test-pytest:
	./scripts/dev_test.sh pytest

dev-test-all:
	./scripts/dev_test.sh all
