# Test and coverage policy

- Status: accepted
- Date: 2026-07-22
- Deciders: Kristov Atlas

## Context and problem statement

The repo's code is small but load-bearing: the gate script is process
infrastructure whose failure modes are "wrongful pass" (catastrophic) and
"wrongful block" (annoying). What testing standard applies?

## Decision outcome

Google's coverage guidance (testing.googleblog.com, 2020-08), adapted:

- **Patch coverage over aggregate worship**: what matters is that *new
  and changed* code is tested. The review battery's correctness legs are
  prompted to flag untested new branches — this is the primary control,
  because a deterministic floor cannot judge test *quality*.
- **A CI floor as the backstop**: `fail_under = 99` (branch coverage,
  `pyproject.toml`), set just under the measured value (100% after the
  wave-2 gap-closing work) so silent regression trips CI. The floor
  follows reality; it is re-derived when code grows, never lowered to
  make a PR pass (lowering it is a standards change → gated PR + ADR
  update).
- **Tests are code**: the gate's tests get the same battery review as
  the gate. Vacuous tests are treated as defects — precedent: PR #1
  round 4, where both models caught a regression test hollowed out by a
  prior fix, and PR #4, where mutation checks (delete the pin, test must
  fail) were used to prove test meaning.
- **Behavioral tests over mocks**: real git repos in tmp dirs, real
  subprocess CLI invocations; in-process equivalents exist only where
  coverage measurement requires them, kept in sync with the subprocess
  truth tests.

### Consequences

- Good: 100% branch coverage achieved and cheap to hold at this size;
  regressions surface in CI, quality regressions surface in review.
- Bad: the floor says nothing about assertion strength — accepted, that
  is the battery's job (and mutation-style spot checks during review).
