---
name: verify-data-preservation
description: Verify filesystem migrations and Photos or camera-media metadata work with persistent readback evidence before accepting preservation or synchronization claims.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Verify Data Preservation

Use for authorized filesystem relocation, migration restoration, Photos metadata
or camera-media preservation. It supplies verification criteria, not permission
to modify private stores, originals, cloud copies or synchronization settings.

- For filesystem copies, APFS metadata or Mutagen restoration, read
  [migration verification](references/migrations.md).
- For MP4 truncation, Photos originals, indexed metadata or scoped keyword work,
  read [media verification](references/media.md).

Retain distinct results for source identity, copied bytes/metadata, indexed state
and remote synchronization. Preserve unknown states and original evidence until
the requested boundary has actually been verified. Use existing authorized
tools; unsupported private transactions are historical evidence, not a workflow
to repeat. Keep identifiers, private paths and per-item rollback data private.
