# Chat reading

## Resolve membership

Discover the installed Codex app tools and use their current schemas. The names
below describe the current capabilities, not a private database contract.

- `list_projects`: resolve project ID, host and project root. Prefer explicit
  user selection, then the observer chat's verified project membership.
- Match returned project IDs and hosts when filtering chat listings. Resolve
  path aliases only to corroborate identity; repository proximity, a similar
  title or a shared directory prefix does not establish project membership.
  Sibling worktrees belong only when app metadata establishes the relationship.
- If more than one project remains plausible, request the project choice before
  reading message history. A non-Git project is a valid target.

## Enumerate and inspect

1. Use `list_threads` in `mode: "history"`, `source: "codex"`,
   `archived: false`, with the resolved `hostId` and a supported page limit.
   Follow every `nextCursor` for that same source, host and archive selection.
   Filter by project membership and deduplicate by host/thread ID. The recent
   sidebar list alone is not an exhaustive project inventory.
2. Record the resulting roster before interpreting status. Exclude the current
   observer chat from worker activity and avoid recycling earlier observer
   reports as independent evidence. Keep their IDs in the coverage note.
3. Read recent turns from every member worker chat with `read_thread`, normally
   starting with a few turns and `includeOutputs: false`. Follow its returned
   page cursor when the latest turns omit unresolved work, the governing goal,
   the reason for a blocker or a decision that changes the interpretation.
   Preserve the per-chat history depth and any truncation or missing page.
4. Parse responses locally before presenting results. Retain user messages,
   final assistant responses and relevant progress statements; avoid dumping
   command arguments, full transcripts or internal reasoning into the report.
   Read bounded tool outputs only when needed to substantiate a particular claim.
5. For running or attention-needed chats, prefer `wait_threads` with
   `timeoutMs: 0` for a compact status snapshot. Group at most eight targets,
   retain each target's host/cursor, and inspect per-target errors. One-off
   briefing does not require a polling loop or waiting for work to finish.
6. Recheck initially running or newly changing chats near the end. If activity
   changed during collection, state the scan interval and updated observation;
   do not portray the scan as an atomic snapshot.

Use the exact returned chat title when naming a source. Keep a separate short
outcome label for the work itself. Use returned source links when available;
otherwise retain title and thread/turn IDs in the evidence detail rather than
inventing a navigation URL.

## Interpret state

| Dimension | Interpret from evidence |
| --- | --- |
| Chat runtime | Running, idle, waiting for input/approval, failed or unavailable, according to the current tool response. Preserve unrecognized statuses as unknown. |
| Development readiness | Planned, being built, partial, implemented, verified or unknown, scoped to the actual capability and its evidence. |
| Work execution | Done, running, queued, waiting on another item, blocked, proposed for later or uncertain. |
| Blocker | Specific unmet dependency, failed acceptance check, external wait or pending decision, with an owner and release condition when established. |
| Evidence | Observed result, reported result, proposal, inference or unresolved contradiction. |

Idle is not proof of a pause, a blocker, abandonment or completion. A running
chat may be advancing an independent branch while the milestone is waiting.
Distinguish implemented, checked, merged, deployed and accepted when relevant;
use the weakest accurate milestone label rather than collapsing these stages.
Waiting and running describe execution, not how much capability has been built.
A renderer or checker file establishes a concrete implementation scope; its
presence alone does not prove the full workflow is integrated or qualified.

Read the project's existing goal/roadmap/status documents for missing direction
or consequential contradictions. Use targeted read-only repository or service
checks when authorized and needed to resolve a material readiness claim. Consult
available CLI guidance before service UI use. Avoid rerunning builds, tests or
production actions merely to generate an overview.

## Coverage and reuse

Each run enumerates the full current non-archived roster. For a refresh, reuse
previously read messages only when the saved project/host/thread identity and
available source revision or update marker still match and runtime is rechecked.
Read new, changed, running and attention-needed chats again. Label reused
evidence with its original observation time. If revision evidence is ambiguous,
reread rather than treating the old summary as current.

Track every member as read, safely reused or unreadable. Report inaccessible
hosts, failed pages, missing membership and unread chats as coverage gaps, not
empty work. Separate enumeration completeness from history depth and factual
confidence. Archived chats remain outside scope unless the user expands it.
