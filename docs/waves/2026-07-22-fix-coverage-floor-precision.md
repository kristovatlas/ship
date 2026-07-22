# Single-change lane — 2026-07-22 — make the coverage floor actually fail

SKILL.md single-small-change path (Phases 0–1 skipped; touch-set below).

**Task:** the required `tests` check reported success on a 98.51%
coverage run despite `fail_under = 99`. Root cause (found by the
standards-enforcement probe PR #6 and reproduced locally): coverage.py
compares `fail_under` against the total **rounded to the configured
`precision`** — default 0 decimal places — so 98.51 rounds to 99 and
passes with exit 0, while pytest-cov's *message* uses the raw value and
prints FAIL. The floor therefore had a ±0.5-point blind spot; a small
uncovered file could land without tripping CI.

**Fix:** `precision = 2` in `[tool.coverage.report]` (verified: breach
now exits 1 and fails the job; clean tree still passes), plus an ADR 0005
note recording the rounding semantics so the floor's mechanics are
documented as they are.

**Predicted touch-set:**
- `pyproject.toml` (one line)
- `docs/adr/0005-test-and-coverage-policy.md` (precision note)
- `docs/waves/2026-07-22-fix-coverage-floor-precision.md` (this file)
- `docs/reviews/pr-<N>/*.json` (hash-exempt)

**Threat model impact:** none new — strengthens an existing detective
control (asset 4, assurance signals); no new surface, no dependency
change. Merge escalates to Kristov anyway: the change alters a required
check's pass/fail semantics, which we treat as gate-trust-boundary
adjacent even though it lives in pyproject.toml rather than
`.github/workflows/`.

**Verification:** post-merge, re-run the uncovered-file probe and confirm
the `tests` check goes red this time.
