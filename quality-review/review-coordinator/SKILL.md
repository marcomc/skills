---
name: review-coordinator
description: Coordinate an authorized scoped code review or remediation using one ledger, risk-selected checks and reusable evidence. Own the local quality decision when invoked directly or through pre-PR and PR-remediation entrypoints; do not start remote review or publish by default.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Review Coordinator

Minimize total model usage per completed change while preserving required
correctness, compatibility and validation. Extra prevention earns its cost by
catching demonstrated risks; fewer comments or faster completion alone is not
success. This is the sole owner of review planning, remediation and local exit.

## One owner and one run

If a calling workflow already has a coordinator, continue that same run. Do not
spawn another coordinator, invoke an entrypoint recursively or create competing
ledgers. Reviewers and workers return findings and evidence; they do not run
their own remediation, learning or publication loops. An explicitly invoked
specialist may retain its standalone behavior outside this composition.

Resolve requested scope, user behavior, repository instructions and validation
commands once. Support branch, commit/range, staged, unstaged and all-uncommitted
scopes; include the actual requested working-tree changes. Refresh only context
invalidated by changes. Use `$project-context-rebuilder` when context is missing,
not as an obligatory reread of a known project.

Before selecting coverage, write a finite scope contract in the ledger:

- objective and in-scope behaviors/files;
- explicit non-goals and intentionally unsupported input forms;
- a finite acceptance matrix covering positive, negative and ambiguous cases;
- required checks and the exact local/remote completion signal.

Treat a review item as actionable only when it identifies a reachable violation
of that contract or an established repository invariant, with a current-head
location and a reproducible consequence. A request to support an intentionally
unsupported form, broaden the objective, or add an unbounded variant is optional
scope and must remain outside the defect ledger unless the user changes the
contract. Reconcile that change as a new bounded scope before editing.

For a remote-feedback run, one replacement-head review is the result of one
frozen closure batch, not one individual fix or commit. Snapshot every current
actionable finding for the reviewed head, triage the complete set, and close all
confirmed findings that share the affected contract before asking for another
remote pass. Run focused checks during the batch and required integrated
validation only after its final change. Do not request a remote review for an
interim commit, a partial finding set, a single test addition, or ledger/docs
bookkeeping. Independent findings from a later review start the next normal
batch; they do not make the loop unsuccessful by count alone.

Keep one cumulative ledger outside the published diff, preferably in the Git
directory. Record scope/base, findings and stable families, selected checks,
evidence, unresolved questions and current outcome. Snapshot the loaded policy
files at entry and hold that revision for the run. User steering and higher-level
instructions still take precedence; reconcile their effect on plan and evidence.

Review permission, edit permission and publication permission remain separate.
An entrypoint preserves existing authorization, never broadens it. Report-only
mode returns required changes. Commits, pushes, PR requests and thread resolution
require the user's applicable authorization and are not local gate actions.

## Select coverage once

Use [routing.md](references/routing.md) to choose the smallest useful set of
checks from behavior and dependencies, not file extensions alone. Record the
reason for each selected check. The common baseline is:

- inspect the requested diff against the user's contract and nearby consumers;
- check correctness and compatibility, including applicable valid/failure cases;
- run required repository checks on the integrated result;
- obtain a final review of substantive changes and affected contracts, reusing
  current evidence. Use one independent report-only reviewer for substantive
  code changes when available; a tiny docs-only change can be checked locally.

Default to bounded prevention. Expand along affected contracts for uncertain
reachability, sensitive/durable side effects, recurrence or a demonstrated
missed sibling/regression. Do not launch every specialist or a repository-wide
search to satisfy a generic checklist. Explicitly requested deep reviews and
mandatory project gates retain their scope. Calibrate future depth using
[calibration.md](references/calibration.md); absent metrics are not zero cost.

Specialists are coverage lenses, not sequential gates. Use one reviewer with
the relevant lenses unless independent surfaces justify parallel work. Worker
briefs contain the contract, assigned diff, constraints and evidence references,
not the full chat. Keep shared contracts/files under one edit owner. Include
`$pre-pr-remediation-worker` for edit-capable workers, then integrate centrally.

## Evaluate evidence before scheduling work

