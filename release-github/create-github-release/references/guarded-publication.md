# Guarded publication

## Default same-host gate

The publisher holds `flock` on `release-publication.lock` in
`git rev-parse --git-common-dir`. All worktrees of that repository share the
same inode; the file is kept in place when the lock is released. A competing
process waits up to `--lock-timeout` seconds (default 60), then starts its own
fresh observations. This gate covers cooperating publisher processes on macOS
and Linux. Separate clones, other machines and direct Git/`gh` writers do not
share it. Remote target/tag/release freshness and non-force tag pushes still
detect observed collisions; they are not global exclusion.

The default requires no CI deployment or service setup. For a managed pipeline
on one Mac, route publication through this publisher and retain the reported
boundary. Use the optional external adapter when the actual project requires
stronger coordination across machines.

## Plan contract and mutation boundaries

`--plan` consumes only an `update-release` **bound** plan after verified merge.
The companion helper is loaded from the sibling installed/repository skill,
with guard API version 1. Upgrade the pair together.

Within the held gate, the publisher verifies:

1. Clean HEAD, matching configured repository and fresh authoritative upstream.
2. Exact plan version/changelog/target SHA and unchanged remote baseline.
3. Complete GitHub release/draft coverage and documented history continuity.
4. The same conditions immediately before local tag creation/adoption, tag push
   and release creation/edit. The optional external verifier runs last before
   each mutation, with a fresh challenge.
5. Exact tag object/peeled commit, release identity, notes/title/state and latest
   designation after publication.

Plan mode creates an unused release; it does not edit existing publications.
No-plan mode can edit an existing stable release when the request authorizes
that operation. Existing drafts/prereleases require separately scoped handling.

The publisher journals tag intent before creation/push, then reads the exact
remote object and peeled commit back. Only that verified current-attempt tag
can be normalized out of later plan comparisons. After creation, only the exact
new release identity/state can be normalized for final verification. Unexpected
tag or release changes remain stale-plan failures. The public `check` command
has no flag to claim ownership of an arbitrary tag/release.

## Optional external adapter

```bash
python3 "$publisher" --plan /path/to/private/publish.json \
  --gate-verifier /path/to/approved/live-gate-verifier \
  --gate-lease "<opaque-lease-handle>"
```

Both options are required together. The handle is an identifier, not a secret
capability; credentials belong in the trusted adapter's private environment.
The same-host lock is still held in this mode; the external checks add stronger
coordination rather than bypassing other local publisher processes.
The explicitly selected executable must be absolute and not group/world
writable. It is part of the approved project's trust boundary. The publisher
cannot infer its honesty from returned JSON: validate its real service client
and policy before using it for production. A test echo implementation is never
production serialization evidence.

The controller acquires and maintains an existing shared lease before invoking
the publisher, retains unresolved outcomes, and releases only after verified
success or read-only reconciliation. The verifier performs fresh authenticated
**reads** of that service and its writer/target policy. It must exit nonzero for
unavailable or ambiguous state. It must not acquire/release locks or publish.
The skills do not create this infrastructure.

The publisher sends one JSON request on stdin:

```json
{
  "schema": 1,
  "nonce": "<fresh-challenge>",
  "lease_id": "<opaque-lease-handle>",
  "phase": "before_push_tag",
  "repository": "github.com/example/project",
  "target_ref": "refs/heads/main",
  "target_sha": "<exact-commit-sha>",
  "version": "1.1.0",
  "tag": "v1.1.0",
  "plan_fingerprint": "<saved-baseline-sha256>"
}
```

Return those exact fields plus:

| Field | Required evidence |
| --- | --- |
| `gate_key` | `release:github.com/example/project`, shared across versions/worktrees |
| `service` | Verified HTTPS service identity, without credentials/query tokens |
| `held`, `exclusive` | This caller currently owns the shared exclusive lease |
| `all_writers_gated` | Actual writer policy requires every relevant publisher to use this service |
| `target_fenced` | Policy prevents target advancement during this critical section |
| `no_unresolved_publication` | Controller has no unresolved prior publication outcome |
| `evidence.lease_revision` | Current server lease revision/receipt |
| `evidence.writer_policy_revision` | Independently checked writer-policy revision |
| `evidence.target_fence_revision` | Independently checked target-fence revision |
| `checked_at`, `expires_at` | Offset-aware ISO times; checked within 10 seconds and lease valid for at least another 90 seconds |

Phases include `initial`, `before_create_tag`, `before_adopt_tag`,
`before_push_tag`, `before_create_release`, `before_edit_release` and
`verify_result`. Unknown fields do not grant authority. A missing/false proof,
wrong challenge/binding or expiring lease stops before the mutation. The
publisher never claims cross-host exclusion in its default mode.

## Uncertain outcomes

Private journals live in `publication-intents/*.json` under the common Git
directory, with mode `0600`. Intent files and their containing directory entries
are synced before writes; atomic status replacements also sync the directory.
Notes are passed through a private temporary file removed on success/failure;
journals retain note hashes, target/tag identity,
operation and observed results. Raw CLI diagnostics and credentials are not
printed. `--journal` may select a new filename within that same intent folder.

`attempting`, `unknown`, `observed_success` without terminal verification, and
`requires_read_only_reconciliation` are not publication success. They block a
new local attempt for the same repository/tag. Local journals are not a durable
cross-machine journal; an external controller must provide that separately.

Reconcile without writing remotely:

```bash
git ls-remote --tags origin refs/tags/v1.1.0 'refs/tags/v1.1.0^{}'
gh release view v1.1.0 --repo example/project \
  --json id,tagName,name,body,isDraft,isPrerelease,publishedAt,url
```

Compare the exact tag object, peeled commit, release identity/state and notes
against the saved intent. A failed read stays unknown. Do not delete a tag or
edit/create a release as an automatic recovery step. After the operator has
documented read-only reconciliation, retain that evidence and explicitly mark
the local intent `reconciled` if a new separately authorized attempt is needed;
refresh/rebind its plan first. An external controller must clear its own durable
uncertainty/fence only after the same reconciliation.

## Validation

Run both suites from their skill directories:

```bash
python3 -m unittest discover -s tests -v
```

Tests use disposable Git repositories/worktrees, mocked service responses and
explicit test adapters. They cover exact tag adoption/collisions, ambiguous
view/edit/create/push results, stale target/releases, same-host process
serialization, plan binding, notes/history/latest semantics, and optional live
adapter rejection. They do not validate a production external gate or authorize
publication.
