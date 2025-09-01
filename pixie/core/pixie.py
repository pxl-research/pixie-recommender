from __future__ import annotations

import logging

from pixie.core.contracts import AskResponse


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
                "summary": f"(mock) tabeldata voor: {question}"
            }
        elif "statistiek" in question.lower():
            return {
                "found_data": True,
                "table": "statistics_table",
                "rows": 15,
                "summary": f"(mock) statistieken voor: {question}"
            }
        else:
            return {
                "found_data": False,
                "reason": "Geen relevante tabeldata gevonden"
            }


class Orchestrator:
    """Central orchestrator that combines multiple RAG sources and makes decisions."""
    
    def __init__(self, rag_adapter: FakeRAGAdapter, tabular_rag: FakeTabularRAG):
        self._rag = rag_adapter
        self._tabular = tabular_rag
        
    def analyze_question(self, question: str) -> dict:
        """Analyze question and determine best response strategy."""
        # Get responses from both sources
        text_result = self._rag.answer(question)
        tabular_result = self._tabular.query(question)
        
        # Decision logic based on question content and available data
        confidence_score = self._calculate_confidence(question, tabular_result)
        
        return {
            "question": question,
            "text_result": text_result,
            "tabular_result": tabular_result,
            "confidence": confidence_score,
            "needs_clarification": confidence_score < 0.7,
            "strategy": self._determine_strategy(question, confidence_score, tabular_result)
        }
    
    def _calculate_confidence(self, question: str, tabular_result: dict) -> float:
        """Calculate confidence score based on question analysis."""
        confidence = 0.6  # higher baseline
        
        # Increase confidence if we have relevant tabular data
        if tabular_result.get("found_data"):
            confidence += 0.3
            
        # Decrease confidence for truly vague questions
        vague_indicators = ["algemeen", "meer info", "vertel eens", "wat meer"]
        if any(indicator in question.lower() for indicator in vague_indicators):
            confidence -= 0.3
            
        # Increase confidence for specific questions
        specific_indicators = [
            "cijfers", "data", "tabel", "statistiek", "wanneer", "waar", "hoofdstad", "naam"
        ]
        if any(indicator in question.lower() for indicator in specific_indicators):
            confidence += 0.2
            
        return max(0.0, min(1.0, confidence))  # clamp between 0 and 1
    
    def _determine_strategy(self, question: str, confidence: float, tabular_result: dict) -> str:
        """Determine the best response strategy."""
        if confidence < 0.7:
            return "ask_user"
        elif tabular_result.get("found_data"):
            return "answer_with_data"
        else:
            return "answer_text_only"


class Pixie:
    """Smart service that uses an orchestrator to decide response strategies."""

    def __init__(
        self, 
        rag_adapter: FakeRAGAdapter | None = None,
        tabular_rag: FakeTabularRAG | None = None
    ):
        self._rag = rag_adapter or FakeRAGAdapter()
        self._tabular = tabular_rag or FakeTabularRAG()
        self._orchestrator = Orchestrator(self._rag, self._tabular)

    def answer(self, question: str) -> AskResponse:
        """Use orchestrator to determine best response for the question."""
        logger = logging.getLogger(__name__)
        logger.info("pixie.answer", extra={"question": question})

        # Use orchestrator to analyze question
        analysis = self._orchestrator.analyze_question(question)
        
        if analysis["strategy"] == "ask_user":
            pending_id = "pending-1234"  # TODO: Generate unique ID in next step
            resp = AskResponse(
                type="ask_user",
                prompt="Kunt u wat meer specifieke informatie geven? "
                       "Dit helpt me een beter antwoord te formuleren.",
                pending_id=pending_id,
            )
        elif analysis["strategy"] == "answer_with_data":
            # Combine text and tabular results
            tabular_summary = analysis["tabular_result"]["summary"]
            text_result = analysis["text_result"]
            combined_text = f"{text_result} + {tabular_summary}"
            resp = AskResponse(type="answer", text=combined_text)
        else:  # answer_text_only
            resp = AskResponse(type="answer", text=analysis["text_result"])

        logger.info("pixie.answer", extra={
            "strategy": analysis["strategy"], 
            "confidence": analysis["confidence"]
        })
        return resp

    def reply(self, pending_id: str, reply_text: str) -> AskResponse:
        """Handle a follow-up reply to a pending ask and return a final answer."""
        logger = logging.getLogger(__name__)
        logger.info(
            "pixie.reply", extra={"pending_id": pending_id, "reply_text": reply_text}
        )

        text = f"(mock) received reply for {pending_id}: {reply_text}"
        resp = AskResponse(type="answer", text=text)

        return resp
