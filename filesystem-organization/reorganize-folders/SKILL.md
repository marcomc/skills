---
name: reorganize-folders
description: Safely analyze and reorganize an arbitrary directory tree into a cleaner taxonomy using only move and rename operations. Use when asked to audit folders, propose a new file tree, rename directories in a chosen language, infer the default naming language from first-level folder names, protect sync-managed folders, preview a proposed structure before applying it, generate a rollback plan, or restore a prior state from a rollback plan without deleting files.
---

# Reorganize Folders

## Overview

Use this skill to reorganize a local directory tree into a cleaner structure without deleting
files. Start with analysis and preview, then apply only `move` and `rename` operations after
approval. Every applied run must emit a rollback plan that can later be consumed by the same
skill to restore the previous layout.

For implementation-oriented work such as turning this workflow into automation, read
[references/automation-notes.md](references/automation-notes.md).
For the rollback file contract, read
[references/rollback-plan.md](references/rollback-plan.md).

## Required Inputs

Collect or infer these inputs before planning:

- Root directory to analyze.
- Whether the user wants:
  - analysis only
  - preview plus approval
  - execution of an already approved plan
  - restoration from a rollback plan
- Optional target naming language for folder names.
- Optional rollback plan path for restore mode.
- Optional constraints such as:
  - preserve some folders exactly as they are
  - avoid touching app-managed folders
  - prefer shallow reorganization over deep normalization

## Language Policy

Use this decision order for folder naming:

1. If the user specifies a target language, use it for newly created or renamed folders.
2. Otherwise infer the default language from meaningful first-level folder names.
3. Ignore tokens that do not help language detection:
   - dates
   - numbers
   - acronyms
   - hidden folders
   - app-managed or sync-managed folders
4. If one language clearly dominates the first meaningful level, use that language for new names.
5. If language inference is weak or mixed, preserve existing names where possible and ask once
   before broad renaming.

Do not translate proper nouns, product names, legal titles, or exact historical labels unless
the user explicitly requests that.

## Safety Rules

Follow these rules on every run:

- Never delete files or folders as part of the reorganization.
- Never overwrite an existing file silently.
- Always preview the proposed tree before applying filesystem changes unless the user explicitly
  says to execute a previously approved plan.
- Prefer whole-folder moves when a folder is already semantically coherent.
- Prefer merging children into an existing destination when the destination already exists.
- Leave protected, external, or app-managed folders alone unless the user explicitly approves
  moving them.
- Keep hidden metadata folders untouched.
- Treat historical material conservatively and prefer moving it into `Archive` over forcing it
  into an uncertain category.
- Generate a rollback plan before the first filesystem change of every applied run.
- In restore mode, preview the reverse moves before applying them unless the user explicitly asks
  for immediate rollback execution.

## Protected Folder Rules

Mark a folder as protected or high-risk if any of these are true:

- The name starts with `.` and looks like metadata or sync state.
- The folder is clearly managed by an app or cloud integration.
- The folder is a well-known export or sync mount that may be interpreted by external software.
- The folder appears to be a system container rather than user content.

When protected folders are present:

- keep them in place by default
- mention them in the preview
- move them only with explicit user approval

## Workflow

### Step 1: Inventory

Scan the target tree first. Collect:

- top-level folders
- folder counts and file counts
- representative child names
- representative filenames
- common extensions
- date patterns
- person names or project names when obvious

Build a compact profile for each folder before deciding anything.

### Step 2: Detect Coherent Buckets

Use deterministic heuristics first. Look for stable themes such as:

- personal administration
- travel
- office or work
- projects or brands
- vehicles
- media
- lifestyle and hobbies
- people and shared
- software and tech
- reference and notes
- archive
- inbox

Treat current folder location as a weak signal. Prefer folder meaning over current placement.

### Step 3: Decide Reorganization Depth

Choose the shallowest safe transformation:

- If a folder is already coherent, move it as a whole.
- If a folder is mixed but its children are coherent, reorganize at child level.
- If a folder is ambiguous, route it to `Archive` or `Unclassified` rather than overfitting.

