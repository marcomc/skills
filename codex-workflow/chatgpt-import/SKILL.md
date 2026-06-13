---
name: chatgpt-import
description: Import one or more ChatGPT desktop conversations into the current Codex task as an English, coding-ready summary. Use when the user wants prior ChatGPT research, design notes, debugging context, or project investigations brought into Codex for software work, especially by topic rather than exact chat title.
---

# ChatGPT Import

Import useful knowledge from ChatGPT into the current Codex task in a format that is immediately useful for programming work.

Primary source:

- `ChatGPT.app` with `Computer Use`

Secondary source:

- Atlas CLI only for quick discovery of titles or conversation URLs when available

## Workflow

### 1. Define the search target

Start from the user's topic, project name, feature, bug, or investigation area.

Prefer this order:

- Exact conversation title if the user gives one
- Project or feature name
- Technical nouns, repo names, APIs, errors, libraries, models, or product names
- Closely related synonyms if the first search is too narrow

If the topic is broad, narrow toward the programming outcome that matters now.

## 2. Discover candidate conversations

Use `ChatGPT.app` as the primary navigation surface.

Preferred approach:

- Open `ChatGPT.app`
- Use the sidebar search to find candidate conversations
- Select the most relevant result first

Optional acceleration:

- If Atlas CLI is available, use it only to discover likely conversation titles or `chatgpt.com/c/...` URLs
- Do not treat Atlas CLI as the source of conversation content unless it can actually expose the content, which is usually not the case

Prioritize conversations that are:

- Clearly about the requested topic
- Rich in implementation detail
- More recent when relevance is otherwise similar

When multiple conversations cover the same topic, import more than one if they add distinct information.

## 3. Extract usable evidence

Read the conversation content from `ChatGPT.app` using `Computer Use`.

Collect:

- Concrete facts
- Design decisions
- Constraints
- Code or config snippets
- Commands
- Error messages
- Open questions
- Trade-offs
- Action items

Do not try to mirror the full transcript if that is unnecessary. Extract enough evidence to preserve the useful technical meaning.

If the conversation is long:

- Read the parts that carry technical weight
- Scroll as needed
- Prefer sections with code blocks, commands, architecture notes, bug context, or explicit decisions

## 4. Merge across conversations

When multiple conversations are relevant:

- Deduplicate repeated facts
- Preserve contradictions explicitly
- Separate confirmed facts from suggestions or speculation
- Keep the most implementation-relevant details

If two conversations disagree:

- State the conflict clearly
- Prefer the more specific or more recent source only as an inference, not as a hidden assumption

## 5. Translate to English

Always produce the final imported summary in English.

Rules:

- Translate source material even if the original chat is in another language
- Preserve technical identifiers, code, commands, API names, filenames, URLs, and error strings exactly when needed
- Keep domain meaning intact; do not over-polish away useful nuance

## 6. Produce a coding-ready summary

The output must be directly reusable for software work in Codex.

Use this structure:

````md
## Topic

## Imported Conversations
- CONVERSATION TITLE OR IDENTIFIABLE LABEL

## Key Facts
- ...

## Decisions
- ...

## Constraints
- ...

## Implementation Notes
- ...

## Commands / Code / Config
```text
...
```

## Open Questions
- ...

## Actionable Spec for Codex
- ...

## Source Trace
- CONVERSATION LABEL - WHY IT MATTERED
````

Formatting rules:

- Keep it concise but technically complete
- Prefer flat bullets
- Keep code blocks only for commands, snippets, or config worth reusing
- Distinguish facts from assumptions

## Quality bar

The import is successful only if the result lets Codex move faster on a programming task.

Good imports:

- Reduce ambiguity
- Surface decisions already made
- Preserve commands and technical details worth reusing
- Convert scattered chat context into implementation-ready guidance

Weak imports:

- Read like generic prose
- Omit technical specifics
- Lose uncertainty or contradictions
- Keep the original language instead of English

## Failure handling

If discovery finds no strong match:

- Say that clearly
- Report the best near matches briefly
- Ask for a narrower topic, exact title, or additional keywords only if needed

If the chat is found but the visible content is insufficient:

- Import what is confirmed
- State that the extraction was partial
- Note what additional scrolling or user guidance would improve completeness

If Atlas CLI and `ChatGPT.app` disagree:

- Trust `ChatGPT.app` for content
- Treat Atlas as discovery metadata only
