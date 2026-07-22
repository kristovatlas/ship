# Review-model floor enforced by allowlist

- Status: accepted
- Date: 2026-07-21
- Deciders: Kristov Atlas

## Context and problem statement

Review quality depends on reviewer capability. "Use a strong model" is a
convention that drifts silently; a weaker model could produce a plausible
artifact that passes every structural check.

## Considered options

1. Deterministic allowlist in the gate (chosen).
2. Record the model, enforce by convention/spot-check (somnus behavior).

## Decision outcome

Option 1. `ALLOWED_MODELS` in `scripts/review_gate.py` — Claude legs:
`claude-opus-4-8`, `claude-fable-5`; Codex legs: `gpt-5.6-sol`. The floor
is "these or better": a better model is admitted by editing the
allowlist, which is a gate-script change and therefore always escalates
to the human (`docs/process/review-gate.md`).

### Consequences

- Good: the floor cannot drift silently; vendor crossover (a Claude model
  attesting a codex leg) is rejected.
- Bad: every new model adoption costs an escalated PR — deliberate: model
  choice for the review battery is a security-posture decision.
- Residual: the gate trusts the `model` string; a fabricated value is
  part of the artifact-genuineness residual (ADR 0001).
