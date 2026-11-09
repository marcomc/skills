---
name: streamline-test-suite
description: Audit or reduce test-suite cost by pruning obsolete tests, consolidating redundant coverage, optimizing fixtures, or adjusting execution frequency while preserving regression controls.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Streamline a test suite

Reduce measured execution and maintenance cost while preserving required
behavioral controls. An audit produces findings; an optimization request permits
local changes within its scope. Preserve unrelated work and project-specific
release, platform, data and approval constraints. Keep existing quality gates
unless the task authorizes changing them.

## Establish the baseline

- Inspect project guidance, supported behavior, test discovery, runner entry
  points and CI triggers. Inventory selected cases, parameter rows, environments,
  skips and shared suites. Record revision, local changes and baseline failures.
  Claim a complete audit only when every scoped case has a disposition.
- Compare executable module and discovery case counts; keep `unittest.main()`
  after all test definitions. For explicit runners, verify each test is called
  and inject a final-case failure to ensure success is printed only after it runs.
- Reuse valid timing and runner results. Separate build, startup, fixtures,
  execution and teardown; file counts are not executed case counts. When useful
  evidence is missing, take a bounded measurement within existing authorization.
  Label estimates and partial runs; avoid expensive or physical runs just to count.
- Distinguish permanent **reduction**, change-specific **selection**, and
  **prioritization** of execution order. Rescheduling retains a test but changes
  when it protects the product; record that trade-off explicitly.

## Evaluate each candidate

Read the complete test and helpers beside the production entry point and relevant
history. Identify what defect its assertions can detect, under which inputs,
boundary, configuration and lifecycle. Compare those claims with potential
survivors, including negative paths and isolation requirements.

Use this decision table; age, slowness, similar names, overlapping coverage and
a history of passing are discovery signals, never sufficient deletion evidence.

| Finding | Decision and required evidence |
| --- | --- |
| Equivalent controls | Consolidate or remove only after mapping every assertion and condition to surviving tests at the required boundary and trigger. |
| Retired behavior | Remove when current requirements and reachable consumers establish that the contract ended; check compatibility, persisted data, migration and rejection obligations first. |
| Historical bug reproduction | Retain its invariant while the failure remains credible; transfer unique inputs, ordering or state into a survivor before removing the old case. |
| Brittle, circular or weak assertion | Repair or replace a still-required control; remove only when it protects no required claim or a survivor already protects it. |
| Rare but valid behavior | Retain unique protection; consider frequency changes only within the project's accepted detection delay. |
| Failing, skipped or flaky case | Diagnose the product, harness and environment. A failure or skip is not evidence of obsolescence. |
| Uncertain equivalence or support | Retain and state what evidence would resolve the decision. |

A unit test and an integration, UI or physical test may cover the same lines but
detect different wiring, transport or lifecycle faults. Preserve independently
valuable layers and important security, data-integrity, compatibility and failure
controls. Static checks can be appropriate for packaging or architecture contracts;
assertion-free tests can detect crashes. Judge the actual claim, not its form.

Rank candidates by avoidable resource/maintenance cost and strength of preservation
evidence, accounting for impact, likelihood and independent fault detection.
Optimize shared setup or safe build reuse when it offers better savings. Preserve
process, account, transaction and mutable-fixture isolation when consolidating.
Do not invent a deletion quota or acceptable coverage loss to meet a cost target.

## Demonstrate preservation

- Record each affected test ID/parameter group, protected behavior, decision,
  surviving test IDs and trigger, evidence, cost and validation command. For a
  retired contract, cite retirement evidence instead of inventing a survivor.
  Keep group records only when all parameter rows have the same disposition.
- Line/branch coverage and similarity identify candidates; they do not establish
  assertion equivalence. Compare affected paths, not just aggregate percentages.
  When fault detection is uncertain or an important regression is transferred,
  use a bounded historical reproduction, deliberate fault or existing mutation
  tool to check that surviving tests fail for the intended reason.
- Compare the same fault/condition set before and after; an unchanged aggregate
  mutation score can hide a newly missed fault. Treat equivalent mutants,
  timeouts and unavailable environments as unresolved evidence. When a removal
  depends on missing proof, retain the test. Passing samples support only the
  checked fault classes, never a guarantee against future regressions.
- Use an isolated disposable workspace for fault injection or historical code;
  preserve original inputs and bytes. Keep paid, live, destructive and hardware
  checks within their existing authorization. Prefer established project tooling
  over adding an expensive instrumentation system for a small cleanup.

For a compact decision record, worked examples and source rationale, read
[references/decisions.md](references/decisions.md). For research or an external
skill comparison, read [references/research.md](references/research.md).

## Implement and validate

Make coherent, reversible batches. Move unique assertions into their surviving
owner before removing the old test. Clean unused test support after checking
consumers; production refactoring requires task scope and contract validation.
Retain a recovery revision or patch, including original content for untracked
tests. Follow project quarantine/review rules when present; skipping a test is
already a reduction in active protection.

For selection or frequency changes, verify runner discovery and actual CI
configuration: every retained control needs an executable command and a real
trigger. Preserve full and specialized suites at their required gates. Moving a
unique check from a merge gate to a nightly job increases detection delay; make
that trade-off explicit and obtain authority if the task does not cover it.
Shared behavior keeps its required release coverage even when another feature
using it is deferred to a later release.

Run focused checks and the appropriate affected suite after each meaningful
batch. Compare before/after case and parameter counts, failures and skips on
matching inputs, configuration and environment. Preserve baseline failures and
first-run failures after retries; a timeout or partial suite is not a pass.
Measure wall time and resource use when relevant, separating build reuse from
test execution savings. Reuse unchanged valid evidence instead of repeating
expensive checks without a reason.

Report decisions and retained controls, measured versus estimated savings,
commands/results, unresolved risks and unrun checks. State the next action and
its gating evidence. A justified finding that nothing can safely be removed is
a valid outcome.
