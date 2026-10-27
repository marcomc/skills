---
name: moneywiz-reconcile
description: Verify and reconcile MoneyWiz accounts against bank, investment and crypto sources using CLI-first reads and writes, with GUI fallback for a single operation and automatic return to CLI. Maintain a private per-user profile and resumable transaction plan for monthly updates, imports, transfer repairs and payee cleanup.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# MoneyWiz reconciliation

Complete the requested review with source-backed transactions, correct relationships
and verified reconciliation flags. Keep personal accounting choices and data in a
private profile outside this generic skill.

## Start and resume

1. Resolve the private profile from the request or project instructions. Load its
   current policies and latest checkpoint before historical notes. If absent, create
   a private per-user file from [profile template](references/profile-template.md)
   once the user identity and private location are established.
2. Determine scope, account order, import cutoff, the current MoneyWiz account
   inventory, the user's configured reminder/task system if one is used, and
   existing authority. MoneyWiz accounts define the checklist; reminder entries
   provide per-account source and method notes. Do not derive reconciliation scope
   from reminder entries or MoneyWiz rows currently marked unreconciled alone.
   Use stable reporting groups from the private profile. Group membership is a
   reporting and coverage key; it does not replace account identity, currency or
   active/archive status.
   Analysis/proposal requests do not authorize live reconciliation. Saved amounts
   are historical observations, never future targets.
3. Discover installed `moneywiz`, app bundle, active database and command help.
   Confirm a known recent record is in that store. Resolve saved numeric IDs again
   by owner, account identity, currency and product; distinguish archived accounts.
4. Prefer source CLI, then API/connector, then the authorized external browser/profile
   or iPhone source. Use MoneyWiz CLI first for every read and write. Discover
   capability separately per operation; do not assume all writes work or are blocked.
5. Read [account workflow](references/account-workflow.md). Load
   [CLI operations](references/cli-operations.md) when selecting a read, writer or
   recovery command. Load [UI and runtime techniques](references/ui-and-runtime.md)
   for native interaction,
   authentication, deep links or failed CLI reads.

## CLI first, fallback for one operation

The default route for **every operation**, including after a GUI fallback, is the
installed `moneywiz` CLI. Check current help, completeness and the exact operation's
runtime/store admission; an enabled or verified capability is still bounded by its
native preconditions. Use the CLI for supported operations within existing authority.

If the CLI cannot complete a particular operation correctly, record its failure or
unsupported contract and use Computer Use only for that operation. Correct a clear
input error through the CLI first; do not loop identical failed commands. GUI fallback
requires the same identity, source evidence and authorization as a CLI write. Missing
authority or unresolved financial identity is not a reason to switch tools.

After the GUI operation, verify persistence, record its outcome and **automatically
return to CLI for the next operation**, even on the same account. No user reminder
is needed. Never make GUI fallback sticky for an account, operation type or session.
Let sync settle, refresh affected CLI reads/guards and rebuild stale plans; close
MoneyWiz before the next native CLI write. If CLI read-back still fails, verify that
operation through the GUI, retain the read limitation and start the next operation
with CLI again.

