---
name: sync-codex-skills
description: Sync Codex-facing skill mirrors from the canonical ~/.agents/skills tree into ~/.codex/skills. Run after adding or updating any shared skill.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Sync Codex Skills

Run the sync script to update all Codex-facing skill mirrors from the canonical agents sources:

```bash
bash ~/.Codex/sync-codex-skills.sh
```

To sync a single skill only:

```bash
bash ~/.Codex/sync-codex-skills.sh <skill-name>
```

After running, report how many skills were synced and whether any were skipped.

The canonical skill source is `~/.agents/skills`. The sync script mirrors those skills into `~/.codex/skills` as symlinks so both agent runtimes see the same skill set without keeping duplicate copies.
