# TODO

## Publication

- Verify remote discovery with `npx --yes skills@latest add marcomc/skills --list`.

## Curation

- Recheck all bundled skills for public-safe paths, names, and machine-specific assumptions.
- Decide whether machine-local workflow skills should stay public or move to a private collection.
- Add first-party skills only with the `MARCOMC-SKILL` provenance marker; keep unmodified third-party skills outside the collection.

## Maintenance

- Before the next release, account for the incompatible `move-codex-chat` helper
  CLI migration when selecting the version and assembling release notes.
- Revalidate native chat movement, consent handling and installed-copy parity
  against the current Codex Desktop version before releasing `move-codex-chat`.
- Keep `README.md` and `CHANGELOG.md` updated when skills are added, removed, renamed, or moved.
- Re-run Markdown, shell, Python syntax, and `skills@latest` discovery checks before each release.
