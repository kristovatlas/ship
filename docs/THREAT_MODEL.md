# Threat model

One page. Every PR must assess its impact against this document and
update it **in the same PR** when the impact is real (rule: Kristov,
2026-07-21; the battery's security legs check both halves).

## What this repo actually is

The product is instructions executed by other people's coding agents.
Someone who installs ship wires this repo's markdown into an agent
holding their GitHub credentials, merge rights, and codebase. SKILL.md is
functionally remote code; `git pull` is the update channel.

## Assets, most valuable first

1. **Integrity of `main`** — what consumers' agents ingest and what the
   reference gate script ships as.
2. **Integrity of the enforcement path** — the gate script, its CI job,
   and the ruleset that makes it binding on this repo's own evolution.
3. **Confidentiality of repo contents** (private repo) and of the
   short-lived CI tokens.
4. **Assurance signals** — scanner results, review artifacts, coverage
   numbers that humans rely on without re-deriving.

## Threat 1: malicious or degraded skill content reaching consumers

The primary threat. An attacker (or an unreviewed mistake) lands a
subtle instruction change on `main` — a weakened escalation list, an
exfiltration step in the wave protocol, a relaxed dependency rule — and
every consumer pulls it.

**Controls:** the full battery + gate on *every* PR including docs-only
(a docs carve-out here would be the vulnerability); diff-hash staleness
binding with merge-base binding; human escalation on the gate's own
trust boundary; account security of the sole maintainer (2FA); tags for
consumers who prefer pinning to tracking `main`.

**Residuals:** artifact genuineness (the gate proves judging happened,
not that it was honest — `docs/process/review-gate.md`); a compromised
maintainer account bypasses everything (GitHub-level, out of repo scope).

## Threat 2: subverting the enforcement path

A PR that weakens the gate instead of passing it. **Controls:** CI runs
the base branch's copy of the gate script; changes to
`.github/workflows/` or `scripts/review_gate.py` always escalate to the
human (a skipped required check reports *success*, so this rule has no
red-flag fallback); the gate is stdlib-only so no third-party code runs
in the enforcement job. **Residuals:** as documented in the process doc
(hash-exempt `docs/reviews/`, ci.yml gate-job editability).

## Threat 3: dev/CI supply chain (dev-facing only)

Pinned actions download scanner binaries at run time without checksum
verification; package transitives float past the 7-day cooldown
(ADR 0004). A compromised scanner or transitive executes in CI.

**Why this does not reach consumers:** those jobs are `contents: read`
with `persist-credentials: false` and no secrets. A compromised binary
can lie in its report, fail the job, or exfiltrate a short-lived
read-only token (repo confidentiality) — it cannot push, approve, or
merge. The consumer-integrity path (threat 1) runs exclusively through
the hermetic gate job, the ruleset, and human escalation — none of which
execute downloaded code. The cost of a lying scanner is degraded
*assurance* (asset 4): a missed secret or dead link, not modified code.

## Out of scope

- Security of consumers' own repos and of the projects ship is run
  against (the skill's escalation list is their control, not this
  repo's).
- The upstream models' behavior (Claude, Codex) — reviewer trust is
  bounded by the two-model battery design, not eliminated.
- GitHub platform compromise.
