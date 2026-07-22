# Dependency policy: hermetic gate, pinned dev deps, 7-day cooldown

- Status: accepted
- Date: 2026-07-21/22
- Deciders: Kristov Atlas

## Context and problem statement

Supply-chain attacks on package registries typically exploit the window
right after a malicious release, before detection. This repo's gate
script is also the enforcement mechanism itself — its dependencies are
attack surface against the control, not just the code.

## Decision outcome

Three tiers:

1. **The gate is hermetic**: `scripts/review_gate.py` is stdlib-only,
   forever. The job that decides merges downloads nothing.
2. **Dev/CI dependencies are exactly pinned** in `requirements-dev.txt`
   (or, where isolation is cheaper, inline in the job with the same
   rules), and every new pin must be **≥ 7 days past its release** when
   added (Kristov, 2026-07-21). Applied on day one: ruff 0.15.22 was six
   days old and was skipped for 0.15.21. Third-party actions are pinned
   by commit SHA *and* their runtime-downloaded scanner binaries are
   version-pinned in the workflow.
3. **Layered detection**: pip-audit (known CVEs) + Socket (heuristics)
   + the battery's security legs (review of every dependency change).
   A new dependency is a security-posture change and escalates to the
   human per the ship escalation list.

## Accepted residuals (battery, PR #4)

- Scanner binaries (gitleaks, lychee) download at run time without
  checksum verification; version-pinned but assets are mutable upstream.
- Transitive dependencies float past the cooldown (no `--require-hashes`
  yet).

Both are **dev-scoped**: they execute in read-only, secretless CI jobs
with no path to the consumer supply chain (see `docs/THREAT_MODEL.md`).
Future work: hash-pinned resolution (pip-compile/uv with
`min-release-age`, mirroring somnus T-13) when the dependency count
justifies the tooling.
