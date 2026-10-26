# macOS Disk Cleanup Reference

## Path classification

| Path kind | Default action | Reason |
| --- | --- | --- |
| `~/.npm` | Clear with `npm cache clean --force` | Supported only when `npm config get cache` resolves exactly to this default; NPM recreates it on demand |
| `~/.cache/*` | Clear eligible children after activity checks | Some children are model stores, runtimes, or virtual environments |
| `~/.cache/uv` | Run `uv cache prune` only when `uv` is inactive | Supported only when `uv cache dir` resolves exactly to this default; lets uv remove dangling entries and cached environments using its own semantics |
| `~/.cache/whisper`, model stores | Preserve by default | Model files are feature assets and may be required offline |
| `~/.cache/codex-runtimes`, cached virtual environments | Preserve by default | Deleting them can disrupt the current tool or require reinstallation |
| `~/Library/Caches/*` | Clear contents | Rebuildable user caches |
| `~/Library/Containers/*/Data/Library/Caches` | Clear contents | Rebuildable sandbox caches |
| `~/Library/Group Containers/*/Library/Caches` | Clear contents | Rebuildable shared caches |
| Xcode `DerivedData` | Clear contents | Rebuildable build output |
| `Application Support`, `Documents`, databases | Preserve | Usually app state or user data |
| Books, Podcasts, Photos, Mail, PastePal history | Preserve | Downloaded or user-visible content |
| Safari Web App nested containers | Preserve | Logins, local storage, offline state |
| AI/ML model directories | Preserve | Feature assets; may be required offline |
| Docker, VM, backup, and external volumes | Preserve | Potentially large but not disposable |

## APFS interpretation

Use the live Data volume as the accounting source:

```sh
df -h /System/Volumes/Data
diskutil apfs listSnapshots /System/Volumes/Data
tmutil listlocalsnapshotdates /
```

Purgeable snapshots can be thinned with an explicit byte target:

```sh
tmutil thinlocalsnapshots / 20000000000 4
```

This trades local snapshot restore history for free space. It does not delete files from the live Data volume or a Time Machine destination, but the operation is not reversible through the local snapshot list.

## Inventory cautions

- DaisyDisk or another scanner may be displaying an APFS snapshot. Compare its breadcrumb, `df`, and live `du` output before deleting anything.
- Friendly app names may represent UUID-named containers or multiple paths. Resolve the bundle identifier and inspect child directories.
- A folder named `Cache` can still contain downloaded offline media. Prefer the owning app's remove-download control when the content is user-visible.
- Keep current wallpaper paths and app processes in mind before clearing generated image caches.
- A mutation must perform a just-in-time `lsof` check for the exact target. Also check known owner processes (`uv`, Codex/ChatGPT, NPM-compatible package managers, Xcode build tools, and Time Machine services); skip and report the target if any are active or if the handle check cannot be completed.
- Treat `lsof` warnings or diagnostics as inconclusive, even when its exit status is also used for an empty handle list. Preserve the affected target.
- Dry runs must not invoke `npm cache verify`: verification can garbage-collect the cache. Run it only after authorized NPM cleanup and report a verification failure.
- Before applying any cache cleanup, resolve cache locations with `npm config get cache` and `uv cache dir` when those tools are installed. Custom or unresolved locations skip all cache mutations for that run; do not add arbitrary or external cache paths to the cleanup set.
- Process-aware cleanup is deliberately best-effort rather than a lock: a process can start after the check. Recheck immediately before each target and never terminate a process to force cleanup.
- A successful deletion is not proof of durable free space until APFS snapshots are rechecked and `df` is measured again.
- A deep `du` scan is intentionally opt-in because APFS volumes with hundreds of gigabytes and millions of files can take many minutes to traverse.
