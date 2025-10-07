"""Run two demo questions against Pixie using the configured Azure + tabular setup."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError as exc:  # pragma: no cover - sanity
    raise SystemExit(
        "python-dotenv is required for scripts/test_relevance.py. "
        "Install it with 'uv add python-dotenv' or 'pip install python-dotenv'."
    ) from exc

from pixie.core.conversation.pixie import Pixie


def load_env() -> None:
    env_file = Path(".env.dev")
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        raise SystemExit(
            ".env.dev not found; please create it before running the test script"
        )
    os.environ["PIXIE_TABULAR_API_URL"] = "http://localhost:8000"


def main() -> None:
    load_env()

    pixie = Pixie()

    questions = [
        "Ik zoek een gaming console met 4 hdmi poorten",
        "Ik zoek een nieuwe printer",
        "Wat is de weersverwachting in Brussel?",
    ]

    for question in questions:
        response = pixie.answer(question)
        print(f"Vraag: {question}")
        print(f"Antwoord: {response}")
        print("-" * 60)


if __name__ == "__main__":
    main()
