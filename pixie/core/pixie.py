from __future__ import annotations

import logging
from uuid import uuid4

from pixie.core.contracts import AskResponse
from pixie.core.pending_store import InMemoryPendingStore


class FakeRAGAdapter:
    """A fake RAG adapter that deterministically answers questions."""

    def answer(self, question: str) -> str:
        return f"(mock) antwoord op: {question}"


class FakeTabularRAG:
    """A fake tabular RAG that provides structured data responses."""

    def query(self, question: str) -> dict:
        """Return mock tabular data based on question."""
        if "cijfers" in question.lower() or "data" in question.lower():
            return {
                "found_data": True,
                "table": "mock_data_table",
                "rows": 42,
                "summary": f"(mock) tabeldata voor: {question}",
            }
        elif "statistiek" in question.lower():
            return {
                "found_data": True,
                "table": "statistics_table",
                "rows": 15,
                "summary": f"(mock) statistieken voor: {question}",
            }
        else:
            return {"found_data": False, "reason": "Geen relevante tabeldata gevonden"}


class Orchestrator:
    """Central orchestrator that simulates LLM decision-making for response strategies."""

    def __init__(self, rag_adapter: FakeRAGAdapter, tabular_rag: FakeTabularRAG):
        self._rag = rag_adapter
        self._tabular = tabular_rag

    def analyze_question(self, question: str) -> dict:
        """Simulate LLM analyzing question and deciding on response strategy."""
        # Get responses from both sources
        text_result = self._rag.answer(question)
        tabular_result = self._tabular.query(question)

        # Simulate LLM decision: "Should I ask for clarification or answer directly?"
        decision = self._simulate_llm_decision(question, tabular_result)

        return {
            "question": question,
            "text_result": text_result,
            "tabular_result": tabular_result,
            "strategy": decision,
        }

    def _simulate_llm_decision(self, question: str, tabular_result: dict) -> str:
        """Simulate how an LLM with ask_user MCP tool would decide."""
        
        # Pattern 1: Very vague questions -> LLM would use ask_user tool
        vague_patterns = [
            "algemeen", "meer info", "vertel eens", "wat meer", 
            "help", "uitleg", "informatie", "details"
        ]
        if any(pattern in question.lower() for pattern in vague_patterns):
            # LLM thinks: "This is too vague, I need clarification"
            return "ask_user"
        
        # Pattern 2: Complex multi-part questions -> LLM might ask for focus
        if "?" in question and len(question.split("?")) > 2:
            # LLM thinks: "Multiple questions, let me ask what's most important"
            return "ask_user"
            
        # Pattern 3: Has specific data available -> LLM answers with data
        if tabular_result.get("found_data"):
            # LLM thinks: "I have relevant data, I can answer this"
            return "answer_with_data"
            
        # Pattern 4: Specific, answerable questions -> LLM gives direct answer
        specific_patterns = [
            "hoofdstad", "naam", "wanneer", "waar", "wie", "wat is", 
            "hoeveel", "welke", "hoe"
        ]
        if any(pattern in question.lower() for pattern in specific_patterns):
            # LLM thinks: "This is specific enough, I can answer"
            return "answer_text_only"
            
        # Default: When uncertain, LLM tends to ask for clarification
        # This simulates cautious LLM behavior
        return "ask_user"


class Pixie:
    """Smart service that uses an orchestrator to decide response strategies."""

    def __init__(
        self,
        rag_adapter: FakeRAGAdapter | None = None,
        tabular_rag: FakeTabularRAG | None = None,
        pending_store: InMemoryPendingStore | None = None,
    ):
        self._rag = rag_adapter or FakeRAGAdapter()
        self._tabular = tabular_rag or FakeTabularRAG()
        self._orchestrator = Orchestrator(self._rag, self._tabular)
        self._pending_store = pending_store or InMemoryPendingStore()

    def answer(self, question: str) -> AskResponse:
        """Use orchestrator to determine best response for the question."""
        logger = logging.getLogger(__name__)
        logger.info("pixie.answer", extra={"question": question})

        # Use orchestrator to analyze question (simulates LLM decision-making)
        analysis = self._orchestrator.analyze_question(question)

        if analysis["strategy"] == "ask_user":
            # LLM decided to use ask_user tool - generate pending_id and store context
            pending_id = f"pending-{uuid4().hex[:8]}"
            self._pending_store.save_pending(pending_id, question, ttl_seconds=300)

            resp = AskResponse(
                type="ask_user",
                prompt="Kunt u wat meer specifieke informatie geven? "
                "Dit helpt me een beter antwoord te formuleren.",
                pending_id=pending_id,
            )
        elif analysis["strategy"] == "answer_with_data":
            # LLM decided to answer using available tabular data
            tabular_summary = analysis["tabular_result"]["summary"]
            text_result = analysis["text_result"]
            combined_text = f"{text_result} + {tabular_summary}"
            resp = AskResponse(type="answer", text=combined_text)
        else:  # answer_text_only
            # LLM decided to give direct text answer
            resp = AskResponse(type="answer", text=analysis["text_result"])

        logger.info(
            "pixie.answer",
            extra={"strategy": analysis["strategy"]},
        )
        return resp

    def reply(self, pending_id: str, reply_text: str) -> AskResponse:
        """Handle a follow-up reply to a pending ask and return a final answer."""
        logger = logging.getLogger(__name__)
        logger.info(
            "pixie.reply", extra={"pending_id": pending_id, "reply_text": reply_text}
        )

        # Validate pending_id and get original question context
        pending_entry = self._pending_store.get_pending(pending_id)
        if not pending_entry:
            return AskResponse(
                type="error", reason=f"Ongeldig of verlopen pending_id: {pending_id}"
            )

        # Resolve the pending entry (removes it from store)
        self._pending_store.resolve_pending(pending_id)

        # Generate answer based on original question + reply context
        original_question = pending_entry.question
        combined_context = f"{original_question} (aanvullende info: {reply_text})"

        # Use orchestrator again with enriched context (simulates LLM with more info)
        analysis = self._orchestrator.analyze_question(combined_context)

        # With additional context, LLM should typically be able to answer
        if analysis["strategy"] == "answer_with_data":
            tabular_summary = analysis["tabular_result"]["summary"]
            text_result = analysis["text_result"]
            combined_text = f"{text_result} + {tabular_summary}"
        else:
            combined_text = analysis["text_result"]

        resp = AskResponse(type="answer", text=combined_text)
        return resp
