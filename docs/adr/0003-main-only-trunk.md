# Main-only trunk development

- Status: accepted
- Date: 2026-07-21
- Deciders: Kristov Atlas

## Context and problem statement

somnus (where the ship process was proven) uses a `dev` branch dogfooded
ahead of `main`, with release PRs promoting between them. Does this repo
need the same structure?

## Considered options

1. PRs straight to `main` (chosen).
2. somnus-style `dev` → `main` with release PRs.

## Decision outcome

Option 1. This project is not very complex (Kristov, 2026-07-21): the
deliverable is a skill document plus one script, there is no deployment
to soak-test on a pre-release branch, and every PR already passes the
full battery. A release branch would add a promotion ceremony with
nothing to promote.

### Consequences

- Good: one gate configuration (`--base origin/main`), no release-PR
  variant, simpler mental model.
- Bad: no staging area — anything merged is immediately what consumers
  `git pull`. Compensated by the gate on every merged PR and by the tag
  convention: skill versions are to be cut as tags (SKILL.md carries its
  version) so consumers can pin instead of tracking `main`. **No tags
  exist yet** — the first (v0.2.0) is a release decision escalated in
  the wave-2 report; until it lands, tracking `main` is the only option.
- Revisit if: release cadence or multi-maintainer coordination ever makes
  a soak branch earn its ceremony.
