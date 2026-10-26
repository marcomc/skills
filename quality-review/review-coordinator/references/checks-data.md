# Data and presentation boundaries

Use only for the affected contracts. These are prompts for concrete evidence,
not a checklist to append to every review report.

- Preserve sentinel/default meaning through normalize, save, merge, reload and
  display: omitted/null/empty, disabled, `all`, `auto`, `default` and `inherit`.
  Normalize fallback-bearing sentinels before defaults without losing fallback.
- Follow admitted configurations through all importers, registries, persisted
  restore and clients. Test commands against effective merged config when globs
  or private overrides may shadow a dedicated registry. Keep immutable active
  sessions distinct from mutable next-session selection.
- Keep bounds/enums consistent across schemas, UI, validators, docs and runtime.
  Charge failed attempts where a batch limit bounds total work.
- Use stable IDs where names collide. Plans for rename, export, copy or generated
  output must detect future target collisions before destination files exist.
  Reject self/descendant directory moves and preserve intended URL/path identity,
  including encoded filenames and Unicode representation.
- Test already-qualified/canonical inputs without a second normalization, and
  preserve fallback data when enriched metadata lacks downstream-required fields.
- Prove expected not-found/stale/invalid cases retain their intended status,
  alongside alternate supported flat/nested content shapes and normal successes.
- Regenerated charts and other editable artifacts must preserve ranges, geometry,
  formatting, orientation, nulls and API-specific properties through success,
  rollback and recovery. Localized sentinels belong to the correct field; compare
  formula-backed displayed values and a locale switch across styling/renderers.
- Update all changed user-visible labels, options, messages and locales. Include
  a case where differing diagnostic context changes the actual rendered message.
- Review source, installed bundle, generated schema/assets and runtime consumers
  when packaging changes their behavior. A helper-only test may miss the real
  entrypoint, installed topology or persistence boundary.

Prefer parameterized cases and shared setup for equivalent behavior. A distinct
failure mechanism deserves its own proof; a Cartesian product of unrelated
dimensions does not establish better coverage.
