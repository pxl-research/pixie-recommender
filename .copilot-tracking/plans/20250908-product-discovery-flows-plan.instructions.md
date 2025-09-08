---
applyTo: '.copilot-tracking/changes/20250908-product-discovery-flows-changes.md'
---
<!-- markdownlint-disable-file -->
# Task Checklist: Product Discovery Flows Implementation

## Overview

Implement mocked product discovery flows to demonstrate the 4 core conversation patterns from copilot-instructions.md with realistic product data and progressive refinement.

## Objectives

- Create comprehensive mock product catalog with filtering capabilities
- Implement all 4 core flows: Product Found, Not Relevant, No Results, Too Many Results
- Add progressive refinement through multiple ask/reply cycles
- Maintain backward compatibility with existing functionality

## Research Summary

### Project Files
- pixie/core/pixie.py - Current orchestrator and mock adapter implementations
- pixie/core/contracts.py - Response data structures and validation
- apps/api/main.py - FastAPI endpoints with unified ask/reply flow
- .github/workflows/copilot-instructions.md - Core flow specifications

### External References
- #file:../research/20250908-product-discovery-flows-research.md - Complete technical analysis
- #file:../../.github/workflows/copilot-instructions.md - Business requirements and flow examples

### Standards References
- #file:../../pyproject.toml - Python project configuration and dependencies
- #file:../../tests/ - Existing test patterns for API and core functionality

## Implementation Checklist

### [ ] Phase 1: Enhanced Response Types

- [ ] Task 1.1: Extend AskResponse contract with product list support
  - Details: .copilot-tracking/details/20250908-product-discovery-flows-details.md (Lines 8-25)

- [ ] Task 1.2: Add refinement question generation patterns
  - Details: .copilot-tracking/details/20250908-product-discovery-flows-details.md (Lines 27-44)

### [ ] Phase 2: Mock Product Catalog

- [ ] Task 2.1: Create FakeProductCatalog class with sample data
  - Details: .copilot-tracking/details/20250908-product-discovery-flows-details.md (Lines 46-75)

- [ ] Task 2.2: Implement filtering by budget, brand, and technology
  - Details: .copilot-tracking/details/20250908-product-discovery-flows-details.md (Lines 77-94)

- [ ] Task 2.3: Add result management (empty, too many results)
  - Details: .copilot-tracking/details/20250908-product-discovery-flows-details.md (Lines 96-113)

### [ ] Phase 3: Enhanced Orchestrator Logic

- [ ] Task 3.1: Add product discovery decision patterns
  - Details: .copilot-tracking/details/20250908-product-discovery-flows-details.md (Lines 115-135)

- [ ] Task 3.2: Implement domain validation for supported categories
  - Details: .copilot-tracking/details/20250908-product-discovery-flows-details.md (Lines 137-150)

- [ ] Task 3.3: Add progressive refinement conversation state management
  - Details: .copilot-tracking/details/20250908-product-discovery-flows-details.md (Lines 152-169)

### [ ] Phase 4: Integration & Testing

- [ ] Task 4.1: Update API endpoints to handle product response types
  - Details: .copilot-tracking/details/20250908-product-discovery-flows-details.md (Lines 171-185)

- [ ] Task 4.2: Create comprehensive tests for all 4 core flows
  - Details: .copilot-tracking/details/20250908-product-discovery-flows-details.md (Lines 187-210)

- [ ] Task 4.3: Validate backward compatibility with existing functionality
  - Details: .copilot-tracking/details/20250908-product-discovery-flows-details.md (Lines 212-225)

## Dependencies

- FastAPI framework (existing)
- Pydantic data validation (existing)
- pytest testing framework (existing)
- Python 3.12+ type system (existing)

## Success Criteria

- All 4 core flows from copilot-instructions.md work with realistic mock data
- Progressive product refinement through budget/brand/technology questions
- Proper handling of empty results and large result sets
- Domain validation rejects unsupported categories gracefully
- Comprehensive test coverage validates all new functionality
- Existing API contracts and tests remain unbroken
