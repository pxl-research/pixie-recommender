# Step 9: Produce patchset and test/lint results for review

## Objective
Gather the final diff/patch and the lint/test outputs into a concise summary for your review and approval before commit.

## Prerequisites
- Steps 1-8 completed and repository state as intended locally

## Actions
1. Run `git diff --staged` or `git diff` to produce the patch summary.
2. Save `pytest` output and `ruff`/`black` outputs to files or paste into a short report.
3. Create a short checklist indicating all tests passed and linters clean.
4. Attach diff and logs to the PR description or a review comment.

## Success Criteria
- A clear patch/diff and logs ready for your review.

## Next Step
Continue to: `./steps/10-await-approval.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
