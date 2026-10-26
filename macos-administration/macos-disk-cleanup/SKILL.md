---
name: macos-disk-cleanup
description: Safely inventory and reclaim macOS disk space across the live boot Data volume, APFS purgeable snapshots, user and app caches, package-manager caches, and rebuildable artifacts. Use when the user asks to clean, reclaim, purge, audit, or free disk space on macOS; it defaults to read-only inventory and requires explicit apply or snapshot-thinning authorization.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# macOS Disk Cleanup

## Quick start

Run the bundled helper in read-only mode first:

```sh
bash scripts/mac_disk_cleanup.sh --dry-run
```

The default audit is fast and read-only. Add `--deep` when a full `du` traversal of the live Data volume is wanted; it can take many minutes on a large disk. After reviewing the inventory, use `--apply-safe` for rebuildable caches only. Use `--thin-snapshots <GiB>` separately when the user explicitly authorizes removal of local Time Machine restore points.

## Workflow

1. Establish the live target. Inspect `/System/Volumes/Data`, `df -h`, APFS snapshots, and local Time Machine snapshots. Do not treat a DaisyDisk breadcrumb such as `backup` as the live filesystem without comparing its paths and sizes against the Data volume.
2. Inventory the live boot Data volume and the user home directory. Use the helper's `--deep` mode for an exact whole-volume size ranking; the default mode inventories filesystem accounting and cache candidates without waiting for a multi-hundred-gigabyte traversal. Resolve friendly app labels to real container or group-container paths before acting.
3. Classify every large path:
   - rebuildable cache or generated artifact: eligible for `--apply-safe` after the activity guard;
   - package-manager cache: clear with the owning package manager (`npm cache clean` or `uv cache prune`), not generic recursive deletion;
   - user content, downloaded media, database, clipboard history, web-app site data, model, VM, Docker, or backup data: report only and use the owning app's controls;
   - system or protected data: never remove manually.
4. Apply safe cleanup only after a just-in-time activity check for each target. Resolve NPM and uv cache locations with their owning CLIs; only the defaults `~/.npm` and `~/.cache/uv` are supported. If a location is custom or cannot be resolved, skip cache cleanup and report it. Check open file handles with `lsof` and the owning process names; if a process is active, the handle check is inconclusive, or `lsof` is unavailable, skip that target and report it. Never terminate unrelated processes to make cleanup proceed.
5. Verify `df`, target sizes, package-manager cache integrity, APFS snapshot state, and the continued presence of current wallpaper or other app-critical state.

## Safe defaults

The helper may clear NPM's default cache at `~/.npm`, eligible direct children of `~/.cache` and `~/Library/Caches`, app-container `Data/Library/Caches`, group-container `Library/Caches`, and Xcode `DerivedData`. These are rebuildable but may cause downloads or rebuilds. It evaluates each direct child separately so an active cache does not block unrelated inactive caches and an inactive sibling is not protected merely because another tool is running. `uv` is handled through `uv cache prune` when `uv cache dir` resolves to its default `~/.cache/uv`; model caches, Codex runtimes, and cached virtual environments are preserved by the generic pass. Custom or unresolved package-manager cache locations disable cache mutations for that run.

Before every deletion, the helper checks the target recursively for open handles and checks relevant owner processes. It skips `~/.cache/uv` while `uv` is active, `~/.cache/codex-runtimes` while Codex or ChatGPT is active, NPM cache while an NPM-compatible package manager is active, Xcode build output while Xcode build processes are active, and snapshot thinning while Time Machine services are active. This is a best-effort point-in-time guard: a process can start after the check, so the helper must still report the exact target it attempted to clean.

It must not delete an entire container, group container, `Application Support`, `Documents`, downloaded books or podcasts, clipboard history, browser/web-app site data, ML models, Docker/VM storage, Mail, Photos, or a backup volume. It must not use `rm -rf` against `/`, `/System`, `/System/Volumes/Data`, or an unresolved wildcard.

APFS purgeable space is normally local snapshot or cache storage. `tmutil thinlocalsnapshots / <bytes> 4` is the supported snapshot operation, but it removes local restore points; external Time Machine backups are not affected. Never delete APFS snapshots by guessed UUID.

## Reporting

Report available space before and after, what was actually removed, what was intentionally preserved, snapshot effects, validation results, and any app that must be reopened or allowed to redownload data. Do not claim a broad cleanup from a scan of a stale snapshot.

See [REFERENCE.md](REFERENCE.md) for the classification rules and command-level safety notes.
