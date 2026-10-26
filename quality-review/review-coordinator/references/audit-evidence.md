# Audit Evidence and Reuse

Use when preparing a pre-head audit or reconciling a remote result with prior
local evidence. The helper performs mechanical checks; it cannot establish
semantic coverage, prove a test actually ran, or approve code.

## Capture stable inputs

Freeze substantive edits while capturing inputs and running the integrated
gate. Store snapshots and the ledger outside the product tree, preferably in
the repository's Git directory. Resolve the base to the intended review base;
use the same base for comparison.

```bash
python3 <skill-dir>/scripts/prepare_remediation_audit.py \
  --repo . --base <base-commit> \
  --environment '<observed-toolchain-and-fixture-revision>' \
  --input <ignored-or-external-dependency-file> > <git-dir>/inputs-before.json
```

`--input` is optional and repeatable. Declare every relevant ignored or external
dependency, such as a private override or generated runtime input; do not put
its content or credentials in the environment label. The label must identify
observed runtime/toolchain/fixture versions, not just say `local` or `production`.
If external state cannot be fingerprinted or independently reconfirmed, its
evidence cannot be reused. The tool fails on missing explicit inputs, unsupported
directory links/submodules and unreadable files; inspect these dependencies
explicitly instead of treating that failure as a match.

The snapshot covers all tracked working files and non-ignored untracked files,
file permissions, symlink identity and file targets, base commit, environment
identity and additional input hashes. It stores hashes rather than file content.
Unchanged content before and after committing can match despite a different
HEAD. Final publication still requires the committed/pushed tree to match the
validated working tree; a dirty checkout cannot prove the published commit.

Run the required tests and capture command, exit result, environment and evidence
location. Snapshot again afterward; unexpected input changes invalidate the run
until inspected and revalidated. This is not an atomic filesystem snapshot:
concurrent edits or live state changes require recapture and affected checks.

## Legacy batch preflight

For a new coordinator run, prefer the common evaluator in
[run-contract.md](run-contract.md). It supports per-requirement dependency maps
and replaces the legacy batch preflight for the same coverage; do not run both
as independent gates. The following CLI remains for existing batch ledgers and
requires whole-snapshot validation. Deliberately reconcile records when migrating.

For legacy batches, give findings, batches and validations explicit IDs. Example:

```json
{
  "findings": [
    {"id": "f1", "family_id": "load-budget", "review_round": 1,
     "remediation": "Charge the shared loader counter before decode",
     "regression": "Failed import and restore each consume one attempt"}
  ],
  "remediation_batches": [
    {"id": "b1", "after_review_round": 1,
     "families": [{"family_id": "load-budget"}],
     "finding_ids": ["f1"], "validation_ids": ["v1"],
     "required_commands": ["python3 -m unittest discover -s tests"]}
  ],
  "validation_runs": [
    {"id": "v1", "scope": "full", "status": "passed",
     "command": "python3 -m unittest discover -s tests",
     "snapshot_digest": "<digest-from-the-validated-snapshot>"}
  ]
}
```

This is the batch fragment; retain the family/contract registry and all previous
findings in the cumulative ledger. Do not synthesize success fields or retrofit
unknown historical evidence as passed. Legacy ledgers remain readable by the
health analyzer; add batch IDs and execution references deliberately before
using the stricter audit preflight.

```bash
python3 <skill-dir>/scripts/prepare_remediation_audit.py \
  --repo . --base <base-commit> \
  --environment '<observed-toolchain-and-fixture-revision>' \
  --input <ignored-or-external-dependency-file> \
  --compare <git-dir>/inputs-before.json \
  --ledger <git-dir>/ledger.json --batch b1 > <git-dir>/inputs-after.json
```

Exit 0 means the requested mechanical checks passed; it is not an audit PASS.
Exit 1 reports changed inputs, `metadata_gaps`, or `validation_gaps`; exit 2 is
invalid input or an operational error. Correct metadata and rerun the preflight.
Stale or failed tests and absent required commands need actual validation.

## Reconcile the final result

The pre-head auditor records the snapshot digest, reviewed scope, path map,
required coverage, validation references and substantive verdict. After remote
review, verify local/remote head, new actionable feedback and these inputs.

- Matching inputs plus the existing substantive PASS and complete current
  execution evidence permit reuse. The final phase is a reconciliation, not
  another whole-PR search for the same evidence.
- Ledger-only corrections require checking the changed references and claims.
  They cannot convert missing test execution or coverage into a metadata issue.
- Changed product code, docs, required inputs or environment invalidate their
  evidence and dependent contracts. The helper returns changed paths, not a
  trusted dependency graph: a reviewer must bound the delta or widen the audit.
- A new substantive finding invalidates the relevant verdict even if file
  fingerprints match. Fix, validate and audit before requesting a new cloud pass.

Required repository gates and runtime proofs remain required. Reuse saves
duplicate analysis and unchanged checks, never the evidence needed to establish
correctness on the final published state.
