---
name: version-breaking-change-analysis
description: Compare two versions of a software component or plugin, find documented breaking changes, and determine their evidence-backed impact on a target project. Use for upgrade compatibility checks, not for applying the upgrade.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Version Breaking Change Analysis

Assess an upgrade from a known version to a target version and answer whether
documented incompatibilities affect the target project. This is an analysis
skill: do not change versions, edit code, create migration files, or deploy
unless the user separately asks.

## Resolve the target project

- With no project argument, use the current working directory.
- If the user names the current project or supplies its current path, use the
  current working directory; do not duplicate the scan.
- For a different named project, look for an exact directory or repository name
  in the accessible workspace and configured project contexts. Search locally
  before asking, but keep the search bounded; do not crawl an entire disk.
- If the requested project cannot be resolved unambiguously, ask for its path
  and stop before assessing impact.
- State which project and revision or working-tree state were examined. A
  repository scan cannot establish the configuration of a separate deployed
  environment.

## Establish the version interval

Confirm the component identity, edition or distribution, old version, and new
version. Resolve versions from repository manifests, lockfiles, image tags,
charts, build configuration, or user-provided values; distinguish declared,
resolved, and deployed versions when they differ. If any required value remains
ambiguous, request it rather than guessing.

Review every released version after the old version through and including the
new version. Account for skipped versions, prereleases, release trains, and
renamed packages. Classify the change as patch, minor, major, baseline, or
vendor-specific equivalent only when that scheme is documented; version numbers
alone do not prove compatibility.

## Gather authoritative change evidence

Prefer sources in this order:

1. Official release notes, changelog, upgrade or migration guide, and security
   advisory.
2. The component's official source repository: release pages, tagged source
   diffs, issues, pull requests, and documentation history linked by the
   release notes.
3. Official compatibility matrices, API references, schema references, and
   package metadata.
4. Maintainer-authored downstream documentation only when primary evidence is
   unavailable; label it accordingly.

Read the complete interval, not merely the destination release page. Follow
links for items described as breaking, incompatible, removed, deprecated with a
removal deadline, security-hardening, changed default, migration, upgrade
required, or minimum-runtime change. When notes are incomplete, inspect the
relevant tagged diff and cite the uncertainty; do not convert an unexplained
code diff into a confirmed breaking change.

For every relevant change, capture the affected versions, exact contract or
behavior, required migration, and supporting source link. Treat a security fix
as an urgency signal separately from a compatibility verdict.

## Map changes to the project

First identify how the component is present: direct versus transitive
dependency, plugin or extension registration, runtime image, build tool,
configuration provider, generated artifact, or external service. Then search
tracked project material for each affected surface, including:

- imports, APIs, classes, commands, endpoints, and feature flags;
- configuration keys, schemas, environment variables, templates, and values;
- plugin declarations, dependency constraints, lockfiles, and compatibility
  metadata;
- startup, deployment, CI, and container definitions; and
- tests, examples, scripts, documentation, and generated artifacts where they
  define runtime input.

Search for the old and replacement names as well as related configuration
paths. Inspect matches in context and follow their call sites or rendered
configuration far enough to decide whether the changed behavior is exercised.
Do not infer non-use from an absent literal when the project can construct the
value dynamically, delegate it to an external system, or hold it in untracked
runtime configuration.

Classify each documented breaking change as one of:

- **Affected** — a project use reaches the changed contract; name the file and
  required adaptation.
- **Likely affected** — evidence strongly suggests use, but a runtime or
  external configuration fact is missing.
- **Not observed in repository** — the component is present but the changed
  surface was not found in tracked material; state the search boundary.
- **Not applicable** — reliable evidence proves the feature or integration is
  unused for this project.
- **Cannot assess** — source, version, target project, or runtime evidence is
  insufficient.

Do not report an upgrade as safe merely because no repository match was found.
Call out transitive dependencies, plugin-to-core compatibility, minimum
runtime requirements, and manual or hosted configuration separately when they
are relevant.

## Report in chat

Return a concise chat report by default; do not create a report, migration
guide, script, branch, commit, or project file unless explicitly requested.
Use this shape, omitting empty sections:

| Item | Result |
| --- | --- |
| Component | `<name>: <old> -> <new>` |
| Target | `<project path and examined revision/state>` |
| Verdict | `affected`, `likely affected`, `no tracked impact observed`, or `cannot assess` |

Then list only material breaking changes with their impact class, concrete
project evidence, and one or two authoritative links. End with the smallest
next action: a specific code/configuration change, a targeted runtime check, or
approval to proceed with the upgrade analysis. Mention security urgency and
evidence gaps in one line each when applicable. Keep raw changelog summaries,
unchanged releases, and exhaustive search logs out of the default response;
provide them only on request.
