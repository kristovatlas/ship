# Wave 2 report — engineering standards

Milestone: issue #3. Two stacked lanes: PR #4 (CI standards, merged
09f84b8 after human review — workflows trust boundary) and PR #5 (this
document's own PR; docs). First wave run end-to-end under the live gate,
and this report's placement is the first use of the Phase 5 option-C
convention.

## 1. Decisions needed

1. **Promote `lint-type`, `security-hygiene`, and `links` to required
   checks** in the ruleset. They run on every PR but are advisory until
   then, and the standards table says so. *Recommendation: promote all
   three; they were green on every run this wave.*
2. **Cut the first tag, `v0.2.0`** (releases escalate by list). The docs
   now honestly say no tags exist; this makes the pinning story real.
   *Recommendation: tag the lane-B merge commit.*
3. **gitleaks license contingency**: if this repo ever moves to an org
   account, `GITLEAKS_LICENSE` becomes required or the job hard-fails.
   No action now; noting for the record.

## 2. Conversations worth having

- The battery's dominant catch this wave, across three independent legs,
  was docs describing *intended* posture as shipped fact (tags that
  didn't exist, jobs called enforcement while advisory, "no secrets"
  where a token exists, "downloads nothing" where SHA-pinned actions
  run). Every instance was rewritten to what is. For a repo whose
  product is instructions, that review pressure is the whole game.
- PR #4's security legs established that SHA-pinning scanner *actions*
  does not pin the scanner *binaries* they download at run time; both
  binaries are now version-pinned in the workflow and the checksum
  residual is recorded as dev-scoped (THREAT_MODEL.md threat 3 — cannot
  reach skill consumers).
- The touch-set gate caught `git add -A` sweeping Kristov's local
  never-commit scratch file into an attested diff; staging is
  explicit-path from now on (precedent recorded in
  engineering-standards.md).
- Cross-model disagreement worth remembering: codex judged the Phase 5
  report convention creates no new unreviewed-content channel; the
  Claude leg argued the equivalence-to-delta-note claim was overstated.
  Resolution: the wording now concedes the wider window and requires the
  committed report to match the delivered message.
- The 7-day dependency cooldown bit on its first application (ruff
  0.15.22, six days old, skipped for 0.15.21) — evidence the policy is
  live, not aspirational.

## 3. What shipped

Lane A: deterministic enforcement of the code-quality standards — a
99% branch-coverage floor (measured 100% after closing every known gap,
including in-process equivalents of the CLI subprocess tests), ruff and
strict mypy, gitleaks and pip-audit and lychee (SHA-pinned actions,
version-pinned binaries, exact cooldown-checked package pins), all under
`contents: read` with no persisted credentials.

Lane B: the permanent record — five MADR ADRs backfilling the standing
decisions (gate architecture, model allowlist, main-only trunk,
dependency policy, test/coverage policy), a one-page threat model built
around the consumer-vs-dev boundary with a per-PR
assess-and-update-in-the-same-PR rule, an engineering-standards page
mapping every practice to its enforcement, the Phase 5 wave-report
convention codified in SKILL.md (v0.2.0, changelog + v1–v3 prehistory),
and the wave-1 report retro-committed with its decisions answered.

## 4. Verification asks

- After promoting the three checks: push any branch that fails ruff (or
  drops a test) and confirm GitHub blocks it — same end-to-end proof we
  ran for the gate itself with probe PR #2.
- After tagging: `git clone --branch v0.2.0` somewhere and confirm the
  skill loads.
- Skim one ADR (0004 is the richest) and confirm the recorded decision
  matches your memory of what we agreed — the ADRs are my rendering of
  our conversations, and you are the authority on them.
