# Storage Layout

This skill updates only the minimum local Codex metadata needed to change project grouping in the
Desktop sidebar.

## Files Touched

- `state_5.sqlite`
  - table: `threads`
  - field updated: `cwd`
- rollout JSONL file recorded in `threads.rollout_path`
  - record type: `session_meta`
  - field updated: `payload.cwd`
  - record type: `turn_context`
  - fields updated: `payload.cwd`, `payload.workspace_roots`

## Read-Only Inputs

- `.codex-global-state.json`
  - used to resolve known workspace roots and project names
- `session_index.jsonl`
  - used to resolve human-facing sidebar thread names

## Important Notes

- Sidebar titles may differ from `threads.title`, so prefer `session_index.jsonl` for matching by
  visible chat name.
- The current chat fallback is implemented as the most recently updated thread, optionally
  constrained by source project.
- All `session_meta` and `turn_context` records are rewritten so a resumed chat receives the
  destination project as its environment context after the move.
- `session_index.jsonl` is not edited by this skill.
- Codex Desktop may require a restart before the sidebar reflects the new grouping.
