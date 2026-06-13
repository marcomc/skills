# Automation Notes

## Purpose

Use this reference when the task is to implement or automate the folder reorganization workflow.
Split the workflow into deterministic filesystem logic and AI-only semantic decisions.

## Folder Profile Schema

For each folder, collect:

- `path`
- `depth`
- `child_dir_count`
- `file_count`
- `sample_child_dirs`
- `sample_files`
- `dominant_extensions`
- `date_tokens`
- `semantic_keywords`
- `language_hint`
- `protected_flag`
- `category_candidates`
- `confidence`

## Deterministic Responsibilities

Use standard code for:

- walking the tree
- filtering hidden folders
- counting files and subdirectories
- extracting extensions
- detecting dates
- detecting collisions
- creating destination directories
- executing move and rename operations
- writing rollback plans
- replaying rollback plans
- verifying before and after state

## AI Responsibilities

Use AI only for:

- ambiguous category assignment
- compact taxonomy synthesis
- target folder name generation in the selected language
- low-confidence conflict resolution advice

## Default Category Set

Start from this stable set and omit unused categories:

- `Inbox`
- `Personal`
- `Travel`
- `Office`
- `Projects and Brands`
- `Vehicles`
- `Media`
- `Lifestyle and Hobbies`
- `People and Shared`
- `Software and Tech`
- `Reference and Notes`
- `Archive`
- `Unclassified`

## Language Inference Rules

Infer the default naming language from meaningful first-level folder names:

1. Read first-level directory names.
2. Ignore dates, numbers, acronyms, hidden names, and obvious app-managed folders.
3. Detect the dominant language from the remaining lexical tokens.
4. If confidence is high, use that language for new names.
5. If confidence is low, preserve existing names and ask once before broad translation.

## Planning Algorithm

```text
scan root
build folder profiles
mark protected folders
classify folders with deterministic rules
send only low-confidence cases to AI
build target taxonomy
choose shallowest safe move depth per folder
generate move-only plan
preview source -> destination mapping
wait for approval when required
write rollback plan before first move
execute create/move/rename/merge-empty-parent cleanup
verify final tree and report leftovers
```

## Execution Constraints

- Never delete user content.
- Never overwrite existing files silently.
- Prefer whole-folder moves over deep reshuffles.
- Prefer `Archive` over forced categorization when confidence is low.
- Preserve proper nouns and exact dates.
- Keep app-managed folders in place by default.
- Always generate a rollback plan for applied runs.
- Validate rollback plans before restore execution.

## Suggested Python Modules

- `scanner.py`
- `classifier.py`
- `taxonomy.py`
- `planner.py`
- `executor.py`
- `verifier.py`
- `ai_adapter.py`
- `rollback.py`

## Minimal AI Contract

Pass to AI:

- folder path
- sampled child names
- sampled filenames
- rule-based candidate categories
- target language or language hint

Expect from AI:

- best category
- confidence score
- suggested folder label
- short rationale
