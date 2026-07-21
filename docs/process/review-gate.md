# The review gate — deterministic enforcement of the review battery

**What it guarantees:** a PR cannot merge unless all four review legs ran
against the *current* code, each leg was produced by an allowlisted model,
every finding was validated, and no validated high/critical security
finding or P1 review finding remains unfixed. The gate is a dumb,
deterministic CI check (`review-gate` job → `scripts/review_gate.py`,
stdlib only) — it does not judge code; it judges that the judging happened
and met thresholds. Same gate for **every** PR, no exemptions (a docs-only
carve-out would be an escape hatch).

This is the reference implementation of the review-gate companion that the
`ship` skill (SKILL.md at the repo root) assumes. It was ported from the
implementation proven in kristovatlas/somnus and is dogfooded by this repo
itself: every PR here goes through it.

**What it cannot guarantee** (accepted, by design): that the artifacts are
*genuine*. It guards against forgetting and threshold-fudging, not
deception. Artifacts are permanent audit records; raw leg output is
embedded so fabrication would be a deliberate act, not drift. Two further
accepted residuals (identified in somnus PR #128 review): `docs/reviews/`
is hash-exempt, so a PR could rewrite *prior* PRs' artifacts without
tripping staleness (audit history is protected by git history + human
spot-checks, not the gate); and on `pull_request` events the workflow file
itself comes from the PR branch — CI therefore runs the **base branch's
copy of the gate script** against the PR checkout as data (a PR editing
`scripts/review_gate.py` cannot weaken its own enforcement), but a PR
editing `ci.yml`'s gate *job* can still neuter it; that last step is
caught only by review of `ci.yml` diffs — an inherent GitHub Actions
property. Both CI jobs run with `contents: read` and
`persist-credentials: false`.
Because a job skipped via an edited `if:` condition **reports success to
required-check evaluation** (GitHub-documented behavior), the ci.yml
residual has no red-flag failure mode — therefore **any PR touching
`.github/workflows/` or `scripts/review_gate.py` always escalates to the
human**, regardless of review outcomes (the one standing exception to
no-human-code-review). Bootstrap note: the gate's own introducing PR is
necessarily unprotected by itself; it runs the gate by convention.

**Ruleset settings** (admin, alongside adding the required checks): enable
*"require branches to be up to date before merging"* — a base-branch
advance then forces a branch update, which moves the merge-base, which
changes the three-dot diff hash, which stales the artifacts and forces
re-review. Without it, reviews attested at an older merge-base remain
valid while main advances.

## Branching

PRs merge straight to `main` (decided by Kristov, 2026-07-21). There is no
`dev` dogfooding branch and no release-PR variant; the gate always runs
with `--base origin/main`.

## Artifacts

Each PR commits `docs/reviews/pr-<N>/<leg>.json` for all four legs:

| file | leg type | blocking severities |
|---|---|---|
| `claude-code-review.json` | review | P1 |
| `claude-security-review.json` | security | critical, high |
| `codex-review.json` | review | P1 |
| `codex-security.json` | security | critical, high |

(The Claude combined review used in practice may emit both
`claude-code-review.json` and `claude-security-review.json` from one pass —
each attests its own dimension.)

Schema (all fields required unless noted):

```json
{
  "leg": "claude-code-review",
  "model": "claude-fable-5",
  "reviewed_diff_sha256": "<see Staleness binding>",
  "reviewed_at": "2026-07-21",
  "raw_output": "<the leg's full findings text, embedded>",
  "findings": [
    {
      "id": "F1",
      "summary": "one-line description",
      "severity_claimed": "P2",
      "validated": true,
      "severity_validated": "P2",
      "disposition": "fixed",
      "reason": "required when validated=false or disposition=dismissed"
    }
  ]
}
```

Severity enums — review legs: `P1 | P2 | P3 | nit`; security legs:
`critical | high | medium | low | info`. `findings: []` is valid (clean
leg). `disposition` ∈ `fixed | dismissed`. **`findings[]` is the canonical
machine record** — the gate thresholds it and only it; `raw_output` is an
audit aid so a human spot-check can catch a findings table that
under-reports its own prose (a sub-case of the genuineness residual,
deliberately not machine-checked).

## Model floor

Each leg's `model` must be on its vendor's allowlist, enforced by the gate
(`ALLOWED_MODELS` in `scripts/review_gate.py`):

- `claude-*` legs: `claude-opus-4-8`, `claude-fable-5`
- `codex-*` legs: `gpt-5.6-sol`

The floor is "these or better" (decided by Kristov, 2026-07-21). A better
model is admitted by adding its id to `ALLOWED_MODELS` via a gated PR —
which, because it edits the gate script, always escalates to the human.

## Gate rules (all enforced by `scripts/review_gate.py`)

1. `docs/reviews/pr-<N>/` exists and contains all four leg files, parseable
   against the schema, each with an allowlisted `model`.
2. Every finding carries a validation verdict (`validated` + a
   `severity_validated` from the leg's enum) and a disposition;
   `dismissed` and `validated: false` require a `reason`.
3. **Threshold:** no finding with `validated: true` at a blocking severity
   (security critical/high; review P1) may have any disposition other than
   `fixed`.
4. **Staleness binding:** `reviewed_diff_sha256` must equal the sha256 of
   the merge-base commit id + `\0` + the raw bytes of
   `git diff origin/main...HEAD -- . ':(exclude)docs/reviews'`
   as produced by `compute_diff_hash`. The merge-base id is bound in
   because diff bytes alone survive a base advance that touches none of
   the PR's files; binding it makes **every** base advance restale the
   artifacts and force re-review of the combined state. The diff
   invocation pins the byte-affecting knobs
   (`--no-ext-diff --no-textconv --no-renames --full-index --unified=3
   --inter-hunk-context=0 --no-color --ignore-submodules=none
   --submodule=short` plus `-c` overrides for prefix/algorithm/quotepath/
   orderFile/suppressBlankEmpty) so local and CI hashes agree —
   `--ignore-submodules=none` also blocks a PR-controlled `.gitmodules`
   `ignore=all` from hiding gitlink changes — regardless of user git
   config; an unpinned knob fails closed as a spurious STALE, never a
   wrongful pass. Any code change after
   the reviews invalidates them — which mechanically enforces the
   re-review-after-fix rule: a "fixed" blocking finding can only pass the
   gate via a post-fix re-attestation whose hash matches the fixed code.
   The `docs/reviews/` exclusion lets artifacts be committed without
   changing the hash they attest to.

## Authoring workflow (orchestrator)

1. Open the PR (reserves `<N>`); finish all fix rounds.
2. `python scripts/review_gate.py --hash-only` → embed the hash in each
   artifact while writing the validation sections.
3. Commit the artifacts (hash unaffected — excluded path).
4. `python scripts/review_gate.py --pr <N>` locally must pass before
   pushing; CI runs the same command as a required check.

## CI

Job `review-gate` (required check on `main`): checks out the PR **head**
(not the merge ref — so the merge-base diff matches what the orchestrator
hashed locally), full fetch depth, runs the script with the PR number and
base. Python-only, no dependencies. Job `tests` runs the gate's unit tests
(`tests/test_review_gate.py`, pytest).
