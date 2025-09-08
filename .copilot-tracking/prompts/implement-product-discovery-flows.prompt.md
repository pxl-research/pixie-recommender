---
mode: agent
model: Claude Sonnet 4
---
<!-- markdownlint-disable-file -->
# Implementation Prompt: Product Discovery Flows Implementation

## Implementation Instructions

### Step 1: Create Changes Tracking File

You WILL create `20250908-product-discovery-flows-changes.md` in #file:../changes/ if it does not exist.

### Step 2: Execute Implementation

You WILL follow #file:../../.github/instructions/task-implementation.instructions.md
You WILL systematically implement #file:../plans/20250908-product-discovery-flows-plan.instructions.md task-by-task
You WILL follow ALL project standards and conventions

**CRITICAL**: If ${input:phaseStop:true} is true, you WILL stop after each Phase for user review.
**CRITICAL**: If ${input:taskStop:false} is true, you WILL stop after each Task for user review.

### Step 3: Implementation Priorities

**Phase 1 Priority**: Extend response contracts first - all other components depend on these data structures.

**Phase 2 Priority**: Build comprehensive mock data - realistic product catalog enables proper testing of all flows.

**Phase 3 Priority**: Enhance orchestrator logic carefully - this is the core intelligence that drives conversation flows.

**Phase 4 Priority**: Integration and testing - validate everything works end-to-end with comprehensive test coverage.

### Step 4: Validation Requirements

For each implemented flow, you MUST validate:

1. **Flow 1 (Product Found)**: Progressive refinement from "I'm looking for a printer" through budget/brand/technology questions to final product list
2. **Flow 2 (Not Relevant)**: Graceful rejection of out-of-scope questions with supported domain listing
3. **Flow 3 (No Results)**: Empty result handling with alternative suggestions
4. **Flow 4 (Too Many Results)**: Large result set management with sorting and sampling options

### Step 5: Testing Strategy

- Unit tests for each new component (FakeProductCatalog, domain validation, etc.)
- Integration tests for complete conversation flows
- API endpoint tests for all new response types
- Backward compatibility tests to ensure no regression

### Step 6: Cleanup

When ALL Phases are checked off (`[x]`) and completed you WILL do the following:
  1. You WILL provide a markdown style link and a summary of all changes from #file:../changes/20250908-product-discovery-flows-changes.md to the user:
    - You WILL keep the overall summary brief
    - You WILL add spacing around any lists
    - You MUST wrap any reference to a file in a markdown style link
  2. You WILL provide markdown style links to .copilot-tracking/plans/20250908-product-discovery-flows-plan.instructions.md, .copilot-tracking/details/20250908-product-discovery-flows-details.md, and .copilot-tracking/research/20250908-product-discovery-flows-research.md documents. You WILL recommend cleaning these files up as well.
  3. **MANDATORY**: You WILL attempt to delete .copilot-tracking/prompts/implement-product-discovery-flows.prompt.md

## Success Criteria

- [ ] Changes tracking file created
- [ ] All 4 core flows from copilot-instructions.md work with realistic mock data
- [ ] Progressive product discovery through multiple conversation turns
- [ ] Domain validation and graceful out-of-scope handling  
- [ ] Result management for empty and large result sets
- [ ] Backward compatibility maintained with existing functionality
- [ ] Comprehensive test coverage for all new features
- [ ] Changes file updated continuously
