# ship

A Claude Code skill: deliver a milestone's worth of work as parallel,
independently reviewed pull requests that merge autonomously when no human
decision is needed, and escalate only genuine product, scope, security,
data, and release decisions.

The skill itself is [`SKILL.md`](SKILL.md). The design rationale — why
each mechanism exists and what was rejected — is
[`references/rationale.md`](references/rationale.md).

## When to use it

ship picks up where planning leaves off. Use it once you have already
spec'd the project, done the design thinking, and established the
project's engineering practices (CI, tests, branch rules, tracker) — and
you are ready to start implementing. It is not an init or scaffolding
tool: it assumes a project where the question is no longer *what to
build or how to set things up*, but *how to get a batch of well-defined
tasks built, reviewed, and merged with few human round-trips*.

## Install

The repo root is the skill directory. Clone it into your skills folder:

```bash
# personal (all projects)
git clone https://github.com/kristovatlas/ship ~/.claude/skills/ship

# or per-project
git clone https://github.com/kristovatlas/ship .claude/skills/ship
```

To track updates, keep it a clone (or symlink a checkout into place) and
`git pull`.

## Invoke

Ask Claude Code to ship a milestone or run a build wave — the skill
triggers on that intent, or invoke it explicitly with `/ship`. Before
promising a wave it runs a preflight (tracker access, CI commands, branch
rules, and above all an enforced review gate) and fails closed to
human-gated merges if anything is missing.

## The review gate

The skill assumes a deterministic review gate: a required CI check that
blocks merge unless diff-bound, severity-validated review artifacts are
present and current. This repo carries the reference implementation —
[`docs/process/review-gate.md`](docs/process/review-gate.md) (the process)
and [`scripts/review_gate.py`](scripts/review_gate.py) (the check, stdlib
only) — and dogfoods it: every PR to this repo passes a 4-leg review
battery (Claude and Codex, code review and security review each) through
that gate before merging.

## License

MIT — see [LICENSE](LICENSE).
