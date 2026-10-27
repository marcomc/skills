# Filesystem Migration Verification

- Persist long verification progress outside temporary logs. A checkpoint is
  reusable only while source/destination identity and metadata fingerprints still
  match. Traverse directories regardless of cached entries and verify hard-link
  relationships, broken symlinks and source changes with restored size/mtime.
  Exercise corruption and interrupted-resume paths.
- Retain the original tree until complete verification and path-switch readback.
  A copied tree, session handle or prior progress count is not migration completion.
- For external APFS UID/GID differences, inspect GlobalPermissionsEnabled and
  caller-dependent stat evidence before diagnosing loss. Compare bytes, ACLs,
  modes, flags, xattrs and native creation times independently. Retain per-item
  qualified ownership exceptions; do not normalize all differences or change
  volume-wide ownership settings merely to pass verification.
- After a failed Mutagen batch lifecycle command, inspect complete state for all
  requested sessions: partial state changes can precede connection failure.
  Restore only sessions authorized by the captured pre-maintenance state,
  individually and idempotently; preserve previously paused sessions. Verify
  unpaused state and Alpha connectivity separately from absent Beta availability.
