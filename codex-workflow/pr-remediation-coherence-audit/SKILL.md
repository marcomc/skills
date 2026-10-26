---
name: pr-remediation-coherence-audit
description: Audit cumulative pull-request remediation for ledger consistency, sibling risks, duplicated or obsolete code, regression coverage, and complexity growth. Use before editing a cross-cutting review finding, before publishing each replacement PR head, and before declaring a remediation loop complete. Run as a report-only review, including from a dedicated subagent; never edit the repository or perform Git/GitHub mutations.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# PR Remediation Coherence Audit

Determine whether the integrated fix closes the affected contract, preserves
valid behavior and earlier fixes, and avoids unnecessary complexity. Stay
report-only: never edit files, stage, commit, push, resolve threads or request a
review. The coordinator owns the ledger and implementation.

## Inputs and evidence

Obtain PR/repository identity, base and current head or working-tree snapshot,
authorized user behavior, finding/family IDs, the reachable-path map, relevant
prior remediations, changed paths, required validation and evidence references.
Use the compact ledger rather than rereading the entire chat. Discover missing
Git context read-only; report absent evidence as unknown.

Use `references/defect-closure.md` and `references/audit-evidence.md` from the
installed `$review-coordinator` for the common closure and evidence
contracts. This skill is a report-only component of the active coordinator,
not another gate or remediation loop. A missing companion/evidence is a gap;
never replace it with an assumed verdict. Its integrated pre-head review can
satisfy the coordinator's final review requirement; do not demand a second pass
under a different reviewer name. Preserve the pinned policy and compact evidence.

The coordinator should complete mechanical ledger checks first. Distinguish:

- `metadata_gaps`: missing IDs, references or measurements whose underlying
  evidence exists and can be checked without re-reviewing unchanged code;
- `validation_gaps`: tests not run, stale inputs, missing boundary coverage or
  unknown environment state; these require substantive work.

A matching digest or a well-formed ledger does not establish semantic correctness.
Inspect implementation and executable evidence; never rubber-stamp a supplied
claim that the map or patch is complete.

## Phases

### `scope`

Use before cross-cutting, recurring or uncertain changes. Check the falsifiable
invariant against user intent, then inspect the path map for reachable siblings
and exclusions. Include derived-output callers, reused artifacts, persistence,
recovery and installed variants when relevant. Ask which supported valid input
or prior fix a proposed guard could break. Return a coverage plan, not invented
passing execution results. Simple complete maps can be checked in `pre-head`.

### `pre-head`

Establish cumulative coverage before publication. Compare the complete PR diff
with the batch delta and relevant earlier fixes. Reuse previously reviewed,
unchanged inputs; inspect changed paths and dependent contracts. Widen the scope
when dependencies or prior evidence cannot be established.

Verify:

- all confirmed defects and required gaps are represented, classified and addressed;
- every confirmed sibling is fixed or excluded with concrete evidence;
- tests prove the failure and preserve supported valid behavior at the affected
  entrypoints, with required integrated/runtime validation on matching inputs;
- the final implementation does not invalidate earlier remediations;
- duplicated invariant implementations, obsolete helpers/configuration, stale
  tests and superseded recovery logic have been removed when no longer needed;
- product decisions, README/runbooks, changelog and planning state agree with
  the resulting behavior before the terminal cloud review is requested.

Ask independently for a missing reachable path or a regression introduced by
the correction. Supply an actionable counterexample or evidence-backed
exclusion, not hypothetical cleanup outside the authorized contract.

### `final`

When remote review is requested, reconcile local/remote head and new findings
with the pre-head
snapshot, substantive verdict and execution evidence. For local-only runs,
reconcile the final requested scope instead. If all relevant inputs
still match and no new substantive issue exists, reuse the pre-head PASS.
Check changed bookkeeping references without restarting the whole code audit.

If inputs changed or a new substantive issue appeared, invalidate affected
proofs and review the delta plus dependent contracts. A scope or dependency
uncertainty requires broader inspection. Any resulting product edit requires
validation and affected review; refresh the remote pass when the user requires it.
A quota, monitor failure or sick-loop stop is non-success and does not require
manufacturing a final PASS.

## Complexity checkpoint

Use measured branch/batch files, additions and deletions as investigation
signals, not acceptance thresholds. Check new helpers, conditionals, fixtures
and repeated validation/recovery paths when a batch adds roughly 200 lines,
a related finding recurs, or duplication is visible. For smaller changes,
perform a brief duplication and obsolete-code check.

Prefer one shared invariant implementation and case tables with common setup
when semantics match. Do not merge different failure behavior merely to lower
counts or repeat an entire audit to repair an additions/deletions measurement.

## Verdict

Return `PASS` for `scope` as plan approval only, when it covers reachable paths and
constraints. For `pre-head` and `final`, require current substantive evidence,
complete finding disposition and no unresolved required coverage/validation gaps.
Only the coordinator translates evidence into local `READY`/`NEEDS_WORK`/`BLOCKED`.
An audit PASS is an evidence record, not a remote or publication decision.
Metadata-only gaps still need correction before publication, but an unchanged
substantive verdict can be reused after checking those references.

```yaml
phase: scope | pre-head | final
verdict: PASS | REMEDIATE
head: <commit-or-working-tree>
snapshot_digest: <digest-or-unknown>
reused_audit: <prior-audit-reference-or-none>
substantive_verdict: PASS | REMEDIATE
metadata_gaps: []
validation_gaps: []
sibling_risks:
  uncovered: []
  excluded_with_evidence: []
compatibility_regressions: []
complexity:
  branch: {files: 0, additions: 0, deletions: 0}
  batch: {files: 0, additions: 0, deletions: 0}
  triggers: []
duplication_findings: []
obsolete_code: []
required_actions: []
```

Use `unknown` for unmeasured scope-phase values. Cite exact findings, paths,
commands and evidence references so the coordinator can act without repeating
this investigation. An evidence-free PASS is never a valid result.