A timed-out write has an **unknown outcome**, not permission to create it again in
the GUI. Inspect persisted rows and use `write recover` first. If unresolved, keep
that operation pending and continue independent work through CLI. See
[CLI execution and recovery](references/cli-operations.md#execution-and-recovery).

## MoneyWiz account coverage and reminder notes

Before applying any reconciliation, enumerate the current MoneyWiz accounts from
the active store and resolve each account by owner, currency, product and
active/archive status. If the user maintains a reminder or task list for account
checks, read the mapped entry's current title, notes, occurrence and completion
state. That list must not silently add or remove accounts from the MoneyWiz-derived
checklist; missing, duplicate, ambiguous or stale mappings remain explicit work
items.

Report the checklist by the user's stable reporting groups from the private
profile. Preserve one row per current MoneyWiz account; do not collapse accounts
merely because they share an institution.

The normal transaction-review scope is the current set of unreconciled MoneyWiz
rows for the requested account or accounts, plus the exact source interval needed
to verify those rows and every linked counterpart leg. Match the source cutoff to
the rows under review. Do not routinely re-check already-reconciled history or
require a full account statement when the authorized source view covers that
bounded interval. A zero unreconciled count means no transaction review is pending;
it does not claim that a separately requested balance, holdings or account review
was performed.

If an unreconciled row conflicts with an already-reconciled row, suggests a missing
or duplicate event, exposes an incomplete or ambiguous CLI read, or leaves a
balance/date gap that cannot be resolved within the pending interval, stop and
recommend the specific broader lookback needed. Include already-reconciled history
only after the user requests it or authorizes that proposed expansion. An explicit
user request for a wider interval takes precedence over this default.

For any provider with scheduled publication windows, check its official release
date before an authenticated lookup. Compare it with the latest corresponding
MoneyWiz record and today's date. Skip a lookup when no new result is available;
do not expose or store account identifiers, and do not complete or advance an
unchecked reminder. Keep the next eligible date and reason in the private profile.

When a mapped reminder or task note lacks the source, method, account/product identity,
coverage cutoff, balance/holdings/debt scope or account-specific restriction needed
for the check, obtain that information from the private profile and the current
authorized source, then update the existing reminder note with a concise
`Source; method; verified through; exception` record. Preserve useful historical
evidence and do not replace a current note with an unverified guess. If the source
route or account identity cannot be established safely, leave the account unresolved
and record the missing information rather than reconciling it.

For API-backed providers, use the CLI or connector configured in the private
profile and follow its current documented contract. Keep credential-file locations
private, enumerate all returned accounts, follow pagination, and never expose key
material. Do not switch to a browser or introduce a new client merely because the
current command's output needs parsing; first verify and normalize its documented
response format.

Record one outcome per checklist account: source-verified, verified with no new
activity, valuation-only difference, unresolved, or intentional skip. Complete or
advance a reminder only for a verified occurrence, retaining the source, method,
coverage cutoff and exception in the private profile. Never store personal reminder
titles, source URLs, balances or account identifiers in this generic skill.

## Live-session invariant

Try browser and other authorized source routes first. Use iPhone Mirroring only
when a required provider source cannot be verified there, and notify the user
before opening it. If Mirroring is opened for source access, keep it active for
the rest of that live operation and perform a harmless real interaction in its
window and the foreground provider app at least every **45 seconds**, including
after extended external work. Track the last interaction and split calls so they
cannot silently overrun the interval. Screenshots, AX reads and window focus
alone do not count. If the operation uses only CLI/browser sources, do not open
or keep Mirroring active. Do not promise a background timer unless the runtime
actually executes it.

When phone/provider authentication requires PIN or Face ID, request only the needed
user unlock; do not enter a bank/device PIN. A tool timeout alone does not prove a
phone or Mac lock. Retain captured source evidence and the queued plan.

## Read, plan, apply, verify

- After imports review exact and fuzzy payee candidates; apply only evidence-backed
  approved merges. Keep unresolved identities explicit while progressing independent
  accounts. Classify transfers before assigning expense categories.
- Inventory **all involved accounts** before changing refunds or transfers. Build
  an internal graph of accounts, ledger rows, reciprocal links and source events.
  Amount/date coincidence is a candidate, not proof of ownership.
- Give each source event one disposition: retain, edit, link, delete or create.
  Record IDs, expected old values, deltas, dependencies and evidence. Do not write
  provisional transactions to investigate a mismatch.
- Use the admitted CLI writer first. A documented URL action with verified targeting
  or native GUI is a fallback for that single operation only. Review the plan and
  digest; apply within the user's existing authority without repeatedly asking
  for the same action.
  Ambiguous identity, missing source evidence or expanded scope needs a decision.
- Database writes use the existing Core Data host, capability gate, app-closed
  protocol and recovery policy. Never substitute raw SQLite mutations. Defer missing
  CLI features to the project TODO; do not develop them during bookkeeping.
- Read back each mutation: IDs, categories, notes, dates, currency, paired legs and
  reconciliation. Timeout/missing UI result means **unknown outcome**: inspect
  persistence before retrying. Execute small planned batches with intermediate
  checks; stop when a precondition or expected delta fails.
- Reconcile verified rows only after source activity and the relevant balance,
  cash or asset quantities agree. Verify both transfer accounts and both legs.
  Cleared/pending and reconciled are separate states. Bulk selection is valid only
  when every selected row is covered by the verified scope.
- For normal transaction reconciliation, review only unreconciled rows and the
  source interval and linked counterpart legs needed to verify them. Do not include
  already-reconciled history by default. If a pending row conflicts with reconciled
  history, a duplicate or missing event is suspected, CLI coverage is incomplete,
  or a balance/date gap remains, recommend a bounded expansion and wait for the
  user's request or authorization before reviewing reconciled history. A user may
  explicitly request a wider transaction interval or a separate balance/holdings
  review.

## Finish and retain learning

Track source coverage, ledger correctness and reconciliation separately. Empty output
or zero unreconciled rows cannot prove completeness when parsing skipped records.
Re-read affected IDs and the in-scope unreconciled set **after the final edit**,
including category changes. Report unresolved rows and valuation-only differences.
Update a recurring reminder once for the verified occurrence; completion may advance
its date. An intentional skip is not a provider-verified account.

Maintain the private profile after verified batches and at interruptions: current
policies, dated evidence, old/new IDs, applied/pending actions, export coverage,
remaining checks and concise reminder notes. Mark superseded interpretations.
Store merchant mappings and account exceptions there, never in this generic skill.
Do not retain credentials or OTPs.

This is an assisted workflow distilled from a multi-day session, not proof of
unattended automation. Validate its reuse on a subsequent cycle.
