---
name: generate-speckit-specify-prompts
description: Generate structured, ready-to-paste prompt blocks for /speckit.specify. Use when the user asks for a Speckit specify prompt, wants a new spec session prompt, or needs to translate a feature idea into a Speckit-ready input.
---

# Generate Speckit Specify Prompts

## Overview

Draft a complete, Speckit-compatible prompt block for `/speckit.specify` based on
the user's feature goal. Ensure the title is neutral (no "Speckit Specify Input")
and the content is scoped, testable, and ready to copy/paste.

## Workflow

1. Extract the user's feature goal and any constraints.
2. Produce a single markdown block with the required sections in this order:
   - Title (neutral, no "Speckit Specify Input")
   - Feature Summary
   - Why This Matters
   - Scope (in/out)
   - Constraints
   - Acceptance Criteria
   - Optional: "The X Points and What To Do" list (when provided or requested)
3. Keep the prompt concise and action-oriented. Avoid implementation details
   unless the user explicitly requests them.

## Output Template

```markdown
# <Neutral Title>

## Feature Summary
<1-3 sentences>

## Why This Matters
<1-3 sentences>

## Scope
- In scope:
  - <bullet list>
- Out of scope:
  - <bullet list>

## Constraints
- <bullet list>

## Acceptance Criteria
- <bullet list>

## The <N> Points and What To Do
1. <Point title>
   - <action>
```

## Notes

- If the user did not provide a numbered list of points, omit that section.
- If they asked to include the “what to do” steps, include the numbered list.
- Keep headings short and in Title Case.
