---
name: gmail-filter-consolidation
description: Audit, consolidate, and safely remove orphaned Gmail filters using an installed Gmail CLI. Use for requests to reduce duplicate Gmail filters without changing their effective behavior.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Gmail Filter Consolidation

Audit a Gmail account's filters and reduce rule count only where the resulting
matching behavior and actions are preserved. Default to read-only analysis; do
not create or delete filters unless the user explicitly asks to apply a plan.

## Select and verify the CLI

- Prefer an installed Gmail-capable CLI. Check `gog` and `gws` before proposing
  installation or a new client.
- Identify the OAuth client/project and requested scopes before using it. A
  client registered under an unrelated application or project is a trust and
  ownership decision, not merely a technical detail. Do not silently reuse it.
- For `gog`, list filters with:

  ```sh
  gog --account ACCOUNT gmail settings filters list --json --results-only
  ```

  Use `gog gmail settings filters create` and `delete` only after write
  authorization. `gog` may require `--force` for forwarding filters.
- `gws gmail users settings filters list --params '{"userId":"me"}'` is a
  viable API fallback. Verify that its OAuth project and scopes are appropriate
  for the user's mailbox before any mutation.
- If the selected OAuth project has Gmail API disabled, explain the owner and
  project impact before enabling it. Never create a new Google Cloud project
  unless the user asks for one.

## Read-only audit

1. List filters and labels, preserving filter IDs, criteria, and actions.
2. Normalize actions as an exact fingerprint: added labels, removed labels,
   forwarding target, and category/system-label actions all matter.
3. Group candidates only when their action fingerprints are identical. A
   replacement may combine the criteria with an equivalent Gmail search query
   or a supported `from` expression.
4. Detect orphaned filters whose action is empty. They can be deletion
   candidates because they have no filtering effect.
5. Separately identify same-criteria rules whose actions are strict subsets of
   another rule. Remove only the truly redundant rule; Gmail filters cannot add
   more than one user label in a single rule, so do not attempt to merge such
   labels into one replacement.

Keep rules with different actions separate even if they share a label or a
sender. In particular, do not merge a rule that stars, archives, marks read,
categorizes, marks important, or forwards mail with one that does not.

## Apply safely

Before writes, present the count, candidate groups, expected final count, and
exceptions. Explicit user approval is required for creating or deleting Gmail
filters.

### Label rename safeguards

When an approved reorganization also renames labels, snapshot label IDs, names,
colors, and every filter's criteria and actions first. Preserve label IDs rather
than recreating labels. If a name-only update fails, inspect the existing color
against Gmail's supported palette; normalize only the affected unsupported
color, then read back the renamed label by ID and verify all historical filters
still have identical criteria and actions.

1. Create the non-forwarding replacements first.
2. Re-list filters and verify every replacement's criteria and action exactly.
3. Create forwarding replacements last, then promptly remove their source
   filters to minimize duplicate forwarding.
4. Delete source filters by IDs obtained from a fresh API listing, not manually
   transcribed IDs. Stop immediately on any unexpected `404`, permission
   failure, or action mismatch.
5. Re-list and validate the final count, the absence of every source ID, and
   the presence of every replacement. Check explicitly preserved exceptions.

If a replacement creation fails, leave its source filters intact and revise the
plan. Do not claim that a rule was consolidated solely because another rule
looks similar in the Gmail UI.
