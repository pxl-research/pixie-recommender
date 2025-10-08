"""Single-pass conversation handler that relies on the LLMs to produce SQL."""

import logging
from uuid import uuid4
from typing import Any, Dict

from ..llms.azure_refinement_llm import AzureRefinementLLM
from ..utils.contracts import AskResponse
from .llm_orchestrator import LLMOrchestrator

logger = logging.getLogger(__name__)


class DirectConversationManager:
    """Minimal conversation layer that delegates everything to the LLM stack."""

    def __init__(
        self,
        search_fn,
        llm_orchestrator: LLMOrchestrator,
        refinement_llm: AzureRefinementLLM,
    ) -> None:
        self.search_fn = search_fn
        self.llm_orchestrator = llm_orchestrator
        self.refinement_llm = refinement_llm
        self._pending_questions: dict[str, dict[str, Any]] = {}

    def handle_new_question(self, question: str) -> AskResponse:
        """Classify relevance, detect category, generate SQL, and run the search stub."""
        logger.info("question", extra={"question": question})
        relevance = self.llm_orchestrator.check_relevance_and_category(question)
        if not relevance.success:
            return AskResponse(type="error", reason="llm_failure")
        if not relevance.result["relevant"]:
            return AskResponse(type="not_relevant", text="Not relevant")

        category = relevance.result["category"]
        if not category:
            return AskResponse(type="error", reason="missing_category")
        sql_result = self.llm_orchestrator.generate_search_query(question, {}, category)
        if not sql_result.success:
            return AskResponse(type="error", reason="search_failed")

        sql_query = sql_result.result.get("sql") if sql_result.result else None
        if not sql_query:
            return AskResponse(type="error", reason="search_failed")

        try:
            results = self.search_fn(sql_query, {"category": category})
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("search_failed", exc_info=exc)
            return AskResponse(type="error", reason="search_failed")
        items, metadata = self._normalise_results(results, category)
        total = metadata.get("count")
        if not isinstance(total, int):
            total = len(items)

        if total > 3:
            prompt = self._build_refinement_prompt(category, metadata, total)
            pending_id = str(uuid4())
            self._pending_questions[pending_id] = {
                "category": category,
                "metadata": metadata,
                "sql": sql_query,
            }
            return AskResponse(type="ask_user", prompt=prompt, pending_id=pending_id)

        if items:
            return AskResponse(
                type="answer", text=self._format_results(items, metadata)
            )
        return AskResponse(type="no_results", text="Geen producten gevonden")

    def handle_reply(self, pending_id: str, reply: str) -> AskResponse:
        """Minimal acknowledgement of refinement answers."""
        logger.info("reply", extra={"pending_id": pending_id, "reply": reply})
        context = self._pending_questions.pop(pending_id, None)
        if context is None:
            return AskResponse(type="error", reason="unknown_pending_id")
        return AskResponse(
            type="answer",
            text="Bedankt voor je extra informatie! Ik ga hiermee verder aan de slag.",
        )

    def _normalise_results(
        self, payload: Any, category: str
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if isinstance(payload, dict):
            metadata = {k: v for k, v in payload.items() if k != "results"}
            items = payload.get("results") or []
        else:
            metadata = {"category": category}
            items = payload or []
        # Defensive: make sure we only pass dicts further down.
        items = [item for item in items if isinstance(item, dict)]
        return items, metadata

    def _format_results(
        self, items: list[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> str:
        header = metadata.get("product_name") or metadata.get("category") or "producten"
        preferred_columns = metadata.get("preferred_columns") or []
        lines = [f"Resultaten voor {header}:"]

        for item in items[:3]:  # keep responses compact
            columns_to_show: list[tuple[str, Any]] = []
            for column in preferred_columns:
                value = item.get(column)
                if value in (None, ""):
                    continue
                columns_to_show.append((column, value))
                if len(columns_to_show) == 3:
                    break

            if not columns_to_show:
                for key, value in item.items():
                    if key in {"id", "created_at", "updated_at", "product_name"}:
                        continue
                    if value in (None, ""):
                        continue
                    columns_to_show.append((key, value))
                    if len(columns_to_show) == 3:
                        break

            if not columns_to_show:
                lines.append("- (geen details)")
                continue

            formatted = []
            for column, value in columns_to_show:
                label = column.replace("_", " ")
                if isinstance(value, (int, float)):
                    formatted.append(f"{label}: {value}")
                else:
                    formatted.append(f"{label}: {value}")

            lines.append(f"- {' | '.join(formatted)}")

        total = metadata.get("total")
        if isinstance(total, int):
            lines.append(f"Totaal gevonden: {total}")
        return "\n".join(lines)

    def _build_refinement_prompt(
        self, category: str, metadata: Dict[str, Any], count: int
    ) -> str:
        product_name = metadata.get("product_name") or category or "producten"
        attribute_info = metadata.get("refine_attribute") or {}
        if isinstance(attribute_info, dict):
            attribute_data = dict(attribute_info)
        else:
            attribute_data = {}

        options_labels: list[str] = []
        attr_type = attribute_data.get("type")
        q1 = attribute_data.get("q1")
        q3 = attribute_data.get("q3")
        attr_name = attribute_data.get("name")
        label = (attr_name or "het product").replace("_", " ")
        unit = "€" if attr_name and "prijs" in attr_name.lower() else ""

        options_labels: list[str] = []
        options_plain: list[str] = []

        if (
            attr_type in {"continuous", "numeric"}
            and isinstance(q1, (int, float))
            and isinstance(q3, (int, float))
            and q1 < q3
        ):
            low = self._friendly_round(q1)
            high = self._friendly_round(q3)
            formatted_low = self._format_numeric_value(low)
            formatted_high = self._format_numeric_value(high)
            options_labels = [
                f"minder dan {unit}{formatted_low}".strip(),
                f"tussen {unit}{formatted_low} en {unit}{formatted_high}".strip(),
                f"meer dan {unit}{formatted_high}".strip(),
            ]
            options_plain = options_labels + ["weet ik niet"]
            attribute_data["options"] = options_plain

        context = {
            "category": product_name,
            "attribute": attribute_data,
        }
        question = None
        try:
            question = self.refinement_llm.generate_question(context)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("refinement_failed", exc_info=exc)
            question = None

        attr_name = attribute_data.get("name")
        label = (attr_name or "het product").replace("_", " ")

        if not question:
            if options_labels:
                question = (
                    f"Ik heb {count} resultaten voor {product_name}. "
                    "Kies een optie of geef je eigen antwoord."
                )
            else:
                question = (
                    f"Ik heb {count} resultaten voor {product_name}. "
                    f"Welk detail over {label} is voor jou het belangrijkst?"
                )

        if options_labels:
            display_options = options_labels + ["'weet ik niet'"]
            options_line = ", ".join(display_options)
            return f"{question}\nAntwoordopties: {options_line}"

        return question

    @staticmethod
    def _friendly_round(value: float) -> float:
        abs_val = abs(value)
        if abs_val >= 1000:
            rounded = round(value / 50) * 50
        elif abs_val >= 100:
            rounded = round(value / 10) * 10
        elif abs_val >= 10:
            rounded = round(value)
        elif abs_val >= 1:
            rounded = round(value)
        else:
            rounded = round(value, 1)
        if abs(rounded - int(rounded)) < 0.01:
            return float(int(rounded))
        return float(rounded)

    @staticmethod
    def _format_numeric_value(value: float) -> str:
        if abs(value - int(value)) < 0.01:
            return str(int(value))
        text = f"{value:.1f}".rstrip("0").rstrip(".")
        return text
