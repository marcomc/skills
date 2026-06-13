---
name: generate-speckit-constitution-prompts
description: Generate structured, ready-to-paste prompt blocks for /speckit.constitution. Use when the user asks for a Speckit constitution prompt or wants to prepare a constitution update session.
---

# Generate Speckit Constitution Prompts

## Overview

Draft a complete, Speckit-compatible prompt block for `/speckit.constitution`
using only the user-provided intent. Do not rely on prior chat context; ask
for missing inputs or use neutral placeholders when needed.

## Workflow

1. Gather required inputs from the user (project name, scope, principles, dates).
2. Produce a single markdown block with the required sections in this order:
   - Title (neutral, no "Speckit Constitution Input")
   - Project Context
   - Non-Negotiables
   - Governance (amendment/versioning rules)
   - Dates (ratification, amendment)
   - Optional: Tooling and workflow constraints
3. Keep the prompt concise, testable, and policy-focused. Avoid implementation
   details unless the user explicitly requests them.

## Output Template

```markdown
# <Neutral Title>

## Project Context
<1-3 sentences>

## Non-Negotiables
- <bullet list>

## Governance
- Amendment procedure
- Versioning policy
- Compliance review expectations

## Dates
- Ratification: <YYYY-MM-DD or TODO>
- Last amended: <YYYY-MM-DD or TODO>

## Tooling and Workflow (optional)
- <bullet list>
```

## Notes

- If the user provides exact principles, use their wording.
- If dates are unknown, include TODO placeholders.
- Keep governance rules declarative and testable.
