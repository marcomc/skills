---
name: codex-review-skill-autolearn
description: Learn from completed reviews and evidenced workflow friction; refine the smallest useful check, skill or instruction source without redundant guidance.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Codex Review Skill Autolearn

Run once after an integrated review outcome, including an explicit non-success
stop. Improve future work from observed defects and execution friction. Keep the
active run's policy stable; apply policy changes to subsequent runs. An urgent
repair requires an explicit rebaseline and reconciliation of affected evidence.

## Collect evidence once

Reuse the coordinator's terminal ledger: findings, fixes, tests/probes, sibling
regressions, local outcome and separate remote status. During work, retain
compact candidate observations with source references in that same ledger.
Investigate a candidate's raw session/tool records only when its summary is
insufficient. A clean review may still expose costly navigation or duplicated
work; a smooth session with no actionable lesson ends without changes.

For evidenced process friction, control retirement, or a user-requested comparison
with Retro, read [session-improvement.md](references/session-improvement.md).
Retro remains an explicitly requested retrospective, never an extra review gate
or a skill to invoke automatically after each batch.

A report-only request, independent comparison or unapproved user choice returns
proposals without edits, installation or learning capture. Otherwise preserve the
caller's authority: skill refinement does not grant product-code, hook, CI,
credential, deployment or publication permission.

## Distill and check coverage

For each supported candidate, identify its root cause, falsifiable contract,
source evidence and the smallest intervention that changes future behavior.
Rank concrete impact and likely recurrence against added context, execution and
maintenance cost; label estimates and unavailable measurements.

Inspect the relevant current target and classify coverage:

- `covered`: verify whether it was reached/applied and whether its tooling ran;
  correct routing or execution rather than repeat the rule;
- `weak`: refine, merge, replace or relocate the insufficient rule;
- `missing`: justify a new check or concise instruction with observed evidence.

Findings with the same mechanism share a lesson family; similar wording or a
shared file does not establish equivalence. Preserve distinct occurrences across
runs for recurrence measurement. Unsupported advice is discarded, not recorded.

## Choose the smallest target

Prefer wiring/fixing an existing deterministic check, then an executable
regression for a reproducible failure. Put judgement-dependent standards in the
existing reviewer guidance. Keep implementation invariants and authority/safety
constraints available before the action that needs them.

| Failure domain | Relevant profile |
| --- | --- |
| Browser, UI, client state | `pre-pr-review-frontend` |
| APIs, workers, persistence | `pre-pr-review-backend-services` |
| Deploy, service lifecycle, containers | `pre-pr-review-infra-runtime` |
| Auth, secrets, privilege, external side effects | `pre-pr-review-security-boundaries` |
| Tests, fixtures, coverage evidence | `pre-pr-review-tests-validation` |
| Docs, release notes, examples | `pre-pr-review-docs-release` |
| Config, schemas, generated data, identity | `pre-pr-review-config-data-flow` |
| Shell, CLI, installers, local tooling | `pre-pr-review-cli-tooling` |
| GitHub Actions and CI | `pre-pr-review-ci-actions` |
| Agent instructions, prompts, learning | `pre-pr-review-agent-workflows` |

Use `review-coordinator` for orchestration, finite scope, evidence reuse or exit
contracts; keep domain checklists out of entry adapters. Use
`pre-pr-remediation-worker` for edit-worker coordination, not review heuristics.
One lesson need not update every layer. A reviewer improvement is detection
unless the implementing agent reaches the prevention target before acting.

## Apply and validate

Resolve owning sources before editing. Refine the smallest set of sources,
validate their complete affected folders, refresh the documented canonical
installation and verify downstream mirrors. Installed-only changes are
non-durable. Leave third-party skills intact unless personalization is requested.

Replace weaker guidance instead of accumulating examples. Remove duplicates,
stale/no-op prose and superseded checks only with coverage evidence; few recent
activations do not justify removing protection against rare serious failures.
Compare the complete reached instruction path, including references, rather than
only shrinking the entrypoint. Missing measurements remain unknown.

Run Markdownlint on changed Markdown with the user config and relevant checks
for changed executable behavior. A new deterministic check must reject the
observed failure and retain supported valid cases. Reconcile affected or
contradictory guidance before returning. Learning alone does not reopen an
unchanged product review or invalidate its remote result.

## Report and capture once

Report evidence-backed failure classes, coverage decisions, proposed/applied
status, targets, verification and the operation (`refine`, `merge`, `replace`,
`remove`, `wire-existing`, `add` or `no-op`). Include changes in instruction size
and observed check cost when available, plus source/install/fanout parity.
Explicitly report when no intervention is warranted.

<!-- BEGIN RECORD AGENT LEARNING HOOK -->
For a real reusable lesson, reference the coordinator's existing capture or use
`record-agent-learning` once per project/source-run/lesson-family. Record applied
targets and verification evidence when already implemented; consolidation must
verify coverage rather than apply it again. Keep unresolved proposals subject to
their existing review/authority boundary. Report-only comparisons create no notes.
<!-- END RECORD AGENT LEARNING HOOK -->
