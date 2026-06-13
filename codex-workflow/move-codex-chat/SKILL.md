---
name: move-codex-chat
description: Safely move a Codex chat from one existing project to another by updating local Codex metadata and backing up affected files first. Use when a chat appears under the wrong project in Codex Desktop, when a project was created after the chat started, when the user wants to move the current chat to another project, or when a chat title and project names must be resolved and corrected.
---

# Move Codex Chat

## Overview

Use this skill to reassign a Codex Desktop chat to a different existing project by editing the
local Codex metadata that drives sidebar grouping. The skill must back up the affected SQLite
database and rollout JSONL files before any write, resolve destination projects conservatively,
and verify that database, session metadata records, and turn context records agree after the move.

For the exact metadata touched by this skill, read
[references/storage-layout.md](references/storage-layout.md).

## Required Inputs

Collect these inputs before running the move:

- Destination project name or full path.
- Optional chat title.
- Optional thread id (recommended for apply after preview).
- Optional source project name or full path.
- Optional explicit apply intent.

Use these defaults:

- If the chat title is omitted, assume the current chat.
- If the source project is omitted, infer it from the resolved chat metadata.

## Safety Rules

Follow these rules on every run:

- Never create a destination project as part of this skill.
- Never write anything until the destination project resolves to one existing path.
- Always create a timestamped backup before changing Codex metadata.
- Never guess when a project name resolves to multiple paths.
- Never guess when a chat title resolves to multiple threads.
- If current-chat detection is ambiguous, stop and explain what needs to be specified.
- Verify the SQLite row, rollout `session_meta` records, and rollout `turn_context` records after
  the move.
- Tell the user that Codex Desktop may need a restart if the sidebar does not refresh.

## Workflow

### Step 1: Resolve Codex Home

Use `$CODEX_HOME` when it is set. Otherwise use `~/.codex`.

### Step 2: Resolve the Destination Project

Use `scripts/move_codex_chat.py` to resolve the destination from Codex's saved workspace roots.

Accepted input forms:

- full absolute path
- exact project folder name such as `movewise`

If the project does not exist:

- stop without writing
- show close project-name suggestions
- tell the user to correct the name or create the project first

### Step 3: Resolve the Chat

Resolve the target thread as follows:

1. If a chat title is provided, match against the sidebar title first, then fall back to the
   thread title stored in SQLite.
2. If a thread id is provided, resolve by that id (optionally constrained by the source project).
3. If no chat title is provided, treat the current chat as the most recently updated thread,
   optionally constrained by the source project if provided.
4. If more than one match remains, stop and show the candidate chat titles, ids, and projects.

### Step 4: Preview Before Applying

Run the helper in dry-run mode first unless the user's message already makes execution explicit.

Example:

```bash
python3 scripts/move_codex_chat.py \
  --dest-project new-project
```

Or with explicit chat and source project:

```bash
python3 scripts/move_codex_chat.py \
  --chat "Planning notes" \
  --source-project old-project \
  --dest-project new-project
```

The preview must show:

- resolved thread id
- resolved chat title
- current project path
- destination project path
- rollout file that will be patched

Important: if the preview used implicit "current chat" resolution (no `--chat`), do not rely on
running the same command again for apply. Another chat updating can change what "current" means.
Prefer applying with the resolved `thread_id` from the preview.

### Step 5: Apply the Move

If the preview is correct and the user asked to execute, run:

```bash
python3 scripts/move_codex_chat.py \
  --dest-project new-project \
  --apply
```

If the preview resolved a `thread_id`, prefer pinning it for apply:

```bash
python3 scripts/move_codex_chat.py \
  --thread-id "<thread-id-from-preview>" \
  --dest-project new-project \
  --apply
```

Or with explicit chat identification:

```bash
python3 scripts/move_codex_chat.py \
  --chat "Planning notes" \
  --source-project old-project \
  --dest-project new-project \
  --apply
```

The helper must:

- back up `state_5.sqlite`
- back up every affected rollout JSONL file
- update `threads.cwd`
- update each `session_meta.payload.cwd` in the rollout file
- update each rollout `turn_context.payload.cwd` and `turn_context.payload.workspace_roots`
- verify the database row, `session_meta` records, and `turn_context` records agree

### Step 6: Report the Result

Summarize:

- moved chat title
- thread id
- source project
- destination project
- backup directory
- number of `turn_context` records updated
- whether a Codex Desktop restart may be needed

## Common Cases

### Move the current chat

Use when the user says something like:

- `move this chat to movewise`
- `move this project chat into movewise`

Run the helper without `--chat`.

### Move a named chat

Use when the user says something like:

- `move "Riorganizza Drive e backup" to movewise`

Pass the title with `--chat`.

### Project Name Does Not Resolve

If the destination does not resolve, do not write. Show close project suggestions and tell the
user the project must exist first.

## Resources

### scripts/

- `move_codex_chat.py`: Resolve the thread and project, create backups, apply the move, and
  verify the result.

### references/

- `storage-layout.md`: Quick reference for the Codex metadata files touched by this skill.
