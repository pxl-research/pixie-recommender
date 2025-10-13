"""Run two demo questions against Pixie using the configured Azure + tabular setup."""

from __future__ import annotations

import json
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
from pixie.core.utils.tabular_api import TabularAPIClient


def _instrument_tabular_calls() -> None:
    """Print each backend call performed by the tabular client."""

    if getattr(TabularAPIClient, "_test_relevance_wrapped", False):
        return

    original_request = TabularAPIClient._request

    def wrapped_request(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
    ):
        try:
            payload_repr = json.dumps(payload, ensure_ascii=False)
        except (TypeError, ValueError):
            payload_repr = repr(payload)
        full_url = f"{self.base_url}{path}"
        print(f"[TABULAR] {method} {full_url} payload={payload_repr}")
        return original_request(self, method, path, payload)

    TabularAPIClient._request = wrapped_request  # type: ignore[assignment]
    setattr(TabularAPIClient, "_test_relevance_wrapped", True)


def load_env() -> None:
    env_file = Path(".env.dev")
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        raise SystemExit(
            ".env.dev not found; please create it before running the test script"
        )
    os.environ["PIXIE_TABULAR_API_URL"] = "http://localhost:8000"
    os.environ.setdefault("PIXIE_CONVERSATION_TTL_MINUTES", "15")
    os.environ.setdefault("PIXIE_RESULT_THRESHOLD", "3")
    os.environ.setdefault("PIXIE_MAX_REFINE_QUESTIONS", "2")


def main() -> None:
    load_env()

    _instrument_tabular_calls()
    pixie = Pixie()

    questions = [
        "Ik zoek een gaming console met 4 hdmi poorten",
        "Ik zoek een nieuwe printer",
        "Wat is de weersverwachting in Brussel?",
    ]

    for question in questions:
        print(f"Vraag: {question}")
        response = pixie.answer(question)
        print(f"Antwoord: {response}")

        turn = 0
        conversation_id = response.conversation_id
        while response.type == "ask_user" and conversation_id:
            follow_up = _craft_follow_up(response.prompt)
            turn += 1
            print(f"→ Follow-up {turn}: {follow_up}")
            response = pixie.reply(conversation_id, follow_up)
            print(f"→ Reactie: {response}")
            if turn >= 5:
                print("→ Conversatie gestopt na 5 reacties zonder definitief antwoord")
                break
            conversation_id = response.conversation_id or conversation_id

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