Do not deep-normalize every branch just because it is possible.

### Step 4: Build the Target Taxonomy

Create a proposed target tree using only the categories that are actually needed.

Use these naming principles:

- keep names short
- keep names descriptive
- use the target language decided above
- preserve dates exactly
- preserve proper nouns
- avoid artificial numeric prefixes unless the user explicitly wants them

### Step 5: Preview Before Apply

Before changing the filesystem, show:

- the proposed top-level tree
- selected deeper branches up to four or five levels when useful
- key mappings in the form `source -> destination`
- protected folders that will remain untouched
- open questions or low-confidence placements

If the user asks for safety, always stop here and wait for approval before applying changes.

### Step 6: Ask For Confirmation

Before applying a reorganization plan, ask for confirmation in plain language. Confirm that:

- the target tree looks correct
- the naming language is correct
- protected folders left untouched are acceptable
- move and rename only is acceptable

Do not start execution until the user approves, unless the user explicitly instructs immediate
execution.

### Step 7: Build a Move-Only Plan

Convert the proposal into operations such as:

- create destination directory
- move folder
- rename folder
- merge children into destination
- remove empty source directory only after successful moves

Never include delete operations in the plan.

### Step 8: Generate a Rollback Plan

Before the first move, generate a rollback plan file that records:

- the root directory
- the plan creation timestamp
- the target naming language or inferred language
- the forward operations
- the reverse operations needed to restore the prior state
- any skipped or protected paths

Use a deterministic, machine-readable format. Prefer JSON. Use the schema described in
[references/rollback-plan.md](references/rollback-plan.md).

Unless the user requests a different location, store the rollback file under:

- `<root>/.reorganize-folders/rollback-YYYYMMDD-HHMMSS.json`

Mention the rollback file path in the execution summary.

### Step 9: Execute Conservatively

Apply operations in this order:

1. Create destination directories.
2. Move the most specific children before removing old containers.
3. Merge existing destinations without overwriting.
4. Remove empty source directories only when they are truly empty.
5. Keep a clear operation log.

If a collision appears:

- stop silent overwrite
- either keep both names or ask the user
- prefer no-op over risky merge

### Step 10: Verify

After execution, rescan and verify:

- the top-level layout matches the plan
- no source content was lost
- protected folders were preserved
- old parallel containers were actually consolidated
- unexpected leftovers are reported explicitly

## Restore Mode

If the user provides a rollback plan and asks to restore a prior state:

1. Load and validate the rollback plan.
2. Check that the current root matches the plan's expected root.
3. Verify that the referenced current paths still exist where expected.
4. Build a reverse preview in the form `current -> original`.
5. Ask for confirmation unless the user explicitly asks for immediate restore execution.
6. Apply reverse moves in the reverse-safe order defined by the plan.
7. Rescan and verify that the original structure was restored as closely as possible.

If the current filesystem no longer matches the rollback plan closely enough for safe restore,
stop and explain the mismatch instead of guessing.

## When To Use AI

Use AI only for genuinely semantic or ambiguous parts:

- classifying a folder whose meaning is unclear
- choosing between multiple plausible categories
- generating a clean folder name in the target language
- synthesizing a compact taxonomy for mixed content

Do not use AI for:

- filesystem scanning
- collision detection
- directory creation
- file moving
- rename execution
- post-run verification

## Expected Output

When working with this skill, produce:

- a concise explanation of the current structure
- a proposed target tree
- a mapping list for major moves
- any language assumptions
- a clear statement that the execution uses move and rename only
- the rollback plan path for applied runs
- a brief restore instruction for that rollback plan
- a post-run verification summary if changes were applied

## Escalation Rules

Pause and ask the user before applying if any of these are true:

- the destination language is unclear and renaming would be widespread
- app-managed folders would need to move
- collisions require content-aware merging
- the user asked for analysis first
- the tree contains many ambiguous folders that would otherwise be archived by default
- the rollback plan cannot be written to the default location
- restore mode detects mismatches between the current tree and the rollback plan
