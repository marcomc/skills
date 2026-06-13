---
name: branch-qa-remediation
description: Run a PR-style QA review on branch changes vs a base branch for any repository, produce meaningful remediation findings with file and line references, and output a markdown report/snippet that can be passed to Codex for applying fixes.
---

# Branch QA Remediation

Use this skill when the user wants a QA review of branch changes (like pre-PR) in any project, with actionable remediations and exact file/line references.

## Workflow

1. Confirm base branch (default `main`; fallback to `origin/main` if needed).
1. Run the bundled script:

```bash
~/.Codex/skills/branch-qa-remediation/scripts/run-branch-qa.sh --base <base>
```

Optional output path:

```bash
~/.Codex/skills/branch-qa-remediation/scripts/run-branch-qa.sh --base <base> --output <absolute-or-relative-md-path>
```

1. Return:

   - report path
   - short findings summary by severity
   - the "Remediation Prompt Snippet" section from the report

1. Add a manual sweep note when the branch touches stateful behavior:

   - sentinel/default round trips (`all`, `auto`, empty, null, omitted, disabled)
   - dry-run, preview, validate, read-only, or disabled paths with side effects
   - negative-path semantics, such as expected misses returning the wrong
     status class (`404` vs `500`, empty-state vs hard failure)
   - wrapper or shell argument parsing that may tokenize input unsafely or
     accidentally execute it
   - probes or validators that assume only one valid content topology when the
     feature may legitimately support both flat and nested layouts
   - repeated background triggers touching the same resource
   - feature-gated privilege artifacts in install/deploy scripts
   - maps or joins keyed by display labels instead of stable IDs
   - time/cadence logic with future timestamps or clock skew
   - limits duplicated across validators, schemas, UI, docs, helpers, or runtime

1. Tag each meaningful finding with the closest specialized reviewer profile so
   downstream remediation can route it without rereading the whole report:
   - `$pre-pr-review-frontend`
   - `$pre-pr-review-backend-services`
   - `$pre-pr-review-infra-runtime`
   - `$pre-pr-review-security-boundaries`
   - `$pre-pr-review-tests-validation`
   - `$pre-pr-review-docs-release`
   - `$pre-pr-review-config-data-flow`
   - `$pre-pr-review-cli-tooling`
   - `$pre-pr-review-ci-actions`
   - `$pre-pr-review-agent-workflows`

## Notes

- This is branch-diff focused (`merge-base(base, HEAD)..HEAD`), not full-repo QA.
- The script includes both heuristic checks and `shellcheck --enable=all` on changed shell scripts when available.
- If there are no findings, still return the generated report path.
- Do not spawn sub-agents from this skill. Treat profile tags as routing context
  for later remediation skills.

## Agent Learning Hook

<!-- BEGIN RECORD AGENT LEARNING HOOK -->
When this review workflow produces a real reusable finding, fix, regression, or
workflow correction, run `$record-agent-learning` before the final response.
Pass this skill name as `--source-skill`. Skip capture for clean/no-op reviews
and one-off repository trivia.
<!-- END RECORD AGENT LEARNING HOOK -->
