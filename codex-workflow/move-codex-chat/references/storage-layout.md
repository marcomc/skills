# Evidence and Context Relocation

## Membership-only evidence

Native `list_projects` and `list_threads` results establish app membership;
`threads.cwd` does not establish a project ID. Keep these identities separate.
The read-only helper uses `$CODEX_HOME` or `~/.codex` and reads an existing
`state_5.sqlite` (including its `sqlite/` variant), the exact thread's rollout,
and Git directory/common-directory/HEAD identity. It opens SQLite in read-only
mode and hashes the entire rollout. Store snapshots privately: they contain
local paths. They are evidence, not permissions or live app state.

The helper does not edit `session_meta`, `turn_context`, workspace roots, Git
metadata, project configuration or thread state. Its legacy `--apply` operation
is refused. The old private metadata writer was removed because changing cwd
and historical contexts does not implement native project membership.

Keep the actual inventory/readback freshness and completeness with the evidence;
a JSON fixture alone cannot prove a live move. Incomplete hosts/sources, missing
or ambiguous destination identity, unknown source membership and conflicting app
versus database cwd must be resolved before any move.

## Helper CLI migration

The next release replaces the private metadata writer with a read-only helper.
This is an incompatible CLI change for scripts invoking the previous helper.

| Previous invocation | Replacement |
| --- | --- |
| `--chat` or implicit most-recent thread | Resolve the exact ID through the app and save its record for `--thread-json`. |
| `--source-project` as a cwd filter | Read actual app membership; a worktree cwd is independent of the project root. |
| `--dest-project` resolved from saved workspace roots | Supply current `list_projects` output with `--projects-json`; use an exact ID, label or path. |
| `--apply` | Use `move_thread_to_project` or the user sidebar; the helper refuses private writes. |
| Verification against a rewritten destination cwd | Save preview stdout, then pass it with `--before-json` and a fresh `--thread-json` readback. |

Keep `--codex-home` or `$CODEX_HOME` when using an alternate local Codex home.
Project paths come from the app inventory; do not hard-code the maintainer's
repository layout. See the entrypoint for preview and verification commands.

## Explicit execution-context relocation

A request to move the execution context is separate from project membership.
Preview its exact scope and use the supported handoff/worktree lifecycle tools
when they support that request. Retain a recoverable snapshot/backup and verify
worktree ownership, cwd, branch, files and session identity after the operation.
Do not infer this authority from a sidebar move. Arbitrary private database and
historical rollout rewriting is not a fallback when a supported handoff refuses.
If the requested relocation has no supported route, state that limitation and
provide a bounded operator action rather than attempting it with this helper.
