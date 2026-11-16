---
name: move-codex-chat
description: Move a Codex Desktop chat between existing projects while preserving its execution directory and worktree, using native membership controls and verified readback.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Move Codex Chat

Change project membership with the native app tools. Preserve the thread ID,
host, cwd, worktree, rollout history and execution envelope by default.
The bundled helper prepares and verifies evidence; it never moves a chat or
writes the Codex database, rollout files or application configuration.

## Resolve and preview

1. Read the actual current `list_projects` inventory. Resolve an existing local
   destination by exact ID, unambiguous label or canonical full path. Saved
   workspace roots are not a complete app inventory. Never create a project or
   infer its ID from its directory name.
2. Resolve the exact chat with `list_threads`, including its host, project ID,
   status and cwd. Use the calling chat's known ID for “this chat”; never assume
   the most recently updated chat is current. Paginate when needed. Resolve
   duplicate titles before proceeding.
3. Preserve active/reserved worker ownership: coordinate an idle boundary with
   its owner before moving an execution envelope. Do not resume or start a chat
   merely to inspect it. Pin the resolved thread ID for every subsequent action.
4. Save a fresh exact thread record and the complete project inventory as private
   JSON evidence outside published files. Run the read-only preview below.
   Keep its stdout as `before.json`. Show source/destination membership and the
   preserved cwd/worktree before executing the user's authorized move.

```bash
python3 <skill-dir>/scripts/move_codex_chat.py \
  --thread-json thread-before.json \
  --projects-json projects.json --dest-project '<project-id>' > before.json
```

The verifier supports local Codex chats. Other hosts/backends require their
supported controls and independent equivalent evidence; do not use this local
helper against them. Read [storage-layout.md](references/storage-layout.md)
for evidence limits and explicit context relocation.

## Move through the app

Call `move_thread_to_project` with the exact thread ID, destination project ID
and host. This changes membership; do not rewrite cwd to simulate it.

- On `confirmation_required`, stop automated writes and name the exact chat and
  destination for the user to move in the sidebar. The native move supplies the
  source-folder consent; the tool has no confirmation override parameter.
- On ambiguous source identity or refusal, explain the exact refusal and use the
  permitted manual action. Do not bypass it with private database writes, guessed
  project mappings, permission changes or another destination chosen to evade it.
- On timeout or uncertain mutation, read current membership before doing anything
  else. Do not automatically retry the move or report success from the API envelope.
- If native tools are unavailable, request the same bounded manual move. Avoid
  UI automation when access to the app is denied.

## Verify and report

Read the exact thread again from the app, independently of the mutation response.
Save that record as `thread-after.json` and run:

```bash
python3 <skill-dir>/scripts/move_codex_chat.py \
  --thread-json thread-after.json --before-json before.json
```

Success requires both the destination `projectId` and identical execution
fingerprints. The chat must remain idle during strict rollout comparison; if a
new turn appended history, reconcile it separately rather than labeling a changed
file preserved. A missing destination, changed context or unavailable evidence is
not success. Preserve evidence and explain the precise next action; do not repair
it by overwriting history. Report the actual route (native tool or user sidebar),
source/destination and preserved cwd/worktree. Do not promise universal automatic
moves from one successful manual case.
