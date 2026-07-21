# Why ship works this way

Background for the `ship` skill. None of this is needed to run the procedure. It is here for when you are deciding whether to change the procedure.

## The core bet

LLM output is non-deterministic, and long sessions accumulate context pollution. The orchestration around the model should not inherit those properties. Make every step that can be exact and machine-checked exact, and contain the fuzziness to the model's actual output. The rest follows: deterministic checks and a review gate decide whether code is safe to merge, the human decides the product questions a check cannot, and the model does the building in between.

## What it replaced

An earlier serial process built one PR at a time, ran the review battery, applied fixes, and waited for a human to merge every PR. It produced reliable PRs and had two costs.

The first was that work serialized on human merge latency even when no human decision existed. Faros AI's 2026 engineering benchmarks (as reported in industry coverage; we did not audit the methodology) found AI-authored PRs wait several times longer for a first review than the review itself takes, so the queue dominates cycle time. Treat the multiple as a heuristic; the direction of the effect is what the design leans on. The second was that the human was asked to review the wrong artifact. Many maintainers do not want to read diffs. They want to make the product and design calls only they can make.

ship keeps the per-PR review rigor and changes what surrounds it: parallel lanes, autonomous merges when nothing needs a human, and one decision document per wave.

## Design decisions and alternatives

Parallelism via git worktrees, one checkout per lane. Shared-checkout agents corrupt each other's branch state, and worktrees are the standard fix. The practical ceiling is 3 to 4 concurrent lanes before coordination overhead and machine resources dominate.

Small PRs. A vendor-published analysis of 1.5 million pull requests reported PRs in the 200-to-400-line range with roughly 40 percent fewer defects and about three times faster approval than larger ones. We adopted the range as a heuristic without auditing the study; the size cap earns its place independently by keeping review artifacts and touch-sets small. Wave scoping enforces it.

The plan as an executable artifact, following spec-driven development. Writing the touch-set down before building lets a mechanical check flag scope creep, and lets the planner prove lanes are independent before spending tokens on them.

Stacks for dependent work. When two tasks share a surface they cannot be parallel lanes. Stacking, branch on branch, lets the dependent work proceed without waiting for each merge, which is the latency the whole skill removes.

Merge queue. Serial merges plus a post-merge check catch most combination breakage. At higher wave cadence, a native merge queue that tests each PR against the future base state mechanizes the same rule. Adopt it when the manual protocol starts to hurt.

Rejected: making the reviewer itself deterministic through voting, pinned prompts, or structured verdicts as the primary control. The reviewer is a language model and will vary. Making the enforcement deterministic is the more reliable lever. See `docs/process/review-gate.md` for the reference implementation.

## The human interface

The wave report exists because first-review latency is the dominant cost, and the human's scarce attention should go to the calls only a human can make while the review battery reads the diffs. Ordering it decisions first, conversations second is deliberate: those are the parts a human can act on.

## Open questions to resolve per project

The escalation-list boundary is the biggest lever and the thing most worth tuning per project. Start conservative, escalating more, and relax as trust builds.

Stacks: manual branch on branch, or a tool.

Merge queue: on from the start, or added when cadence justifies it.

## Changelog

Record process versions here as the skill evolves.

- **v0.1 (2026-07-21):** extracted into a dedicated repo
  (kristovatlas/ship). Added the review-gate reference implementation
  (`scripts/review_gate.py`, `docs/process/review-gate.md`), ported from
  the somnus implementation with two changes: PRs merge straight to `main`
  (no dev branch), and the review-model floor (Claude Opus 4.8 / Fable 5
  or better; Codex GPT 5.6 Sol or better) is enforced deterministically by
  the gate via an allowlist. The repo dogfoods its own protocol: every PR
  runs the 4-leg battery through the gate.
