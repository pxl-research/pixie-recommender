from __future__ import annotations

import logging
from uuid import uuid4
from typing import Any

from pixie.core.contracts import AskResponse
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

    def __init__(self, pending_store: InMemoryPendingStore | None = None):
        self._pending_store = pending_store or InMemoryPendingStore()

    def answer(self, question: str) -> AskResponse:
        logger = logging.getLogger(__name__)
        logger.info("pixie.answer", extra={"question": question})

        key = question.strip().lower()

        # 2) Not relevant
        if key in ("i'm looking for my mom", "i am looking for my mom"):
            return AskResponse(
                type="not_relevant",
                text=(
                    "Sorry, I can't help with that. I only have information about"
                    " printers, laptops, smartphones, ..."
                ),
            )

        # 3) No results
        if key in (
            "i want a brother laser printer under €50",
            "i want a brother laser printer under 50 euros",
        ):
            return AskResponse(
                type="no_results",
                text=(
                    "Unfortunately, no printers match your criteria. Please try again with a "
                    "broader budget or contact support for assistance."
                ),
            )

        # 1 & 4) Start product discovery flow
        if key in ("i'm looking for a new printer", "i am looking for a new printer"):
            pending_id = f"pending-{uuid4().hex[:8]}"
            context: dict[str, Any] = {
                "flow": "product",
                "stage": "ask_budget",
                "filters": {},
            }
            self._pending_store.save_pending(
                pending_id, question, ttl_seconds=300, conversation_context=context
            )
            return AskResponse(
                type="ask_user",
                prompt=(
                    "What is your budget for a printer? Less than €150, between €150–€300,"
                    " more than €300, or no preference?"
                ),
                pending_id=pending_id,
            )

        return AskResponse(
            type="not_relevant",
            text=(
                "Question not recognized; use one of the example sentences:"
                " 'I'm looking for a new printer', 'I want a Brother laser printer under €50',"
                " or 'I'm looking for my mom'."
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
        if ctx.get("flow") != "product":
            self._pending_store.resolve_pending(pending_id)
            return AskResponse(type="error", reason="Unsupported pending flow")

        stage = ctx.get("stage")
        filters: dict[str, Any] = ctx.setdefault("filters", {})
        key = reply_text.strip().lower()

        # tiny fixed catalog
        catalog = [
            {
                "name": "Brother XC 2570",
                "brand": "Brother",
                "tech": "laser",
                "price": 199,
                "desc": "short description",
            },
            {
                "name": "Brother XT 3560",
                "brand": "Brother",
                "tech": "laser",
                "price": 159,
                "desc": "short description",
            },
            {
                "name": "Brother ZX 1570",
                "brand": "Brother",
                "tech": "inkjet",
                "price": 69,
                "desc": "short description",
            },
            {
                "name": "HP Inkjet 234",
                "brand": "HP",
                "tech": "inkjet",
                "price": 79,
                "desc": "short description",
            },
            {
                "name": "Kyocera T70",
                "brand": "Kyocera",
                "tech": "laser",
                "price": 99,
                "desc": "short description",
            },
            {
                "name": "HP Inkjet 1234",
                "brand": "HP",
                "tech": "inkjet",
                "price": 109,
                "desc": "short description",
            },
        ]

        # ask_budget
        if stage == "ask_budget":
            if "no preference" in key or key == "no preference":
                filters["max_price"] = None
            elif "maximum" in key or "€" in key or "eur" in key:
                import re

                m = re.search(r"(\d+)", key)
                if m:
                    filters["max_price"] = int(m.group(1))
                else:
                    filters["max_price"] = None
            else:
                filters["max_price"] = None

            ctx["stage"] = "ask_brand"
            self._pending_store.save_pending(
                pending_id,
                pending_entry.question,
                conversation_context=ctx,
            )
            return AskResponse(
                type="ask_user",
                prompt=(
                    "Which brand do you prefer? Brother, BenQ, HP, Kyocera, … or no preference?"
                ),
                pending_id=pending_id,
            )

        # ask_brand
        if stage == "ask_brand":
            if "no preference" in key or key == "no preference":
                filters["brand"] = None
            else:
                filters["brand"] = key.split()[0].capitalize()

            ctx["stage"] = "ask_tech"
            self._pending_store.save_pending(
                pending_id,
                pending_entry.question,
                conversation_context=ctx,
            )
            return AskResponse(
                type="ask_user",
                prompt=(
                    "Which printing technology? Inkjet, laser, thermal inkjet, or no preference?"
                ),
                pending_id=pending_id,
            )

        # ask_tech
        if stage == "ask_tech":
            if "no preference" in key or key == "no preference":
                filters["tech"] = None
            else:
                filters["tech"] = key.split()[0].lower()

            # apply filters
            results = []
            for p in catalog:
                if (
                    filters.get("brand")
                    and p["brand"].lower() != filters["brand"].lower()
                ):
                    continue
                tech_filter = filters.get("tech")
                if tech_filter and p["tech"].lower() != tech_filter.lower():
                    continue
                maxp = filters.get("max_price")
                if maxp and p["price"] > maxp:
                    continue
                results.append(p)

            THRESHOLD = 5
            if len(results) == 0:
                self._pending_store.resolve_pending(pending_id)
                return AskResponse(
                    type="no_results",
                    text=(
                        "Unfortunately, no printers match your criteria. Please try again with a broader"
                        " budget or contact support for assistance."
                    ),
                )

            if len(results) > THRESHOLD:
                ctx["stage"] = "choose_result_view"
                ctx["results"] = results
                ctx["total_count"] = len(results)
                self._pending_store.save_pending(
                    pending_id,
                    pending_entry.question,
                    conversation_context=ctx,
                )
                return AskResponse(
                    type="ask_user",
                    prompt=(
                        f"I found {len(results)} printers. Would you like to see the top 5 "
                        "sorted by price, or a random sample of 5?"
                    ),
                    pending_id=pending_id,
                )

            # return manageable list
            self._pending_store.resolve_pending(pending_id)
            lines = [
                f"{i+1}. {p['name']} – €{p['price']} – {p['desc']}"
                for i, p in enumerate(results)
            ]
            return AskResponse(
                type="answer", text="Here are matching printers:\n" + "\n".join(lines)
            )

        # choose_result_view
        if stage == "choose_result_view":
            results = ctx.get("results", [])
            if not results:
                self._pending_store.resolve_pending(pending_id)
                return AskResponse(type="error", reason="No results cached")

            if "sorted" in key:
                sorted_res = sorted(results, key=lambda r: r["price"])[:5]
                self._pending_store.resolve_pending(pending_id)
                lines = [
                    f"{i+1}. {p['name']} – €{p['price']} – {p['desc']}"
                    for i, p in enumerate(sorted_res)
                ]
                return AskResponse(
                    type="answer",
                    text="Here are the top 5 printers sorted by price:\n"
                    + "\n".join(lines),
                )

            if "random" in key or "sample" in key:
                sample = results[:5]
                self._pending_store.resolve_pending(pending_id)
                lines = [
                    f"{i+1}. {p['name']} – €{p['price']} – {p['desc']}"
                    for i, p in enumerate(sample)
                ]
                return AskResponse(
                    type="answer",
                    text="Here is a sample of 5 printers:\n" + "\n".join(lines),
                )

            self._pending_store.resolve_pending(pending_id)
            return AskResponse(type="error", reason="Unknown choice")

        # fallback
        self._pending_store.resolve_pending(pending_id)
        return AskResponse(type="error", reason="Unsupported conversation stage")
