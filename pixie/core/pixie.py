from __future__ import annotations

import logging
from uuid import uuid4

from pixie.core.contracts import AskResponse, Product
from pixie.core.conversation_state import ConversationState, ConversationStateManager
from pixie.core.domain_validator import DomainValidator
from pixie.core.fake_catalog import FakeProductCatalog
from pixie.core.pending_store import InMemoryPendingStore
from pixie.core.product_questions import ProductQuestionGenerator
from pixie.core.result_manager import ResultManager


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

    def __init__(
        self, 
        rag_adapter: FakeRAGAdapter, 
        tabular_rag: FakeTabularRAG,
        product_catalog: FakeProductCatalog | None = None,
        domain_validator: DomainValidator | None = None,
        result_manager: ResultManager | None = None
    ):
        self._rag = rag_adapter
        self._tabular = tabular_rag
        self._product_catalog = product_catalog or FakeProductCatalog()
        self._domain_validator = domain_validator or DomainValidator()
        self._result_manager = result_manager or ResultManager()

    def analyze_question(self, question: str, conversation_context: dict | None = None) -> dict:
        """Simulate LLM analyzing question and deciding on response strategy."""
        # Check if this is a product-related question first
        if self._domain_validator.is_product_related(question):
            return self._analyze_product_question(question, conversation_context or {})
        
        # Original non-product logic
        text_result = self._rag.answer(question)
        tabular_result = self._tabular.query(question)
        decision = self._simulate_llm_decision(question, tabular_result)

        return {
            "question": question,
            "text_result": text_result,
            "tabular_result": tabular_result,
            "strategy": decision,
        }

    def _analyze_product_question(self, question: str, context: dict) -> dict:
        """Analyze product-related questions with domain validation."""
        # Check if question is in supported domains
        category = self._domain_validator.detect_product_category(question)
        
        if category is None:
            # Out of scope question
            return {
                "question": question,
                "strategy": "not_relevant",
                "supported_domains": self._domain_validator.get_supported_domains(),
                "text_result": self._domain_validator.generate_rejection_message()
            }
        
        if category == "unknown_product":
            # Product-related but unclear category
            return {
                "question": question,
                "strategy": "ask_user",
                "text_result": self._domain_validator.generate_category_clarification_message(),
                "detected_category": None
            }

        # Valid product category detected
        return self._analyze_product_search(question, category, context)

    def _analyze_product_search(self, question: str, category: str, context: dict) -> dict:
        """Analyze product search with current context."""
        applied_filters = context.get("applied_filters", {})
        
        # Add detected category to filters
        search_filters = applied_filters.copy()
        search_filters["category"] = category
        
        # Search products with current filters
        products = self._product_catalog.search_products(search_filters)
        
        # Analyze results and decide strategy
        if self._result_manager.is_empty_result(products):
            return {
                "question": question,
                "strategy": "no_results",
                "text_result": self._result_manager.generate_empty_result_message(search_filters),
                "alternatives": self._result_manager.generate_alternatives_suggestion(search_filters),
                "detected_category": category
            }
        
        elif self._result_manager.is_too_many_results(products):
            return {
                "question": question,
                "strategy": "ask_user_refinement",
                "text_result": self._result_manager.generate_too_many_results_message(len(products)),
                "product_count": len(products),
                "detected_category": category,
                "refinement_options": self._result_manager.handle_refinement_options(products)
            }
        
        else:
            # Good number of results - return product list
            return {
                "question": question,
                "strategy": "product_list",
                "products": products,
                "text_result": f"Here are {len(products)} matching products:",
                "detected_category": category
            }

    def _simulate_llm_decision(self, question: str, tabular_result: dict) -> str:
        """Simulate how an LLM with ask_user MCP tool would decide."""

        # Pattern 1: Very vague questions -> LLM would use ask_user tool
        vague_patterns = [
            "algemeen",
            "meer info",
            "vertel eens",
            "wat meer",
            "help",
            "uitleg",
            "informatie",
            "details",
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
            "hoofdstad",
            "naam",
            "wanneer",
            "waar",
            "wie",
            "wat is",
            "hoeveel",
            "welke",
            "hoe",
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
        product_catalog: FakeProductCatalog | None = None,
    ):
        self._rag = rag_adapter or FakeRAGAdapter()
        self._tabular = tabular_rag or FakeTabularRAG()
        self._product_catalog = product_catalog or FakeProductCatalog()
        self._orchestrator = Orchestrator(
            self._rag, 
            self._tabular, 
            self._product_catalog
        )
        self._pending_store = pending_store or InMemoryPendingStore()
        self._conversation_manager = ConversationStateManager()
        self._question_generator = ProductQuestionGenerator()

    def answer(self, question: str) -> AskResponse:
        """Use orchestrator to determine best response for the question."""
        logger = logging.getLogger(__name__)
        logger.info("pixie.answer", extra={"question": question})

        # Use orchestrator to analyze question (simulates LLM decision-making)
        analysis = self._orchestrator.analyze_question(question)
        strategy = analysis["strategy"]

        if strategy == "not_relevant":
            # Out of scope question
            resp = AskResponse(
                type="not_relevant",
                text=analysis["text_result"],
                supported_domains=analysis["supported_domains"]
            )
        
        elif strategy == "no_results":
            # Empty product search results
            resp = AskResponse(
                type="no_results",
                text=analysis["text_result"]
            )
        
        elif strategy == "product_list":
            # Return product list
            resp = AskResponse(
                type="product_list",
                text=analysis["text_result"],
                products=analysis["products"]
            )
            
        elif strategy == "ask_user_refinement":
            # Too many results, need refinement
            pending_id = f"pending-{uuid4().hex[:8]}"
            
            # Create conversation state for progressive refinement
            self._conversation_manager.create_state(
                pending_id,
                question,
                analysis.get("detected_category")
            )
            
            # Store in pending store with conversation context
            conversation_context = {
                "type": "product_refinement",
                "detected_category": analysis.get("detected_category"),
                "product_count": analysis.get("product_count"),
                "refinement_options": analysis.get("refinement_options")
            }
            
            self._pending_store.save_pending(
                pending_id, 
                question, 
                ttl_seconds=300,
                conversation_context=conversation_context
            )

            # Generate next refinement question
            next_question = self._question_generator.get_next_question(
                analysis.get("detected_category", "unknown")
            )
            
            resp = AskResponse(
                type="ask_user",
                prompt=next_question or analysis["text_result"],
                pending_id=pending_id,
                refinement_context=conversation_context
            )
            
        elif strategy == "ask_user":
            # Original ask_user flow or product category clarification
            pending_id = f"pending-{uuid4().hex[:8]}"
            
            conversation_context = None
            if analysis.get("detected_category") is not None:
                # Product-related question needing clarification
                self._conversation_manager.create_state(
                    pending_id,
                    question,
                    analysis.get("detected_category")
                )
                conversation_context = {
                    "type": "product_category_clarification",
                    "detected_category": analysis.get("detected_category")
                }
            
            self._pending_store.save_pending(
                pending_id, 
                question, 
                ttl_seconds=300,
                conversation_context=conversation_context
            )

            resp = AskResponse(
                type="ask_user",
                prompt=analysis.get("text_result", 
                    "Kunt u wat meer specifieke informatie geven? "
                    "Dit helpt me een beter antwoord te formuleren."
                ),
                pending_id=pending_id,
            )
            
        elif strategy == "answer_with_data":
            # Original data-based answer
            tabular_summary = analysis["tabular_result"]["summary"]
            text_result = analysis["text_result"]
            combined_text = f"{text_result} + {tabular_summary}"
            resp = AskResponse(type="answer", text=combined_text)
            
        else:  # answer_text_only
            # Original direct text answer
            resp = AskResponse(type="answer", text=analysis["text_result"])

        logger.info(
            "pixie.answer",
            extra={"strategy": strategy},
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

        # Check if this is a product refinement conversation
        conversation_context = pending_entry.conversation_context or {}
        
        if conversation_context.get("type") == "product_refinement":
            return self._handle_product_refinement_reply(pending_id, reply_text, pending_entry)
        elif conversation_context.get("type") == "product_category_clarification":
            return self._handle_category_clarification_reply(pending_id, reply_text, pending_entry)
        else:
            return self._handle_original_reply(pending_id, reply_text, pending_entry)

    def _handle_product_refinement_reply(self, pending_id: str, reply_text: str, pending_entry) -> AskResponse:
        """Handle product refinement conversation replies."""
        # Get conversation state
        state = self._conversation_manager.get_state(pending_id)
        if not state:
            self._pending_store.resolve_pending(pending_id)
            return AskResponse(type="error", reason="Conversation state not found")

        # Parse the refinement response
        category = state.detected_category or "printer"  # Default to printer
        filter_updates = {}
        
        # Try to parse budget response
        budget_result = self._question_generator.parse_budget_response(reply_text)
        if budget_result:
            filter_updates["budget"] = budget_result
            
        # Try to parse brand response  
        brand_result = self._question_generator.parse_brand_response(reply_text)
        if brand_result:
            filter_updates["brand"] = brand_result
            
        # Try to parse technology response
        tech_result = self._question_generator.parse_technology_response(reply_text, category)
        if tech_result:
            filter_updates["technology"] = tech_result

        # Update conversation state
        self._conversation_manager.update_state(pending_id, filter_updates)
        
        # Create search filters from current state
        search_filters = self._conversation_manager.create_search_filters(state)
        
        # Search for products with updated filters
        products = self._product_catalog.search_products(search_filters)
        
        # Check if we need more refinement or can return results
        if not products:
            self._conversation_manager.remove_state(pending_id)
            self._pending_store.resolve_pending(pending_id)
            return AskResponse(
                type="no_results",
                text="Unfortunately, no products match your refined criteria. Please try again with different preferences."
            )
        elif len(products) > self._product_catalog.result_threshold:
            # Still too many results, ask for more refinement
            next_question = self._question_generator.get_next_question(category, state.applied_filters)
            
            if next_question:
                # Update pending store with new context
                conversation_context = {
                    "type": "product_refinement", 
                    "detected_category": category,
                    "product_count": len(products)
                }
                self._pending_store.save_pending(
                    pending_id, 
                    pending_entry.question,
                    ttl_seconds=300,
                    conversation_context=conversation_context
                )
                
                return AskResponse(
                    type="ask_user",
                    prompt=next_question,
                    pending_id=pending_id
                )
            else:
                # No more questions, return top results
                top_products = self._product_catalog.get_top_products(products, count=5)
                self._conversation_manager.remove_state(pending_id)
                self._pending_store.resolve_pending(pending_id)
                
                return AskResponse(
                    type="product_list",
                    text=f"Here are the top 5 products from {len(products)} matches:",
                    products=top_products
                )
        else:
            # Good number of results
            self._conversation_manager.remove_state(pending_id)
            self._pending_store.resolve_pending(pending_id)
            
            return AskResponse(
                type="product_list",
                text=f"Here are {len(products)} matching products:",
                products=products
            )

    def _handle_category_clarification_reply(self, pending_id: str, reply_text: str, pending_entry) -> AskResponse:
        """Handle product category clarification replies."""
        # Try to detect category from reply
        category = self._orchestrator._domain_validator.detect_product_category(reply_text)
        
        if not category or category == "unknown_product":
            self._pending_store.resolve_pending(pending_id)
            return AskResponse(
                type="not_relevant",
                text="I'm not sure which product category you're interested in. Please be more specific about what you're looking for.",
                supported_domains=self._orchestrator._domain_validator.get_supported_domains()
            )
        
        # Now proceed with product search using the clarified category
        self._pending_store.resolve_pending(pending_id)
        
        # Create new question combining original and clarification
        combined_question = f"{pending_entry.question} {reply_text}"
        return self.answer(combined_question)

    def _handle_original_reply(self, pending_id: str, reply_text: str, pending_entry) -> AskResponse:
        """Handle original non-product conversation replies."""
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

        return AskResponse(type="answer", text=combined_text)
