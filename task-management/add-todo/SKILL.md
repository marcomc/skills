---
name: add-todo
description: Capture one or more user ideas and add them to the active project TODO artifact with a Propositions section. Use when the user asks to record, triage, or structure future work ideas into either a Markdown TODO file or a Kanban JSON file.
---

# Add Todo

## Workflow

1. Locate the project TODO artifact.

- Prefer `TODO.kanban` when present.
- Otherwise use the primary Markdown TODO file (for example `TODO.md`).
- If multiple candidates exist, choose the one already used as the backlog source in the repository.

1. Parse user ideas.

- Accept one or more free-form ideas from the user message.
- Split compound ideas into distinct propositions only when they describe independent deliverables.
- Keep the original intent, but rewrite each proposition in technical language.

1. Create a proposition entry for each idea.

- Assign a concise technical title (initiative-style, implementation-oriented).
- Write a short assessment description focused on feasibility/risk/value.
- Add a concrete action list that can drive future implementation decisions.

1. Update TODO content according to file type.

- For Markdown TODO files:
  - Ensure a `## Propositions` section exists; create it if missing.
  - Add each proposition as a checklist block with title, description, and action bullets.
- For Kanban JSON files:
  - Ensure a `Propositions` list exists; create it if missing.
  - Add one parent proposition card per idea with description and acceptance framing.
  - Add child action cards linked to that idea.

1. Apply Kanban labeling discipline.

- Create one unique label per proposition (for example `idea:observability-audit`).
- Attach that label to all cards created for that idea.
- Never reuse that label for unrelated cards.
- Reuse the same label only for future cards that belong to the same proposition.

1. Preserve repository conventions.

- Keep existing schema, ordering, and metadata style untouched outside the new proposition entries.
- Preserve UUID requirements for Kanban IDs when the file uses UUIDs.
- Respect project-specific rules in `AGENTS.md` before editing TODO artifacts.

## Output Requirements

- Return a short summary including:
- target file updated,
- proposition titles created,
- label(s) created (for Kanban),
- action count per proposition.

- Keep proposition actions concrete and implementation-ready. Avoid vague tasks like "investigate" without scope.
