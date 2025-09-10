---
mode: agent
model: Claude Sonnet 4
---
<!-- markdownlint-disable-file -->
# Implementation Prompt: Real Search Implementation

## Implementation Instructions

### Step 1: Create Changes Tracking File

You WILL create `20250909-real-search-implementation-changes.md` in #file:../changes/ if it does not exist.

### Step 2: Execute Implementation

You WILL follow #file:../../.github/instructions/task-implementation.instructions.md
You WILL systematically implement #file:../plans/20250909-real-search-implementation-plan.instructions.md task-by-task
You WILL follow ALL project standards and conventions

**CRITICAL**: If ${input:phaseStop:true} is true, you WILL stop after each Phase for user review.
**CRITICAL**: If ${input:taskStop:false} is true, you WILL stop after each Task for user review.

### Step 3: Implementation Guidelines

**Data Creation Priority**: Create realistic printer dataset with proper Dutch names and specifications
**Compatibility First**: Ensure all existing tests continue to pass with new implementation
**Performance Focus**: Maintain sub-100ms response times for search operations
**Clean Integration**: Use factory pattern for seamless mock/real engine switching

### Step 4: Validation Requirements

**Before completing each phase**:
1. Run existing test suite to verify no regressions
2. Test specific attribute filtering scenarios (budget, brand, technology)
3. Verify backward compatibility with MockSearchEngine interface
4. Check performance with realistic data size

### Step 5: Cleanup

When ALL Phases are checked off (`[x]`) and completed you WILL do the following:
  1. You WILL provide a markdown style link and a summary of all changes from #file:../changes/20250909-real-search-implementation-changes.md to the user:
    - You WILL keep the overall summary brief
    - You WILL add spacing around any lists
    - You MUST wrap any reference to a file in a markdown style link
  2. You WILL provide markdown style links to .copilot-tracking/plans/20250909-real-search-implementation-plan.instructions.md, .copilot-tracking/details/20250909-real-search-implementation-details.md, and .copilot-tracking/research/20250909-real-search-implementation-research.md documents. You WILL recommend cleaning these files up as well.
  3. **MANDATORY**: You WILL attempt to delete .copilot-tracking/prompts/implement-real-search-implementation.prompt.md

## Success Criteria

- [ ] Changes tracking file created
- [ ] All plan phases implemented with working real search functionality
- [ ] Comprehensive printer dataset with 20-50 realistic entries
- [ ] Attribute-based filtering working for budget, brand, technology
- [ ] All existing tests pass with RealSearchEngine
- [ ] Factory pattern enables easy mock/real engine switching
- [ ] Performance meets sub-100ms requirements
- [ ] Documentation updated with new capabilities
- [ ] Changes file updated continuously
