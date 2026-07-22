---
name: ship
description: Deliver a milestone's worth of work as parallel, independently reviewed pull requests that merge autonomously when no human decision is needed, and escalate only genuine product, scope, security, data, and release decisions. Invoke when the user asks to ship a milestone or run a build wave across several independent tasks.
version: 0.2.0
---

# ship

Build a set of independent tasks in parallel, each as its own reviewed PR. A PR merges without a human when the change is routine, and pauses for the human only on decisions a human has to make. This skill assumes a deterministic review gate is already in place (a reference implementation ships alongside this skill: `docs/process/review-gate.md` and `scripts/review_gate.py`); it orchestrates work through that gate.

## When to use

Invoke explicitly when the user has a milestone or a batch of tasks and wants them built with few round-trips. For a single small change, skip Phases 0 and 1, write a one-lane plan (a predicted touch-set is still required, since Phase 3 gates on it), run Phases 3 and 4, and deliver a shortened Phase 5 handoff: what shipped, how to verify it, and any decisions or judgment calls.

## Preflight (required before promising a wave)

Resolve and record, in the plan file:

- the base branch and release branch
- the tracker and whether you can write milestones/labels and close items
- the CI commands and required checks
- **the review gate**: a deterministic required check that blocks merge unless review artifacts are present, complete, current, and clear of blocking findings (see `docs/process/review-gate.md` for the pattern and a reference implementation)
- branch rules: PR required, required checks enforced, your merge permissions
- git worktree support

**Fail closed:** if any of these is missing, and above all if there is no enforced review gate, autonomous merging is prohibited for the whole engagement. Build and review as below, but every merge escalates to the human until the gate exists and is a required check.

## Phase 0: Shape the milestone

The milestone is where the human's intent enters the system. Do not derive it from the backlog on your own. Have a real conversation about what the human wants to focus on next, and what they are willing to test once it is built. Record the settled set in the tracker (a milestone or label). From then on the milestone is a contract you may deliver autonomously. New items enter only through the same conversation.

## Phase 1: Scope a wave

Take a slice sized for one wave: at most 3 to 4 lanes, each targeting a small PR of a few hundred lines. Split or defer anything larger.

## Phase 2: Write the independence plan

Before any code, produce a plan file (convention: `docs/waves/<date>-wave-<n>.md`, or wherever the project keeps process records) recording, per lane: the task, an approach sketch, and a predicted touch-set (files, schemas, tests, docs).

- Touch-sets must be pairwise disjoint. Overlap means the tasks are not independent.
- Any file multiple lanes would edit is a serialized resource. Either one lane owns all changes to it, or the shared changes become their own integration PR that passes the complete Phase 3/4 cycle. Never modify reviewed content during a merge: an edit at merge time either invalidates the diff-bound review artifacts or lands unreviewed.
- Dependent tasks cannot be lanes in the same wave. Build them as a stacked chain instead: each branch off the previous, reviewed separately, merged in order.
- Surface any known product decision to the human now, batched, so lanes do not stall mid-flight.

## Phase 3: Build each lane

Run every lane in its own git worktree: build, tests, and the review battery all inside that worktree, so lanes never corrupt each other's checkout.

- Run the review battery the project's review gate requires. Where the project defines none, the floor is one correctness-focused and one security-focused pass; use two different models per pass when more than one is configured, and record the models used in the artifacts either way. Blocking thresholds match the gate: validated security critical/high and validated P1 correctness findings must be fixed; lower-severity findings are recorded and dispositioned but do not block.
- Severity-validated re-run: adversarially validate any claimed blocking finding (is it real, is the severity right) before acting. If validated, fix it and re-run the whole battery on the new head. Loop until a pass yields no new validated blocking findings. Record dismissed or invalidated claims with reasons.
- Touch-set gate: before opening the PR, diff the lane's actual files against the plan. Overflow pauses the lane; re-plan or record the scope change explicitly.

## Phase 4: Merge gate

A lane merges without human review only when all of these hold:

1. Deterministic checks green, verified immediately before merge, and the review battery complete with no unresolved validated findings.
2. The touch-set matched the plan, or overflow was re-planned.
3. Nothing on the escalation list below applies.

Then merge one lane at a time. Before each merge, the lane must be current against the base branch: if the base advanced since the lane's checks ran, update the branch and let checks re-run against the combined state (with a diff-bound review gate, the update restales the review artifacts and forces re-review, which is the point; branch protection's "require branches up to date" makes this automatic). After each merge, wait for the post-merge check on the base to go green before merging the next lane. If a post-merge check goes red anyway: stop the wave, fix forward or revert through a normal gated PR until the base is green, and record the incident in the wave report. At each merge, close the lane's linked tasks yourself: merges to a non-default branch usually do not fire the tracker's auto-close keywords. Remove the lane's worktree once its PR is merged or abandoned.

An escalation pauses its own lane while the human responds. The other lanes keep building and merging; never stall the wave on one lane's question.

Escalation list, always wait for the human and merge only after the conversation:

- Product or user-visible behavior choices that are not bug fixes: changed meaning of anything users see, removed or renamed concepts, new flows.
- Scope: descoping, dropping items, new milestones.
- Security posture: any change to the threat model, new attack surface, new dependency, auth or network change.
- Data: schema migrations beyond additive-nullable, anything touching existing user data, destructive operations.
- Releases: release-branch PRs, tags, release notes.
- The gate's own trust boundary: any change to CI config or the review-gate script. A PR can neuter its own gate, and a skipped required check reports success.

## Phase 5: Wave report

When the wave lands or stalls, deliver one document to the human as a message. If the project keeps process records, also commit it alongside the plan file — in the wave's final PR, after the battery converges but before attestation, so the attested hash covers it (recorded with a standard post-review delta note; the report is prose about the process, so the never-leg-reviewed impurity is the same accepted residual as any delta note). Do not put reports in the hash-exempt artifacts path: that zone is for machine-checked attestations, and the report is a document humans act on. Order the report:

1. Decisions needed: the genuine ones, batched, each with a recommendation, answerable inline.
2. Conversations worth having: judgment calls you made autonomously that deserve a human sanity-check, and things worth watching in use. This is the human's primary read and stands in for reading diffs.
3. What shipped: a prose changelog per lane, no code.
4. Verification asks: the specific real-world checks that prove each change works.

## Changing this protocol

Read `references/rationale.md` before modifying this skill. It records why each mechanism exists and what was rejected; do not load it during normal execution.

## Version and source

This is ship v0.2.0. If you are reading a copied SKILL.md rather than a
clone, the latest version (and the review-gate reference implementation,
rationale, and changelog) lives at https://github.com/kristovatlas/ship.

## Guardrails

- A threat-model impact note on every PR.
- The base branch stays green. Merges are serial with post-merge verification.
- Audit dependencies before install. Never add one silently.
- Docs describe what the change actually does, never an intended end-state.
- Coverage floors hold on new code.
