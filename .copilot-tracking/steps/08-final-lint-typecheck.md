# Step 8: Final lint/format/type-check

## Objective
Confirm repository is clean: linters and formatters pass, and any basic type checks are OK.

## Prerequisites
- Steps 1-7 completed
- `ruff`, `black`, and optional `mypy`/type-checker available (mypy optional)

## Actions
1. Re-run `ruff` and `black` across the repo.
2. Optionally run `mypy` or a lightweight type check if configured.
3. Record outputs and ensure no new issues.

## Success Criteria
- `ruff` and `black` clean; optional type-check passes.

## Next Step
Continue to: `./steps/09-produce-patchset.md`

## Cleanup
When this step is completed successfully, this file can be deleted.
