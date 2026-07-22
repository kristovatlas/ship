# Engineering standards

The practices this repo holds itself to, what enforces each, and where
the reasoning lives. Decisions are recorded as MADR-format ADRs in
`docs/adr/`; a PR that changes a recorded decision updates the ADR in the
same PR (checked by the review battery).

| Practice | Enforced by | Rationale |
|---|---|---|
| Deterministic review gate on every PR, no exemptions | `review-gate` required check (ruleset) | ADR 0001, `docs/process/review-gate.md` |
| Review-model floor (Claude Opus 4.8/Fable 5+; Codex GPT 5.6 Sol+) | `ALLOWED_MODELS` in the gate | ADR 0002 |
| Main-only trunk; versions cut as tags | ruleset + convention | ADR 0003 |
| Hermetic (stdlib-only) gate script | battery + human escalation on gate changes | ADR 0004 |
| Exact dependency pins, ≥7-day release cooldown per pin | `requirements-dev.txt` review + battery | ADR 0004 |
| New dependency = security escalation | ship escalation list | ADR 0004, SKILL.md |
| Secret scanning, CVE audit, link check | `security-hygiene` + `links` CI jobs | ADR 0004 |
| Lint/format/types: ruff + mypy strict | `lint-type` CI job | `pyproject.toml` |
| Branch-coverage floor (fail_under just below measured; never lowered to pass a PR) | `tests` CI job | ADR 0005 |
| Patch coverage + test quality on new code | battery correctness legs | ADR 0005 |
| Threat-model impact assessed per PR; doc updated in-PR when real | battery security legs + PR note | `docs/THREAT_MODEL.md` |
| Wave plans with predicted touch-sets; overflow recorded | orchestrator + battery | SKILL.md Phase 2/3 |
| Wave reports committed in-PR post-convergence, pre-attestation | convention (delta-noted) | SKILL.md Phase 5 |
| Docs describe what is, never an intended end-state | battery correctness legs | SKILL.md guardrails |

Precedents worth knowing: the touch-set gate caught an unplanned file in
PR #4 after `git add -A` swept in a local scratch file (staging is
explicit-path since); the battery caught its own fix hollowing out a
regression test in PR #1 round 4 (mutation checks — delete the control,
the test must fail — are now standard review practice for test changes).
