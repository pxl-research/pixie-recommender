---
mode: agent
model: Claude Sonnet 4
---
<!-- markdownlint-disable-file -->
# Implementation Prompt: Conversation Loop Flow

## Implementation Instructions

### Step 1: Create Changes Tracking File

You WILL create `20250909-conversation-loop-flow-changes.md` in #file:../changes/ if it does not exist. The planner will NOT modify any existing abstract classes (for example `pixie/core/abstractclasses/llm.py`).

### Step 2: Execute Implementation

You WILL follow #file:../../.github/instructions/task-implementation.instructions.md
You WILL follow the plan in #file:../plans/20250909-conversation-loop-flow-plan.instructions.md but note: this prompt is planning-only. The agent must NOT implement code nor modify existing abstract classes. Every execution phase and task requires an explicit approval gate from the user before any code changes are made.

**CRITICAL**: EVERY phase and task requires explicit user approval before implementation. The planner stops after creating the concrete plan for each task and awaits your approval.

### Step 3: Cleanup

When ALL Phases are checked off (`[x]`) and completed you WILL do the following:
  1. You WILL provide a markdown style link and a summary of all changes from #file:../changes/20250909-conversation-loop-flow-changes.md to the user (only after you have approved and the changes have actually been made):
    - You WILL keep the overall summary brief
    - You WILL add spacing around any lists
    - You MUST wrap any reference to a file in a markdown style link
  2. You WILL provide markdown style links to .copilot-tracking/plans/20250909-conversation-loop-flow-plan.instructions.md, .copilot-tracking/details/20250909-conversation-loop-flow-details.md, and .copilot-tracking/research/20250908-conversation-loop-flow-research.md documents. You WILL recommend cleaning these files up as well.
  3. **MANDATORY**: You WILL attempt to delete .copilot-tracking/prompts/implement-conversation-loop-flow.prompt.md

## Success Criteria

- [ ] Changes tracking file created
- [ ] All plan items implemented with working code (after explicit approvals)
- [ ] All detailed specifications satisfied
- [ ] Project conventions followed
- [ ] Changes file updated continuously (only after commits are made post-approval)
---
mode: agent
model: Claude Sonnet 4
---
<!-- markdownlint-disable-file -->
# Implementation Prompt: Conversation Loop Flow Implementation

## Implementation Instructions

### Step 1: Create Changes Tracking File

You WILL create `20250908-conversation-loop-flow-changes.md` in #file:../changes/ if it does not exist.

### Step 2: Execute Implementation

You WILL follow #file:../../.github/instructions/task-implementation.instructions.md
You WILL systematically implement #file:../plans/20250908-conversation-loop-flow-plan.instructions.md task-by-task
You WILL follow ALL project standards and conventions

**CRITICAL**: If ${input:phaseStop:true} is true, you WILL stop after each Phase for user review.
**CRITICAL**: If ${input:taskStop:false} is true, you WILL stop after each Task for user review.

### Step 3: Cleanup

When ALL Phases are checked off (`[x]`) and completed you WILL do the following:
  1. You WILL provide a markdown style link and a summary of all changes from #file:../changes/20250909-conversation-loop-flow-changes.md to the user:
    - You WILL keep the overall summary brief
    - You WILL add spacing around any lists
    - You MUST wrap any reference to a file in a markdown style link
  2. You WILL provide markdown style links to .copilot-tracking/plans/20250908-conversation-loop-flow-plan.instructions.md, .copilot-tracking/details/20250908-conversation-loop-flow-details.md, and .copilot-tracking/research/20250908-conversation-loop-flow-research.md documents. You WILL recommend cleaning these files up as well.
  3. **MANDATORY**: You WILL attempt to delete .copilot-tracking/prompts/implement-conversation-loop-flow.prompt.md

## Success Criteria

- [ ] Changes tracking file created
- [ ] All plan items implemented with working code
- [ ] All detailed specifications satisfied
- [ ] Project conventions followed
- [ ] Changes file updated continuously
