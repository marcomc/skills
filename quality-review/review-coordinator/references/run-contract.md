# Shared run and evidence contract

The coordinator maintains this optional extension of the existing cumulative
ledger. The family analyzer still reads legacy ledgers. Before using this stricter
gate, reconcile historical dispositions and evidence explicitly; never invent
past execution or automatically mark legacy fixes resolved.

## Plan once

`review_run` contains `id`, `depth` (`bounded`/`expanded`), `risk_reason`,
`policy_files`, `policy_digest`, `coverage_reviewed` and `requirements`.
Store absolute local paths or paths relative to the ledger for evidence/policy
files. The ledger and evidence belong outside the published diff. Policy files
include the loaded coordinator, entrypoint, applicable references/profiles and
governing repo instructions; record only actually relevant loaded resources.

Each requirement has:

- `id`, `kind` (`review`/`validation`), `coverage`, explicit `required` boolean;
- `command` for validation, including actual arguments/environment identity;
- `feedback_revision`: start at zero and increment for new substantive feedback
  affecting this requirement, even when code is unchanged;
- optional `inputs`: exact repository-relative files or directory prefixes ending
  in `/`; omit or use null for the full snapshot. No globs or empty selection;
- `dependency_evidence` for narrow inputs: reference a checked map including
  callers, configs, fixtures, generators and directory membership where relevant;
- `independent: true` for a required independent review;
- `optional_reason` when a check is optional, never a substitute for a repo gate.

Require a correctness review and actual applicable validation even for a tiny
scope. A docs-only correction may use a coordinator review and Markdownlint.
Substantive code normally needs an independent integrated review. The coordinator
reviews coverage before setting `coverage_reviewed: true`; the script cannot
infer missing requirements or verify that an input map is complete.

Do not add separate requirements for equivalent lenses already covered by one
review. A coherence review can satisfy the integrated review requirement. Preserve
mandatory repository gates and explicit user coverage. Record their concrete
commands rather than an invented generic suite.

## Record evidence, then reuse it

Run the snapshot helper from [audit-evidence.md](audit-evidence.md) before/after
execution. `review_evidence` is a chronological append-only list with unique
IDs. Each record includes `requirement_id`, `requirement_digest`, `policy_digest`,
`status` (`passed`/`failed`/`unknown`), `snapshot` (snapshot JSON path) and `source`
(nonempty execution log or review report file). Reviews also identify `reviewer`
and explicit `independent: true` when required. Preserve the actual evidence,
including command/exit status and environment or the reviewed scope/verdict.

Use this helper before scheduling another check:

```bash
python3 <coordinator-dir>/scripts/evaluate_review.py <git-dir>/ledger.json \
  --snapshot <git-dir>/current-inputs.json
```

It prints actual `policy_digest`, per-requirement digests, reusable/pending check
IDs and `mechanical_status`. On initial setup, pin the policy digest and record
requirement digests before running checks. These are identities, not PASS evidence.
Evidence sources are checked for existence, not parsed as proof of execution.
Only record passed evidence after the check actually passed on matching inputs.

The latest record for a requirement controls reuse. A later failure/unknown result
supersedes an older pass. Changed coverage, command, dependency map, independent
review requirement or feedback revision changes its digest. Policy drift blocks
the run until deliberately reconciled; do not silently replace the pinned digest.
Do not mutate past requirement records to retroactively justify evidence.

By default any snapshot change invalidates reuse. With a reviewed complete input
map, an unrelated file change may preserve a requirement's evidence. Changed
directory members, base, environment, repository identity and ignored/external
dependencies remain covered; global changes invalidate all narrow reuse too.
Unknown dependencies or live state require wider checks. Check published content
separately: a matching subset cannot prove the full pushed tree was validated.

Each `findings` entry keeps its existing family fields and gains an explicit
`status: resolved` plus `resolution_evidence` once a defect is fixed and validated.
False positives/intentional behavior need `disposition_evidence`. Other defects
remain open. Optional suggestions live outside `findings`; an actual defect
cannot become optional to meet budget. Invoke the family health analyzer before
selecting another remediation batch; record any stop in `blocked_reason`.

## Interpret the result

Exit 0: required records are current and no recorded defect is open. Exit 1:
pending work or a non-success block. Exit 2: malformed input or operational error.
`semantic_approval: false` is intentional: the coordinator/auditor must assess
the plan, implementation and underlying evidence before granting local `READY`.

Keep local `READY`/`NEEDS_WORK`/`BLOCKED` separate from remote provider status.
Missing required validation, unresolved feedback or policy drift cannot be
replaced by a cloud clean signal. A legacy health state `NORMAL` says nothing
about readiness. One integrated verdict closes local work; no literal zero-findings
phrase, additional audit or metadata-only repeat is required.
