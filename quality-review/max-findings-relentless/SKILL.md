---
name: max-findings-relentless
description: Automate repeated runs of max-findings-review plus remediation/testing loops until the codebase reports no findings; use whenever a thorough fix-and-test cycle is required before merging.
---

# Max Findings Relentless

## When to use

Use this skill when you need to treat a pull request or diff as “review then fix until spotless”: run the `/max-findings-review` skill, remediate every finding, test, debug until success, and repeat until the review reports “No issues found.”

## Workflow

1. **Kick off the review.** Invoke `/max-findings-review` against the current diff and capture every finding. Follow its prompt verbatim, load relevant AGENTS.md guidance, and treat each finding as a real risk that must be addressed.
2. **Classify findings by specialist profile.** Tag each finding with the
   smallest useful reviewer profile, such as `$pre-pr-review-frontend`,
   `$pre-pr-review-backend-services`, `$pre-pr-review-infra-runtime`,
   `$pre-pr-review-security-boundaries`, `$pre-pr-review-tests-validation`,
   `$pre-pr-review-docs-release`, `$pre-pr-review-config-data-flow`,
   `$pre-pr-review-cli-tooling`, `$pre-pr-review-ci-actions`, or
   `$pre-pr-review-agent-workflows`.
3. **Convert findings into explicit checks before changing code.** For each finding, write down the concrete failure mode you need to prove or disprove. Prefer a small reproducible check before editing so you can tell whether the finding is a true regression, a generated-artifact issue, or an unrelated environment problem.
4. **Propose and apply remediations.** For every reported issue, add a focused fix proposal (brief description + concrete code changes) and apply it using the appropriate files/commands. Prefer minimal, targeted edits that directly resolve the reported impact.
   When multiple edit-capable sub-agents are explicitly authorized and the write
   scopes are disjoint, include `$pre-pr-remediation-worker` and the selected
   reviewer profile in each worker brief.
5. **Test the exact affected path first.** Run the narrowest check that proves the specific finding is fixed before you fall back to broader suites. For wrapper/config changes, test the real user-facing entrypoint, not only the underlying script or helper. For generated/configured systems, rerender or regenerate artifacts before testing the live command path.
6. **Debug until stable.** If the exact check still fails, debug the failing path, collect logs/output, and determine whether the blocker is:
   - a real code defect
   - stale generated artifacts or caches
   - a race introduced by the test itself
   - unrelated environment or fixture corruption
7. **Run the broader regression set.** Once the narrow path is green, run the most relevant broader tests (integration suites, CI smoke checks, lint tasks, scenario tests, etc.). Choose the best command for the stack (for example `ws ansible-lint`, `npm test`, `pytest`, `cargo test`) and keep rerunning until the failing scenario no longer reproduces.
8. **Run the publication sanitizer when relevant.** If the branch, PR, repository, package, or generated artifacts may be public, run `$repo-publication-sanitizer` after fixes and before the final review decision. Treat accidental disclosure findings as blocking.
9. **Re-run the review.** Once the tests pass, rerun `/max-findings-review`. If it reports new findings, loop back to step 2. Continue cycling until `/max-findings-review` explicitly states “No issues found.”
10. **Feed generic lessons back into the skill corpus.** If the loop exposed a
   reusable blind spot in local review guidance, tighten the relevant skill or
   checklist before finishing. Prefer refining an existing higher-leverage rule
   over appending a duplicate new reminder.
11. **Summarize results.** When the loop ends cleanly, summarize the fixes, the final test commands, the publication/privacy scan status when applicable, and the fact that the review returned zero findings so the change is ready for the next gate.

### Python-specific validation rules

When the repo is Python-first, also do the following:

1. Prefer the repo's canonical gate command when one exists, such as `make check`, after targeted checks pass.
2. If a config model changed, verify the load, write, validate, example-config, docs, and installer/bootstrap paths still agree.
3. If `pyproject.toml` changed or new imports were introduced, verify optional dependencies, package data, and console-script entrypoints still match real installation behavior.
4. If the diff touches a packaged web or CLI entrypoint, test the user-facing command path, not only the helper or renderer.
5. If `AGENTS.md` requires live validation for the touched surface, report that requirement explicitly even when local checks are green.
6. If the diff touches interrupt handling, worker pools, retries, or cleanup helpers, run at least one cancellation-focused regression that proves shutdown stays clean under partial work.

## Prevention checks

Before asking for the next review pass, explicitly check for these generic failure classes:

- **Argument-contract regressions**
  - If you touched a CLI, wrapper, shell parser, or config DSL, run the documented user-facing command forms, especially ones with quoting, spaces, or multi-token passthrough values.
  - Add one adversarial input check for injection or malformed input, and one compatibility check for a documented happy-path invocation.
  - When modes share one dispatcher, explicitly test mutually exclusive and required-together combinations on the real top-level entrypoint so an early guard does not block a later valid branch.

- **Generated-artifact drift**
  - If a change affects rendered configs, generated harness files, compiled assets, or vendored metadata, rerender/regenerate before validation.
  - Test the real entrypoint only after confirming the generated copy reflects the source edit.

