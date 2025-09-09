
# Contributing

We want contributions to be easy and consistent. Below are a few small, optional steps you can use locally to keep code formatted and linted before committing.

Recommended developer commands (one-time setup):

1. Create a virtual environment and install dev tools:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

1. Optional: install pre-commit hooks (recommended but opt-in):

```bash
# install pre-commit once
pip install pre-commit
pre-commit install
# run all hooks against the repo once
pre-commit run --all-files
```

Useful commands:

```bash
# format with Black
python -m black .
# lint with Ruff
python -m ruff check .
# run tests
python -m pytest -q
```

Notes

- The pre-commit hooks are optional — if you prefer not to install them, just run the commands above before committing.
- CI already runs `black --check`, `ruff check` and `pytest` on PRs against `main`.
