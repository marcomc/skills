# Recurring runs and handoffs

## Refresh and scheduling

A manual invocation produces one dated brief and stops. A skill is not a
background watcher and does not install a startup hook by itself.

When the user requests an actual recurring schedule, discover the current
`automation_update` capability and use its current schema. Prefer a heartbeat
in the dedicated observer chat unless the user wants a separate task each run.
Resolve cadence, local timezone and target project; request missing scheduling
information only when it blocks configuration. A statement that the skill
should support periodic use is not an instruction to create a schedule now.
Do not write cron files, raw automation directives or invent model IDs.

Bind scheduled prompts to the verified project/host, name `$project-visual-brief`,
preserve read-only behavior, and request a fresh visual plus material changes.
Capture the requested output language at scheduling time; scheduled runs have
no new live utterance from which to infer it. Use that language until changed.
Keep notification preferences in the automation's supported fields. For an
unchanged run, report that compactly without repeating a long project narrative.

Persist only the evidence model, source/version references, coverage and visual
outputs needed for comparison, in a private task-owned location. Avoid raw
transcripts, secrets and access-bearing URLs. Compare only matching project/host
baselines and disclose partial scans. Treat vanished or archived sources as
membership changes; a disappearing chat does not establish completed work.

## Destination-chat drafts

Generate drafts only when a grounded finding offers a concrete benefit. Keep
each brief, normally under 150 words, with:

- exact destination chat title and ID;
- observation time and source references;
- the useful project outcome at stake;
- a proposed bounded next step and success condition;
- any proposed deferral, trade-off and return condition;
- a request to reconcile the suggestion with newer work and current instructions.

The receiving chat owns its implementation plan. A snapshot's suggestion
does not supersede its latest user decisions. Keep the draft labeled as a draft.

Use `send_message_to_thread` only after the human explicitly instructs sending
the relevant draft or a clearly defined set of drafts. Before dispatch, recheck
destination project/host, exact title and runtime status. Preserve an instruction
to avoid interruption: leave running chats a draft for later; do not send now,
pause them or create an unsolicited watcher. If a send outcome is uncertain,
reconcile through read-only history before considering another attempt.

## Optional learning

Use existing learning skills only for their actual remit. A project blocker or
an assistant recommendation alone is not a reusable agent lesson.

- `record-agent-learning`, when available: capture an evidenced recurring
  failure, applied correction or concrete prevention lesson under its rules.
- `codex-review-skill-autolearn`, when available: review-process improvements
  grounded in completed review evidence.
- `workflow-retrospective`, when available and requested: a bounded analysis of
  evidenced execution friction in the selected chats. Pass source references,
  preserve its checkpoint and authority boundaries, and keep any worker change
  outside this observer's default read-only scope.
- Retro or other retrospective tooling: use when explicitly requested and
  available; otherwise provide the small observation directly in the brief.

Keep these optional. Do not install skills, change worker instructions, rewrite
global memory or add learning notes merely to complete a routine status update.