- **Validation-path mismatches**
  - If you changed a helper or abstraction layer, test both the helper and the command or workflow that consumes it.
  - Do not assume a lower-level green check proves the user-facing path is still correct.

- **Race-prone verification**
  - Avoid overlapping runs that mutate the same files, containers, databases, or services while you are trying to prove a regression.
  - When a scenario intentionally breaks state before repairing it, run that scenario in isolation.

- **Environment health versus code health**
  - If a regression appears in an external system or mutable fixture, verify whether the environment is healthy before blaming the code.
  - Repair or reset corrupted fixtures, then rerun the same check so you can separate product bugs from testbed decay.

- **Cleanup-path realism**
  - When a test intentionally introduces drift or failure, verify the cleanup path from the current live state, not from an old snapshot or pre-test assumption.
  - Prefer rebuilding cleanup state from current authoritative data.
  - For concurrent cleanup, make best-effort drains tolerant of secondary timeout/cancellation errors so they do not mask the original failure or interrupt.

- **Sentinel/default round trips**
  - If a UI, API, config writer, or form handler touches values where empty/null/omitted means "all", "default", "auto", "inherit", or "disabled", test a normal save/load cycle that preserves that semantic value.
  - Add a regression for newly added resources after an "all/default" save so stale concrete lists do not silently replace sentinel state.
  - Treat empty strings as a first-class sentinel candidate whenever the surrounding config/examples use `""` for optional fields; verify they do not silently become concrete filesystem paths, IDs, or selectors.

- **Side-effect mode contracts**
  - For dry-run, preview, validate, disabled, no-op, or read-only modes, assert that external effects do not happen: no device writes, privileged helper calls, background workers, network publishes, detach/attach operations, or persistent markers unless documented.
  - Monkeypatch or fake the side-effect boundary so the narrow test fails if the forbidden call is made.

- **Shared-resource worker ownership**
  - If a path starts background work, retries jobs, exports artifacts, or mutates a shared resource, test repeated triggers while the first operation is still running.
  - Verify both behavior and user-visible status: no duplicate worker starts, and success/start messages only claim work that actually began.
  - Also test interruption while sibling workers are still active; cancelled or timed-out workers must not escape shutdown with stray tracebacks or follow-on side effects.

- **Filesystem migration topology**
  - If code moves, renames, or migrates directories/files based on config, test same-path and descendant-path destinations in addition to the happy path.
  - Reject or skip self-nesting moves such as moving a directory into one of its own children.

- **Privilege and feature lifecycle**
  - If install, bootstrap, or deployment code grants privileges, capabilities, credentials, policies, service units, or root helpers, test the disabled/uninstalled feature path.
  - Verify privilege artifacts are skipped or removed when the feature is off, not merely unused by happy-path code.

- **Stable identity and collision checks**
  - When resource names, labels, titles, slugs, or display text are used in maps, joins, charts, caches, files, or routes, add a duplicate-label scenario.
  - Use stable unique identifiers for lookup keys and keep labels as presentation data.

- **Time and bound drift**
  - Test future timestamps, clock skew, stale markers, zero/default intervals, and catch-up behavior for scheduling code.
  - Mirror limits across schemas, validators, UI constraints, docs, helper scripts, and runtime enforcement, then test just outside each boundary.

- **Publication/privacy disclosure**
  - If code, docs, examples, config, scripts, reports, or release artifacts may be public, run `$repo-publication-sanitizer`.
  - Treat accidental home paths, hostnames, IPs, usernames, secrets, hardware IDs, copied logs, and private endpoints as blockers until redacted or intentionally accepted.

## Generic debugging loop

Use this loop for any project when a review finding does not yield to the first fix:

1. Reproduce the exact reported scenario with the smallest command or test that exercises it.
2. Capture the observable failure signal: stdout/stderr, logs, rendered config, exit code, HTTP response, or artifact diff.
3. Classify the failure:
   - code path wrong
   - arguments parsed wrong
   - generated artifact stale
   - environment broken
   - test racing another mutation
4. Fix only the class you have evidence for.
5. Re-run the same exact reproduction before running broader tests.
6. If it passes narrowly, run the nearest integration or smoke check.
7. Only after both are green should you ask for another review pass.

## Notes

- Treat every `/max-findings-review` finding as blocking until verified fixed; even edge cases deserve consideration.
- Favor reproducible, automated tests over manual verification whenever possible; document any manual steps that were necessary to build confidence.
- This skill assumes you have access to the usual workspace commands for testing and review; adapt the test command list to match the repository’s toolchain.
- When a review finding exposes a generic blind spot in your process, update the local workflow or skill guidance before moving on so the next loop benefits from the lesson.
- For public work, a clean code review is not enough if the final diff still leaks personal or system-specific data.

## Agent Learning Hook

<!-- BEGIN RECORD AGENT LEARNING HOOK -->
When this review workflow produces a real reusable finding, fix, regression, or
workflow correction, run `$record-agent-learning` before the final response.
Pass this skill name as `--source-skill`. Skip capture for clean/no-op reviews
and one-off repository trivia.
<!-- END RECORD AGENT LEARNING HOOK -->
