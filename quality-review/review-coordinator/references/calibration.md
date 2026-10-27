# Calibrate prevention from observed outcomes

The objective is lower total usage per completed change at the same quality
requirements. Local analysis and cloud review both count; waiting time is a
separate metric. Do not optimize round count by accepting defects or relabeling
required checks as optional.

Record with the run: selected depth (`bounded` or `expanded`), concrete risk
reasons, selected profiles/checks, policy revision and observed model/effort.
Use the existing ledger `cost_events` described in [loop-health.md](loop-health.md)
for non-overlapping observed increments. Add compact `review_outcome` metadata:

```json
{
  "review_outcome": {
    "depth": "bounded",
    "risk_reasons": ["single parser contract with known consumers"],
    "policy_digest": "<recorded-digest>",
    "model": "<observed-model>",
    "effort": "<observed-effort>",
    "local_status": "READY",
    "remote_status": "clean_current",
    "reused_check_ids": ["parser-review"],
    "executed_check_ids": ["repo-gate"]
  }
}
```

The example is a completed outcome, never defaults to insert before execution.
If no cloud review was requested, record `not_requested`. Keep unavailable model,
usage and duration values absent. Record cloud review requests separately from
local token counters; do not infer their token cost from comments or elapsed time.
Cache input is part of total input, not an extra token total.

Within a run, a reproduced missed sibling or remediation regression expands the
implicated contract immediately. A recurrence follows the existing health gate.
Independent defects and stylistic suggestions do not alone justify expansion.

After completion, compare equivalent changes using policy/model/effort, risk,
scope and available metric coverage. Inspect escapes, introduced regressions,
false positives and unsupported valid inputs alongside time and usage. A few
real comparable PRs can expose waste, but cannot prove a universal percentage or
unchanged defect-detection quality. Forked/cumulative counters are not additive.

Promote a deeper check when an actual escaped defect demonstrates its value.
Move a repeatable check into tests/lint where practical. Remove duplicate passes
when their coverage and dependency evidence are already supplied elsewhere.
Reduce unique preventive coverage only after matched replay/real results support
it without worse detection or compatibility. Keep the existing minimum until
then. Missing telemetry never triggers an automatic cheaper policy.

Apply policy changes to a subsequent run and retain the prior revision for
comparison. No scheduler, automatic model downgrade or claimed financial savings
is implied by collecting these records.
