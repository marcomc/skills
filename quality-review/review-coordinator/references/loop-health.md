# Loop Health Reference

Read when creating/reconciling the ledger or interpreting analyzer output.
Store one cumulative ledger per PR outside the published tree, preferably under
its Git directory; retain it across task continuations.

## Contents

- [Stable identity](#stable-identity)
- [Ledger schema](#ledger-schema)
- [States and contract attention](#states-and-contract-attention)
- [Recovery](#recovery)
- [Cost accounting](#cost-accounting)

## Stable identity

Register each family with a persistent `id`, normalized root cause, falsifiable
invariant and lifecycle/trust boundary. Before assigning another ID, compare the
mechanism with existing families and explain whether it matches. Never split a
family by filename, reviewer wording or round to reset recovery history.

Findings, sweeps, batches and recovery markers reference `family_id`. Optional
free-text cause/invariant/boundary descriptions that differ from the registered
fingerprint require `family_evidence` explaining equivalence. The analyzer
checks references, not semantic truth; the coordinator and independent auditor
must verify that evidence. It never merges fuzzy matches automatically.

A `contract_id` can connect distinct families across a shared observable
behavior. Those families retain separate recovery allowances. Sharing a file or
technology alone is insufficient for either grouping.

Legacy ledgers remain supported with the original exact normalized triple.
Exact legacy records join a matching registered fingerprint. Before changing
legacy wording, assign IDs to the complete family history, including sweeps,
batches and recovery markers. Paraphrased historical records need explicit
family assignment and evidence, never a silent reset or automatic fuzzy merge.
The analyzer warns when legacy text identity is still in use.

## Ledger schema

```json
{
  "contracts": [
    {"id": "catalog-loading", "invariant": "Import and restore share bounded loading"}
  ],
  "families": [
    {"id": "load-budget", "contract_id": "catalog-loading",
     "root_cause_class": "failed attempts bypass cumulative budget",
     "invariant": "Each failed load consumes the shared attempt budget",
     "boundary": "catalog load"}
  ],
  "findings": [
    {"id": "f1", "review_round": 1, "family_id": "load-budget",
     "locations": ["import"], "disposition": "defect", "origin": "pre_existing",
     "remediation": "Charge before decode", "regression": "Failed-load entrypoint test"}
  ],
  "convergence_sweeps": [],
  "remediation_batches": [
    {"id": "b1", "after_review_round": 1,
     "families": [{"family_id": "load-budget"}],
     "changed_locations": ["import", "restore"], "changed_lines": 40,
     "finding_ids": ["f1"], "validation_ids": ["v1"],
     "required_commands": ["python3 -m unittest discover -s tests"]}
  ],
  "recovery_epochs": [],
  "validation_runs": [
    {"id": "v1", "scope": "full", "command": "python3 -m unittest discover -s tests",
     "status": "passed", "snapshot_digest": "<validated-input-digest>",
     "duration_seconds": 30}
  ],
  "cost_events": []
}
```

Use positive review rounds and lowercase IDs containing letters, numbers,
dots, underscores or hyphens. Finding disposition is `defect`, `false_positive`
or `intentional`; only defects drive recurrence. Keep evidence for exclusions.

Origin is `pre_existing`, `missed_sibling`, `remediation_regression`,
`independent` or `unknown`. The latter is the default when origin is unproven.
Missed siblings, introduced regressions and independent findings require
`origin_evidence`, such as prior map coverage, parent/batch reproduction or an
implementation comparison. Do not assume that a later finding was introduced
by the previous fix.

Retain the closure map, specification and substantive audit references with the
batch. Use [audit-evidence.md](audit-evidence.md) for mechanical ID/reference
checks and input fingerprints. Unknown old validation is not a passing result.

## States and contract attention

Run `scripts/analyze_remediation_loop.py <ledger.json>` before selecting a batch
and before requesting a replacement-head review. The highest family state wins:

- `NORMAL`: no family crosses another threshold.
- `SUSPECTED`: at least two distinct rounds in one family, or at least three
  defects spanning at least two locations.
- `RECOVERY`: at least three rounds, a recurrence after a convergence sweep,
  or recurrence plus sibling spread and at least two remediation batches.
  An unfinished recovery also remains here; resume that epoch.
- `BLOCKED`: a family recurs after its recovery epoch, or more than one epoch
  was recorded. This is non-success; stop automatic remediation and publication.

`convergence_attention` is a separate advisory: a registered contract has at
least two distinct defect families spanning at least three rounds and is still
active in the latest defect round. These deliberately conservative initial
thresholds do not change family state or claim a pathological loop. Inspect the
contract's missed paths, changed policy and simplification options before
publishing another partial patch; record the conclusion. Calibrate with actual
outcomes before changing the thresholds.

## Complete a suspected-family sweep

After a `SUSPECTED` family's bounded closure, record the actual convergence sweep
with `completion_version: 1`, `family_id`, `after_review_round`,
`status: completed`, `head` and
`validation_evidence`. It returns `NORMAL` with `completed_convergence_sweep: true`
only when the sweep covers the latest defect and no recovery/block condition
exists. The local gate still requires resolved defects and current review/tests.
An unfinished or undocumented sweep does not clear the signal. Legacy sweep
`status` values may be free-text notes; without `completion_version: 1` they
remain historical markers and never imply verified completion. Reconcile genuine
existing evidence into the versioned record rather than inferring it from prose. Do not manufacture
a recovery epoch merely to clear resolved history; this sweep uses no recovery
allowance. A later recurrence after it enters `RECOVERY`, preserving history.

## Recovery

Allow exactly one epoch per family. Freeze new review requests; reconstruct its
history, define the smallest observable contract, map reachable siblings, and
prefer coherent shared enforcement or simplification over accumulated guards.
Use focused checks during edits, then the required integrated validation and
pre-head audit for the complete recovery head. Preserve authorized scope.

Record an epoch with `family_id`, `after_review_round` and `status: in_progress`.
After integration and validation, update that same record to `status: completed`
with `head` and `validation_evidence`. Do not append another epoch to record its
completion. A single completed epoch without a later defect reports `NORMAL`
and `completed_recovery_epoch: true`; later recurrence still reports `BLOCKED`.

A legacy epoch without completion evidence is unfinished. Reconcile genuine
existing proof rather than starting a second recovery or inventing success.
Existing `replacement_head` and `validation` fields remain accepted aliases
for `head` and `validation_evidence`; existing batch labels retain compatibility.
On a block, retain the ledger/head and report the family, rounds, remaining
feedback and smallest redesign, rollback or PR split needing user direction.

## Cost accounting

Optional `cost_events` contain a unique `id`, category `local`, `audit`, `test`
or `cloud_wait`, and observed `duration_seconds`, `input_tokens`,
`cached_input_tokens`, or `output_tokens`. Record non-overlapping per-event
increments, never repeated cumulative counters or inherited fork totals.
Cache tokens are part of input, not an additional total. Unknown fields stay
absent; finite non-negative values and unique IDs are checked by the analyzer.

`costs_by_category` reports recorded values, not a bill or necessarily complete
coverage; `observed_events` counts how many events supplied each metric. Do not
add overlapping durations to infer elapsed wall time. Legacy
`validation_seconds` totals recorded durations and is not additive with test
cost events describing the same executions. Compare new families, missed
siblings, introduced regressions, re-opened files and time to a current clean
result; fewer rounds alone does not establish quality.

Keep the fast path cheap: maintain a compact ledger, load references only when
needed, share relevant evidence rather than entire chats, and run required full
validation on integrated changes rather than partial edits. Budget limits never
permit accepting a known defect or claiming an unobserved clean result.
