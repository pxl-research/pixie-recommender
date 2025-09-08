<!-- markdownlint-disable-file -->
# Task Details: Product Discovery Flows Implementation

## Research Reference

**Source Research**: #file:../research/20250908-product-discovery-flows-research.md

## Phase 1: Enhanced Response Types

### Task 1.1: Extend AskResponse contract with product list support

Add new response types and fields to support product listings and refinement questions.

- **Files**:
  - pixie/core/contracts.py - Extend AskResponse model with product fields
- **Success**:
  - AskResponse supports `products` field for product listings
  - New response type `product_list` properly validated
  - Refinement context fields added for conversation state
- **Research References**:
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 24-35) - Response Contract Structure
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 37-65) - Required Core Flows
- **Dependencies**:
  - Existing Pydantic validation patterns

### Task 1.2: Add refinement question generation patterns

Create intelligent question patterns for progressive product discovery.

- **Files**:
  - pixie/core/product_questions.py - New module for refinement question logic
- **Success**:
  - Budget refinement questions with predefined ranges
  - Brand selection questions from supported list
  - Technology filtering questions (inkjet, laser, thermal)
  - Question ordering logic for optimal refinement flow
- **Research References**:
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 37-42) - Flow 1: Product Found Pattern
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 95-110) - Filter Categories
- **Dependencies**:
  - Task 1.1 completion (enhanced AskResponse)

## Phase 2: Mock Product Catalog

### Task 2.1: Create FakeProductCatalog class with sample data

Implement comprehensive mock product database with realistic sample data.

- **Files**:
  - pixie/core/fake_catalog.py - New FakeProductCatalog class
- **Success**:
  - At least 20 sample products across multiple categories
  - Product schema matches research specifications (id, name, price, brand, category, technology, description)
  - Products cover all budget ranges (under €150, €150-€300, over €300)
  - Multiple brands represented (Brother, HP, Kyocera, Canon, Epson)
  - Different technologies available (inkjet, laser, thermal inkjet)
- **Research References**:
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 67-93) - Mock Data Requirements
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 95-110) - Filter Categories
- **Dependencies**:
  - None (standalone mock data)

### Task 2.2: Implement filtering by budget, brand, and technology

Add comprehensive filtering capabilities to the product catalog.

- **Files**:
  - pixie/core/fake_catalog.py - Add filtering methods to FakeProductCatalog
- **Success**:
  - `filter_by_budget()` method with range parsing
  - `filter_by_brand()` method with case-insensitive matching
  - `filter_by_technology()` method with technology type validation
  - `filter_by_category()` method for supported product categories
  - Chainable filtering for multiple criteria application
- **Research References**:
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 95-110) - Filter Categories
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 37-42) - Progressive Refinement Pattern
- **Dependencies**:
  - Task 2.1 completion (FakeProductCatalog base class)

### Task 2.3: Add result management (empty, too many results)

Implement logic for handling edge cases in product search results.

- **Files**:
  - pixie/core/fake_catalog.py - Add result management methods
  - pixie/core/result_manager.py - New module for result handling strategies
- **Success**:
  - Empty result detection and alternative suggestion generation
  - Large result set detection (threshold configurable, default 10)
  - Sorting options (price ascending/descending, name alphabetical)
  - Random sampling for large result sets
  - "Top N" selection with configurable N
- **Research References**:
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 44-48) - Flow 3: No Results
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 50-65) - Flow 4: Too Many Results
- **Dependencies**:
  - Task 2.1 and 2.2 completion (filtering functionality)

## Phase 3: Enhanced Orchestrator Logic

### Task 3.1: Add product discovery decision patterns

Extend the Orchestrator class to recognize and handle product discovery conversations.

- **Files**:
  - pixie/core/pixie.py - Extend Orchestrator._simulate_llm_decision method
- **Success**:
  - Product-related question detection patterns
  - Progressive refinement decision logic
  - Integration with FakeProductCatalog for product queries
  - Decision flow that matches copilot-instructions examples
- **Research References**:
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 37-65) - All 4 Core Flows
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 143-161) - Current Orchestrator Decision Logic
- **Dependencies**:
  - Phase 2 completion (FakeProductCatalog functionality)
  - Task 1.1 completion (enhanced response types)

