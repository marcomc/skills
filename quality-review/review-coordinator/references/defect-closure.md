# Defect Closure Protocol

Use for a confirmed review finding or an affected shared contract before the
first PR publication and each remediation batch. This procedure grants no
permission to edit, commit, publish, resolve threads, or start a cloud review.
In report-only mode, return findings and required checks without applying fixes.

## Establish the contract

State the smallest falsifiable user-visible condition, affected state and
lifecycle or trust boundary. Verify the reported scenario against current code,
supported runtime and the user's decisions. Preserve intentional behavior and
record evidence-backed false positives. Do not invent a broader product policy
to satisfy a reviewer.

Reconcile the finding with the existing family registry before assigning an ID.
Keep cause, invariant and boundary stable across paraphrased feedback; cite the
mechanism that makes it the same family. Different causes can share a contract
without consuming one another's recovery allowance. Classify the finding's
origin as pre-existing, a missed sibling, an introduced regression, independent,
or unknown; require evidence for causal claims.

## Map reachable paths before editing

Keep one compact matrix with path/entrypoint, lifecycle role, classification,
evidence and required coverage. Search symbols, serialized keys, normalized
representations, aliases and invocation/registration points. Inspect candidates
enough to prove reachability; a textual match is not a defect.

Cover relevant producers, validation/mutation, persistence and reload,
retry/recovery, consumers, wrappers and supported installed/runtime variants.
For derived output, inspect all callers and consumer entrypoints. For reused
directories or artifacts, inspect existing-target, resume and cache paths.
Record concrete reasons for exclusions and search evidence for empty categories.
Expand only along the implicated contract within the authorized scope.

Before edits, the remediation brief contains root cause, falsifiable invariant,
path/call-site matrix, required searches, compatibility and scope constraints,
and a test matrix. Reuse earlier proven map entries whose inputs still match.
An uncertain, cross-cutting or recurring defect requires a scope audit before
implementation; a simple complete map can be checked in the integrated audit.

## Prove both failure and compatibility

- Reproduce the reported defect at the implicated boundary.
- Identify siblings that can violate the same contract and the downstream
  effects of the proposed correction, including new early returns or guards.
- For each distinct confirmed path, prove the defect is prevented and supported
  valid behavior remains available. Use paired examples or parameterized case
  tables; avoid a Cartesian product of dimensions not implicated by evidence.
- Exercise normal, boundary, failure and recovery variants when reachable.
  Use the real entrypoint/consumer where isolated helper tests could mask a
  gap; include persisted and installed topology when they change behavior.
- Prefer shared invariant enforcement over parallel patches when that removes
  real duplication. Do not merge different failure semantics just to reduce
  lines or add abstractions without a demonstrated caller/contract benefit.

## Integrate and challenge once

Apply one coherent batch for all confirmed siblings. A reachable sibling cannot
be deferred while its path-only fix is presented as complete. Refresh affected
searches and tests, update exclusions, and reconcile the final implementation
with the original brief. Run targeted checks during edits, then the required
integrated repository gate on the stable batch.

Give the independent reviewer the user contract, current code/diff, map and
evidence references. Ask it to discover an omitted reachable path, a supported
valid case rejected by the change, or an earlier fix invalidated by it. Do not
ask it merely to confirm a supplied PASS conclusion.

Close substantive findings before publishing, including cumulative docs and
release-policy coherence. New code or evidence gaps trigger a focused review of
the delta and affected contracts. Unchanged inputs and a corrected ledger entry
do not require another full-code review. Reuse requires the evidence rules in
[audit-evidence.md](audit-evidence.md), never a claim that green tests imply
semantic completeness.
