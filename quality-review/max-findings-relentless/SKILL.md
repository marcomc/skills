---
name: max-findings-relentless
description: Review and remediate an authorized diff until confirmed defects are closed and required evidence is current, using the shared review coordinator. Retains the existing thorough-remediation entrypoint without an independent nested loop.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Thorough Review and Remediation

Enter `$review-coordinator` with the requested remediation scope. Preserve an
explicit request for exhaustive/deep review as a coverage requirement; ordinary
invocation does not require every specialist or speculative repository-wide work.
Verify candidates against the user's contract before accepting them as defects.

The companion `review-coordinator` must be installed alongside this skill.
It owns remediation scheduling and exit. If already active, return the selected
`max-findings-review` lens and findings to it; do not start another loop or invoke
the gate/scoped entrypoints recursively. A missing companion is a dependency gap.

Use `max-findings-review` as a focused correctness lens where useful, together
with selected domain profiles. One sufficient independent integrated review can
cover those lenses and the coherence audit. Do not require another identical
pass or the literal phrase "No issues found" after the shared exit contract is met.

Close every confirmed defect and required validation gap in the authorized scope.
Optional cleanup and unsupported candidates are not defects; document their
classification. A cost/iteration limit never establishes readiness. Persistent
recurrence follows the coordinator's health gate and remains non-success.

The coordinator records candidate lessons during work and consolidates once
at the terminal outcome. Keep active policy stable; this entrypoint neither
updates skills between fixes nor repeats learning performed by its caller.
