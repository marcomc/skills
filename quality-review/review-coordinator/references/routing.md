# Select checks from the change

Read only the applicable rows and linked references. Specialist profiles supply
domain checks; they are not additional orchestrators. A check already satisfied
by current evidence is covered regardless of which reviewer produced it.

| Changed behavior or risk | Primary lens | Conditional detail |
| --- | --- | --- |
| User-visible contract, algorithm or API behavior | `max-findings-review` or the corresponding domain profile | One correctness pass; do not also run branch QA for the same coverage |
| New/uncertain regression plan | `diff-regression-check-planner` | Use its output to select execution, not a second code review |
| Browser state, rendering, accessibility | `pre-pr-review-frontend` | [Data and presentation](checks-data.md) |
| APIs, workers, storage | `pre-pr-review-backend-services` | [Data and presentation](checks-data.md) |
| Config, schema, generated data, identity | `pre-pr-review-config-data-flow` | [Data and presentation](checks-data.md) |
| CLI, shell, install/uninstall, argument forwarding | `pre-pr-review-cli-tooling` | [Runtime boundaries](checks-runtime.md) |
| Deploy, service lifecycle, recovery, host selection | `pre-pr-review-infra-runtime` | [Runtime boundaries](checks-runtime.md) |
| CI permissions, matrices, caches or workspace ownership | `pre-pr-review-ci-actions` | [Runtime boundaries](checks-runtime.md) |
| Trust boundaries, credentials, privilege, external side effects | `pre-pr-review-security-boundaries` | Add `security-best-practices` only for a distinct uncovered requirement |
| Test harness correctness or uncertain coverage | `pre-pr-review-tests-validation` | Do not review ordinary unchanged tests separately |
| Agent policies, prompts or workflow control | `pre-pr-review-agent-workflows` | Routing, authorization, policy stability, execution versus claimed evidence |
| Docs, versioning, examples, public output | `pre-pr-review-docs-release` | [Publication](publication.md); sanitizer for externally visible artifacts |

Use `stack-best-practices-review` for a demonstrated framework/API-fit concern
or an explicit request. Use `code-quality-remediation` for implicated duplication,
complexity or maintainability. Run these in report-only mode when composed.
Their names do not require separate rereads of the diff. Do not load all profiles.

## Bounded and expanded prevention

For a bounded change, trace the changed contract and actual callers/consumers;
include the reported failure and a supported valid case when behavior changes.
No universal number of agents, test cases, files or review rounds determines
coverage. A docs-only correction still needs relevant documentation validation.

Expand before editing when reachability is unclear, the fix crosses state/trust
boundaries, durable mutation/recovery or concurrency could magnify harm, or real
feedback shows a missed sibling or introduced regression. Map the implicated
producer/consumer/recovery paths and use a scope audit when that map is uncertain.
Expand by contract, not by loading every checklist. A later independent defect
does not automatically justify a broad scan of unrelated subsystems.

Required repo gates, supported target runtimes and explicit user requests are
minimum coverage. Risk selection cannot waive them. Record omitted optional
lenses with a short reason when their applicability could reasonably be unclear.