Use [audit-evidence.md](references/audit-evidence.md) for content/environment
snapshots and actual execution evidence. Use [run-contract.md](references/run-contract.md)
and `scripts/evaluate_review.py` to identify reusable and outstanding checks.
The helper validates records, not semantic truth or test execution. Review the
coverage plan before treating its mechanical result as a local verdict.

Keep unchanged passing evidence. Product changes, changed requirements, relevant
dependencies, environment drift or new substantive feedback invalidate affected
proofs. Narrow reuse needs an explicit complete input map; uncertainty means
broader validation. Never relabel a stale result as current to avoid a check.
Ledger-only corrections require reference checks, not another code review.

## Close confirmed defects

Collect and triage the complete current feedback batch. Keep optional suggestions
outside the defect list. Confirm a failure against intended behavior before
editing; record evidence for false positives and intentional behavior.

For each confirmed defect use [defect-closure.md](references/defect-closure.md).
Fix reachable siblings within the implicated contract together, preserving
supported valid behavior. Keep the smallest coherent, testable batch; unrelated
cleanup or independent redesign belongs outside it. If closure exceeds the
authorized scope, report that boundary and a concrete split or decision instead
of declaring a partial fix complete.

Use `scripts/analyze_remediation_loop.py` and
[loop-health.md](references/loop-health.md) when findings/batches exist. Its
recurrence states and one recovery allowance are authoritative for remediation.
Do not reclassify a family to evade the stop. `BLOCKED` is a non-success outcome.
Do not impose a global review-round limit: a loop may continue while later
reviews identify independent, current, actionable defects. When a family becomes
`SUSPECTED`, complete and record its convergence sweep before another
replacement-head request. When it reaches `RECOVERY`, freeze remote requests,
reconstruct the smallest observable contract, map reachable siblings, and make
one coherent recovery change. Only recurrence after that completed recovery
produces `BLOCKED`; report the concrete redesign decision rather than treating
ordinary new findings as a reason to stop.

During edits run focused tests, then required integrated validation. Use
`$pr-remediation-coherence-audit` as the report-only final reviewer when cumulative
fixes need it; that pass also satisfies the common final review requirement.
A scope audit is needed before uncertain, cross-cutting or recurring fixes.
Do not add an identical general review after a sufficient independent audit.

## One local exit contract

- `READY`: no unresolved confirmed defects; required review, tests and applicable
  publication checks have current evidence; the integrated behavior and docs
  agree with the user's contract. Optional suggestions do not prevent readiness.
- `NEEDS_WORK`: triage, fixes, required coverage or evidence remain. In review-only
  mode report these actions without making edits.
- `BLOCKED`: a recurrence gate, operational failure or necessary user decision
  prevents continuation. Preserve progress and give the smallest next action.

A scope-plan approval is not a final quality verdict. Unknown or stale required
evidence cannot become `READY with gaps`. Optional checks may remain unrun but
must be visibly optional with reasons; never downgrade a required gate for cost.

Report local quality separately from remote review: `not_requested`, `pending`,
`clean_current`, `feedback`, or `blocked`. The provider adapter owns remote
evidence. A cloud 👍 is not a substitute for local proofs, and local readiness
does not satisfy a user request for a current cloud review. After remote feedback,
reenter this same run only for affected work; unchanged clean inputs need no new
local pass. Freeze the final product/docs before an authorized terminal review.

## Close the run once

Return scope/base, local status, remote status when applicable, resolved/open
defects, reused versus executed checks, remaining optional suggestions, and
observed usage coverage. Use [publication.md](references/publication.md) when a
release handoff or public output is in scope.

Record learning candidates during work. After the outcome, consolidate once
through `$codex-review-skill-autolearn` when appropriate. Prefer a regression
test or deterministic check, then the smallest relevant profile; keep generic
orchestration rules here. Do not mutate the active policy to manufacture a pass.
An urgent policy correction ends/rebaselines the run explicitly with affected
proofs reconciled. Learning never reopens unchanged product review by itself.

## Agent Learning Hook

When the integrated run produces a reusable finding or correction, invoke
`$record-agent-learning` once, or reference the capture already made by the
terminal learning step. Do not repeat capture in each composed skill.
