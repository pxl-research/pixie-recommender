from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from pixie.core.contracts import AskResponse
from pixie.core.conversation_loop import ConversationLoopManager
from pixie.core import azure_llm_set
from pixie.core.pending_store import InMemoryPendingStore


class Pixie:
    """Minimal hardcoded product discovery mock implementing 4 example flows.

    Supported literal starting sentences (English):
      - "I'm looking for a new printer"  -> product discovery multi-turn
      - "I want a Brother laser printer under €50" -> no results
      - "I'm looking for my mom" -> not relevant

    The product discovery flow implements stages saved in the pending store:
      ask_budget -> ask_brand -> ask_tech -> (results or choose_result_view)
    """

    def __init__(
        self,
        pending_store: InMemoryPendingStore | None = None,
        conversation_manager: ConversationLoopManager | None = None,
    ):
        self._pending_store = pending_store or InMemoryPendingStore()
        # If no conversation_manager was provided, attempt to create one using
        # the Azure LLM factory. This keeps existing behavior when a manager
        # (usually from tests) is injected.
        if conversation_manager is not None:
            self._conversation_manager = conversation_manager
        else:
            try:
                relevance, sql, refinement = azure_llm_set.create_azure_llm_set()
                # Provide a default search function that will be used by the
                # ConversationLoopManager. Import lazily to avoid cycles.
                from pixie.core.search_engine import RealSearchEngine

                engine = RealSearchEngine()
                self._conversation_manager = ConversationLoopManager(
                    relevance, sql, refinement, engine.search, pending_store=self._pending_store
                )
            except Exception as e:
                # If Azure isn't configured (e.g., in local test runs), leave
                # the conversation manager unset so existing fallback flows
                # remain functional. Log the reason.
                logging.getLogger(__name__).warning(
                    "Could not initialize Azure LLMs for ConversationLoopManager: %s",
                    e,
                )
                self._conversation_manager = None

    def answer(self, question: str) -> AskResponse:
        logger = logging.getLogger(__name__)
        logger.info("pixie.answer", extra={"question": question})

        key = question.strip().lower()
        # Exact Dutch literal flows only
        if key == "ik zoek mijn mama":
            return AskResponse(
                type="not_relevant",
                text=(
                    "Sorry, daar kan ik je niet bij helpen. "
                    "Ik heb enkel informatie over printers, laptops, smartphones, ..."
                ),
            )

        if key == "ik wil graag meer informatie over een brother laserprinter":
            pending_id = f"pending-{uuid4().hex[:8]}"
            context: dict[str, Any] = {"flow": "brother_laser", "stage": "ask_budget"}
            self._pending_store.save_pending(
                pending_id, question, ttl_seconds=300, conversation_context=context
            )
            return AskResponse(
                type="ask_user",
                prompt=(
                    "Wat is uw budget voor een Brother laserprinter? "
                    "Minder dan 150€, tussen 150€ en 300€, meer dan 300€ of maakt het niet uit?"
                ),
                pending_id=pending_id,
            )

        if key == "ik zoek een nieuwe printer":
            # delegate to conversation manager when available
            if self._conversation_manager:
                return self._conversation_manager.handle_new_question(question)
            pending_id = f"pending-{uuid4().hex[:8]}"
            context: dict[str, Any] = {
                "flow": "product",
                "stage": "ask_budget",
            }
            self._pending_store.save_pending(
                pending_id,
                question,
                ttl_seconds=300,
                conversation_context=context,
            )
            return AskResponse(
                type="ask_user",
                prompt=(
                    "Wat is uw budget voor een printer? "
                    "Minder dan 150€, tussen 150€ en 300€, meer dan 300€ of maakt het niet uit?"
                ),
                pending_id=pending_id,
            )

        # fallback for any other literal input
        return AskResponse(
            type="not_relevant",
            text=(
                "Vraag niet herkend; gebruik letterlijk één van de voorbeeldzinnen zoals:\n"
                "'Ik zoek een nieuwe printer',\n"
                "'Ik wil graag meer informatie over een Brother laserprinter',\n"
                "of 'Ik zoek mijn mama'."
            ),
        )

    def reply(self, pending_id: str, reply_text: str) -> AskResponse:
        logger = logging.getLogger(__name__)
        logger.info(
            "pixie.reply", extra={"pending_id": pending_id, "reply_text": reply_text}
        )

        pending_entry = self._pending_store.get_pending(pending_id)
        if not pending_entry:
            return AskResponse(type="error", reason="Invalid or expired pending_id")

        ctx = pending_entry.conversation_context or {}
        flow = ctx.get("flow")
        stage = ctx.get("stage")
        key = reply_text.strip().lower()

        # Flow: brother_laser (specialized)
        if flow == "brother_laser":
            if stage == "ask_budget":
                # user literal: Minder dan 50€ -> no results
                if (
                    key == "minder dan 50€"
                    or key == "minder dan 50"
                    or key == "minder dan 50eur"
                ):
                    self._pending_store.resolve_pending(pending_id)
                    return AskResponse(
                        type="no_results",
                        text=(
                            "Ik heb helaas geen printers gevonden die voldoen aan uw criteria. "
                            "Probeer het misschien opnieuw met wat ruimere criteria of "
                            "contacteer een van onze medewerkers voor meer informatie."
                        ),
                    )
                # any other reply -> ask brand (follow the minimal literal flow)
                ctx["stage"] = "ask_brand"
                self._pending_store.save_pending(
                    pending_id, pending_entry.question, conversation_context=ctx
                )
                return AskResponse(
                    type="ask_user",
                    prompt=(
                        "Welk merk van printer had u in gedachte? "
                        "U kan kiezen uit Brother, Benq, HP, Kyocera, ... of weet u het nog niet?"
                    ),
                    pending_id=pending_id,
                )

        # Flow: product (general product discovery)
        if flow == "product":
            # stage: ask_budget
            if stage == "ask_budget":
                # record budget literally but we only need to check a few exact phrases
                ctx["stage"] = "ask_brand"
                self._pending_store.save_pending(
                    pending_id, pending_entry.question, conversation_context=ctx
                )
                return AskResponse(
                    type="ask_user",
                    prompt=(
                        "Welk merk van printer had u in gedachte? "
                        "U kan kiezen uit Brother, Benq, HP, Kyocera, ... of weet u het nog niet?"
                    ),
                    pending_id=pending_id,
                )

            # stage: ask_brand
            if stage == "ask_brand":
                ctx["stage"] = "ask_tech"
                self._pending_store.save_pending(
                    pending_id, pending_entry.question, conversation_context=ctx
                )
                return AskResponse(
                    type="ask_user",
                    prompt=(
                        "Welke printtechnologie had u in gedachte? "
                        "U kan kiezen uit inkjet, laser, thermal inkjet of weet u het nog niet?"
                    ),
                    pending_id=pending_id,
                )

            # stage: ask_tech
            if stage == "ask_tech":
                # If user answered "weet ik niet" for all stages we simulate many results
                if key == "weet ik niet":
                    ctx["stage"] = "choose_result_view"
                    ctx["total_count"] = 152
                    self._pending_store.save_pending(
                        pending_id, pending_entry.question, conversation_context=ctx
                    )
                    return AskResponse(
                        type="ask_user",
                        prompt=(
                            "Ik heb 152 verschillende printers gevonden. "
                            "Wilt u graag de top 5 zien gesorteerd op prijs of dat ik er 5 "
                            "willekeurig selecteer?"
                        ),
                        pending_id=pending_id,
                    )

                # If user gives a concrete technology like "laser", return two Brother results
                if key == "laser":
                    self._pending_store.resolve_pending(pending_id)
                    return AskResponse(
                        type="answer",
                        text=(
                            "Ik heb volgende printers voor u gevonden\n"
                            "1. Brother XC 2570\n"
                            "Prijs: 199€\n"
                            "Beschrijving: ....\n"
                            "2. Brother XT 3560\n"
                            "Prijs: 159€\n"
                            "Beschrijving: ..."
                        ),
                    )

                # any other literal -> no results
                self._pending_store.resolve_pending(pending_id)
                return AskResponse(
                    type="no_results",
                    text=(
                        "Ik heb helaas geen printers gevonden die voldoen aan uw criteria. "
                        "Probeer het misschien opnieuw met wat ruimere criteria of contacteer een "
                        "van onze medewerkers voor meer informatie."
                    ),
                )

            # stage: choose_result_view
            if stage == "choose_result_view":
                # expect literal 'gesorteerd op prijs' or 'willekeurig'
                if key == "gesorteerd op prijs":
                    self._pending_store.resolve_pending(pending_id)
                    return AskResponse(
                        type="answer",
                        text=(
                            "Ik heb volgende printers voor u gevonden\n"
                            "1. Brother ZX 1570\n"
                            "Prijs: 69€\n"
                            "Beschrijving: ....\n"
                            "2. HP inkjet 234\n"
                            "Prijs: 79€\n"
                            "Beschrijving: ...\n"
                            "3. Kyocera T70\n"
                            "Prijs: 99€\n"
                            "Beschrijving: ....\n"
                            "4. Brother XT 3560\n"
                            "Prijs: 99€\n"
                            "Beschrijving: ...\n"
                            "5. HP inkjet 1234\n"
                            "Prijs: 109€\n"
                            "Beschrijving: ...."
                        ),
                    )

                if key == "willekeurig" or key == "willekeurig selecteer":
                    self._pending_store.resolve_pending(pending_id)
                    return AskResponse(
                        type="answer",
                        text=("Hier is een willekeurige selectie van 5 printers."),
                    )

                self._pending_store.resolve_pending(pending_id)
                return AskResponse(type="error", reason="Onbekende keuze")

        # unsupported flow
        self._pending_store.resolve_pending(pending_id)
        return AskResponse(type="error", reason="Unsupported pending flow")
