# Publication and release evidence

Use when public/external artifacts or release readiness are within the scope.
Select `$repo-publication-sanitizer` and reuse its evidence only while its actual
inputs match. It returns findings to the coordinator and does not open a loop.

Block accidental disclosure of real personal paths, identifiers, private
addresses/services, credentials, signed URLs and copied operator logs. Preserve
intentional public author/license/package metadata. Distinguish synthetic fixtures,
reserved ranges and clear placeholders from live data before reporting a defect.
Ambiguous sanitized examples need clearer labeling; they are not automatically
proof of private disclosure. Track actual privacy blockers until resolved or
explicitly authorized by the user.

When secrets or private values move to ignored overrides, prove tracked defaults
still support their intended deploy path; public placeholders must not leak into
numeric fields or runtime behavior. Disabled/opt-in defaults must remain inert.

Reconcile docs, operator commands, product choices and planning artifacts with
the integrated result before the terminal remote review. Preserve the repository's
existing changelog structure: use `Unreleased` when present; preserve a concrete
pending release heading when that is the documented convention. Merge repeated
notes; do not turn a release changelog into remediation chronology.

For a release handoff, report scope/base, reviewed/pushed HEAD, local quality,
publication status, actual commands/evidence, required missing proofs, optional
recommendations, target-environment caveats and whether tagging is supported.
`$create-github-release` may consume that handoff; readiness does not itself
authorize tagging, publishing or deploying.
