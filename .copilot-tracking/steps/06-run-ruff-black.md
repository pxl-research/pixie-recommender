# Step 6: Run `ruff --fix` and `black` on changed files

## Objective
Ensure code style and simple lint issues are auto-fixed using `ruff --fix` and `black`.

## Prerequisites
- Steps 1-5 applied locally
- `ruff` and `black` available in dev environment

## Actions
1. Run `ruff --fix` on the repository or the changed files.
2. Run `black` to format code.
3. Inspect any remaining `ruff` warnings that require manual edits and fix them.

## Success Criteria
- `ruff` and `black` report no remaining errors on changed files.

## Next Step
Continue to: `./steps/07-run-tests.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