### Task 3.2: Implement domain validation for supported categories

Add domain filtering to reject out-of-scope questions gracefully.

- **Files**:
  - pixie/core/domain_validator.py - New module for domain validation
  - pixie/core/pixie.py - Integrate domain validation into Orchestrator
- **Success**:
  - Supported domain list (printers, laptops, smartphones, tablets)
  - Out-of-scope question detection patterns
  - Graceful rejection responses with supported domain enumeration
  - Clear messaging that matches Flow 2 example from instructions
- **Research References**:
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 43-48) - Flow 2: Not Relevant
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 95-110) - Supported Categories
- **Dependencies**:
  - Task 3.1 completion (enhanced decision patterns)

### Task 3.3: Add progressive refinement conversation state management

Implement conversation state tracking for multi-turn product discovery.

- **Files**:
  - pixie/core/conversation_state.py - New module for state management
  - pixie/core/pending_store.py - Extend to store refinement context
- **Success**:
  - Track applied filters across conversation turns
  - Store partial product search state in pending entries
  - Intelligent next question selection based on current filters
  - Conversation completion detection when sufficient filters applied
- **Research References**:
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 37-42) - Progressive Refinement Pattern
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 8-18) - Current Pending Store System
- **Dependencies**:
  - Task 3.2 completion (domain validation)
  - Task 1.2 completion (refinement questions)

## Phase 4: Integration & Testing

### Task 4.1: Update API endpoints to handle product response types

Modify the FastAPI application to properly serialize and return product data.

- **Files**:
  - apps/api/main.py - Update response handling for product types
- **Success**:
  - Product list responses properly serialized in API responses
  - Refinement question responses include conversation context
  - Error responses for domain validation failures
  - API documentation updated with new response schemas
- **Research References**:
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 19-23) - API Implementation
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 163-175) - Current API Flow
- **Dependencies**:
  - Phase 3 completion (enhanced Orchestrator)
  - Task 1.1 completion (enhanced response types)

### Task 4.2: Create comprehensive tests for all 4 core flows

Add test coverage for all product discovery scenarios and edge cases.

- **Files**:
  - tests/test_product_discovery.py - New comprehensive test suite
  - tests/test_fake_catalog.py - Unit tests for catalog functionality
  - tests/test_api_product_flows.py - Integration tests for API endpoints
- **Success**:
  - Flow 1 (Product Found): Complete printer discovery scenario
  - Flow 2 (Not Relevant): Out-of-scope question handling
  - Flow 3 (No Results): Empty result scenario and alternatives
  - Flow 4 (Too Many Results): Large result set management
  - Edge case coverage (invalid filters, malformed requests)
  - Performance validation (response time < 100ms for catalog queries)
- **Research References**:
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 37-65) - All Core Flow Examples
  - #file:../../tests/test_api_routes.py - Existing test patterns
- **Dependencies**:
  - Task 4.1 completion (API integration)
  - All previous phases (complete functionality)

### Task 4.3: Validate backward compatibility with existing functionality

Ensure all existing functionality continues to work without regression.

- **Files**:
  - Run existing test suite with new changes
  - tests/test_backward_compatibility.py - New compatibility validation tests
- **Success**:
  - All existing tests pass without modification
  - Original ask/reply flows work unchanged for non-product questions
  - API contracts remain stable for existing clients
  - Performance impact minimal (< 10ms overhead for non-product queries)
- **Research References**:
  - #file:../research/20250908-product-discovery-flows-research.md (Lines 8-35) - Current Architecture Analysis
  - #file:../../tests/ - Existing test coverage
- **Dependencies**:
  - Task 4.2 completion (comprehensive testing)

## Dependencies

- FastAPI framework with Pydantic validation
- Python 3.12+ type system for robust mock implementations
- pytest framework for comprehensive test coverage

## Success Criteria

- All 4 core flows from copilot-instructions.md demonstrate realistic product discovery
- Progressive refinement works across multiple conversation turns
- Domain validation gracefully handles out-of-scope questions
- Result management handles both empty and oversized result sets appropriately
- Backward compatibility maintained with zero breaking changes
- Test coverage exceeds 90% for all new functionality
