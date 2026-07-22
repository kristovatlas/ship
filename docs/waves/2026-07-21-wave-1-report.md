# Wave 1 report — ship the ship skill + review gate

Delivered as a message 2026-07-21; retro-committed under the option-C
convention (SKILL.md Phase 5) in wave 2. Decisions shown with their
answers.

## 1. Decisions needed

1. **Merge PR #1** — escalated (bootstrap PR; touches the gate trust
   boundary). *Answered: approved and merged 2026-07-22 (f257821).*
2. **Finish the ruleset** (required checks `review-gate` + `tests`,
   require branches up to date). *Answered: done 2026-07-22; enforcement
   probe-verified (PR #2 hard-blocked).*
3. **Skill version lineage** — repo says v0.1.0; pre-extraction lineage
   was "ship-v4". *Answered: keep repo-era numbering; prehistory noted in
   the changelog (wave 2).*

## 2. Conversations worth having

- The battery earned its keep on its own gate: four rounds, ~30 findings,
  three blocking — a P1 introduced by a round-1 fix (orderFile pin
  crashing the hash; caught by delta verification), a `.gitmodules
  ignore=all` submodule-pointer bypass of the staleness hash (high,
  codex, reproduced before fixing), and the hash not binding the
  merge-base id (high; found independently by codex security and the
  Claude review leg). Round 4 caught fixes hollowing out earlier
  regression tests. Full audit record: `docs/reviews/pr-1/`.
- Merge-base binding is a deliberate strictness increase over somnus:
  base advances restale artifacts and force re-review of combined state.
  Serial multi-lane merges therefore re-run batteries per lane; token
  cost accepted (Kristov). This is the knob if that changes.
- Wave-report placement wrinkle → resolved as option C (this file's own
  convention; SKILL.md Phase 5, decided 2026-07-22).
- Watch in use: the submodule regression test flaked locally then failed
  on CI's older git (`git add <submodule>` porcelain semantics under
  `ignore=all` vary by version); fixed via `update-index --cacheinfo`
  plumbing. Deterministic claims eventually want CI git-version pinning.

## 3. What shipped

A single PR turning the two dropped-in markdown files into an
installable, self-governing skill repo: the ship skill (v0.1.0, with
version/source provenance for copy-pasters), its rationale doc, and a
reference review-gate implementation — a stdlib-only gate script
enforcing four review legs (Claude + Codex, code + security each) with
merge-base-bound, config-pinned diff-hash staleness, a deterministic
model floor, severity validation, and fix-or-dismiss dispositions —
behind a CI job that runs the base branch's copy of the script. Plus 44
unit tests, the process doc, the wave plan with its matched predicted
touch-set, README, MIT license, and the four attested review artifacts
for the PR itself.

## 4. Verification asks

- Merge, then confirm the post-merge run on `main` goes green. *Done:
  success.*
- After extending the ruleset, confirm GitHub blocks an unattested
  branch. *Done: probe PR #2, "base branch policy prohibits the merge".*
- Optionally clone into `~/.claude/skills/ship` elsewhere and confirm
  pickup. *Open.*
