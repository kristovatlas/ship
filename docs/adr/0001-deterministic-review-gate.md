# Deterministic review gate as the merge control

- Status: accepted
- Date: 2026-07-21 (recorded 2026-07-22)
- Deciders: Kristov Atlas

## Context and problem statement

PRs in this repo are authored and reviewed by LLMs, whose output is
non-deterministic. How do we decide a PR is safe to merge without a human
reading every diff, and without trusting any single model run?

## Decision drivers

- LLM review output varies run to run; enforcement must not.
- Human attention should go to product/scope/security decisions, not
  routine diffs (see `references/rationale.md`).
- A control that can be forgotten is not a control.

## Considered options

1. Deterministic gate over review *artifacts* (chosen).
2. Make the reviewer itself deterministic (voting, pinned prompts,
   structured verdicts as the primary control).
3. Human review of every PR.

## Decision outcome

Option 1. A stdlib-only script (`scripts/review_gate.py`) behind a
required CI check verifies that four review legs (Claude + Codex, code +
security each) ran against the *current* code, that every finding was
severity-validated and dispositioned, and that no validated blocking
finding is unfixed. Staleness is bound by
`sha256(merge-base-id + NUL + pinned-diff-bytes)`. CI executes the **base
branch's copy** of the script so a PR cannot weaken its own enforcement.
Full mechanics and accepted residuals: `docs/process/review-gate.md`.

### Consequences

- Good: forgetting is impossible; thresholds are machine-enforced; the
  fuzzy part is contained to what the models actually write.
- Good: every base advance restales artifacts, mechanically forcing
  re-review of combined state (strict up-to-date ruleset).
- Bad: docs-only PRs pay the full battery cost — accepted, because a
  carve-out would be an escape hatch (this skill's markdown *is* the
  executable product).
- Residual: the gate judges that judging happened, not that artifacts are
  genuine — see the process doc's residuals section.

## Validation

The gate found three blocking defects in its own introduction (PR #1,
four battery rounds) and was probe-verified to hard-block an unattested
PR (probe PR #2, 2026-07-22).
