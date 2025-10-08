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

        if response.type == "ask_user" and response.pending_id:
            follow_up = _craft_follow_up(response.prompt)
            follow_response = pixie.reply(response.pending_id, follow_up)
            print(f"→ Follow-up: {follow_up}")
            print(f"→ Reactie: {follow_response}")

        print("-" * 60)


def _craft_follow_up(prompt: str | None) -> str:
    prompt = (prompt or "").lower()
    if "prijs" in prompt or "budget" in prompt:
        return "Mijn budget is ongeveer 250 euro."
    if "merk" in prompt:
        return "Ik geef de voorkeur aan het merk HP."
    if "beschikbaarheid" in prompt:
        return "Ik heb het product graag op voorraad."
    return "Ik weet het nog niet precies."


if __name__ == "__main__":
    main()
