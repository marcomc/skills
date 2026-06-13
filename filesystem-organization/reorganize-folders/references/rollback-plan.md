# Rollback Plan

## Purpose

Use this reference to generate and consume rollback plans for folder reorganization runs.

Each applied run should write a rollback file before the first move. The same skill should later
be able to consume that file and restore the previous state using only move and rename
operations.

## Default Location

Unless the user specifies another location, write the rollback file to:

`<root>/.reorganize-folders/rollback-YYYYMMDD-HHMMSS.json`

## Required Properties

Each rollback file should contain at least:

- `version`
- `created_at`
- `root_path`
- `mode`
- `language`
- `protected_paths`
- `skipped_paths`
- `forward_operations`
- `reverse_operations`

## Recommended JSON Shape

```json
{
  "version": 1,
  "created_at": "2026-04-17T12:34:56Z",
  "root_path": "/absolute/path/to/root",
  "mode": "reorganize",
  "language": {
    "requested": "en",
    "inferred": "it",
    "effective": "en"
  },
  "protected_paths": [
    "/absolute/path/to/root/.sync-metadata"
  ],
  "skipped_paths": [
    {
      "path": "/absolute/path/to/root/Ambiguous",
      "reason": "low_confidence"
    }
  ],
  "forward_operations": [
    {
      "type": "move",
      "from": "/absolute/path/to/root/Old Folder",
      "to": "/absolute/path/to/root/New Bucket/Old Folder"
    }
  ],
  "reverse_operations": [
    {
      "type": "move",
      "from": "/absolute/path/to/root/New Bucket/Old Folder",
      "to": "/absolute/path/to/root/Old Folder"
    }
  ]
}
```

## Forward and Reverse Rules

- Write `forward_operations` in execution order.
- Write `reverse_operations` as the exact inverse mapping needed for restore.
- Ensure reverse operations can be replayed safely without guessing.
- Never encode delete operations.
- If a directory is created only as a container, it may be removed during restore only if it is
  empty after reverse moves.

## Restore Validation

Before applying a rollback plan:

- verify that `root_path` matches the requested restore root
- verify that enough `from` paths in `reverse_operations` still exist
- verify that the plan version is supported
- verify that the rollback file is readable and valid JSON

If validation fails, stop and report the mismatch.

## Restore Preview

Before restore, show:

- the rollback plan path
- the root path
- the number of reverse operations
- representative reverse mappings
- any paths that are missing or blocked

## Execution Order

During restore:

1. Validate the plan.
2. Preview the reverse mapping.
3. Ask for confirmation unless immediate restore was explicitly requested.
4. Apply reverse operations in the stored reverse-safe order.
5. Remove only empty container directories created by the original run.
6. Rescan and verify.
