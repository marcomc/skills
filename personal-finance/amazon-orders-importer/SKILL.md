---
name: amazon-orders-importer
description: Safely refresh an existing Google Sheets Amazon order tracker from the authorized amazon-orders CLI. Use for recurring or requested Amazon order imports, deduplication, and item classification while preserving manual corrections.
---
<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Import Amazon orders into Google Sheets

Use the user's private configuration at
`~/.config/amazon-orders-importer/config.json`. Never publish configuration,
order records, authentication material, or private receipts. Before use, read
that file and the local CLI registry. Verify the effective Google account and
OAuth profile, the spreadsheet ID, its parent folder and write capability.
Validate Amazon session acceptance without interactive sign-in. Independently
confirm the configured Amazon account greeting with the CLI's own authenticated
session and match a stable prior order against the sheet and a trusted local
source snapshot. A stored cookie or a name alone does not establish identity.
Stop if identity, access, schema, session or source coverage is ambiguous.

Read [references/tracker-contract.md](references/tracker-contract.md) before
planning writes to the existing tracker.

For the configured tracker, run the maintained importer from the project using
the managed `amazon-orders` interpreter. It defaults to a dry-run; pass `--apply`
only for an authorized refresh. Review its aggregate output and report deferred
orders. The scheduler invokes this command without interactive login:

```sh
cd "${AMAZON_ORDERS_PROJECT_ROOT}"
"${AMAZON_ORDERS_PYTHON}" src/sync.py --apply
```

The importer applies verified new orders, components and safe status/refund
changes. It does not silently reconcile changed amounts or item details on
existing orders.
New items with no unique known ASIN category use `Da classificare`. A pending
journal blocks the next run until the result is reconciled.

## Source and planning

1. Inspect live sheet metadata and exact headers before reading bounded ranges.
   This tracker uses annual tabs, `Carte`, `Articoli`, and `Dashboard`. Preserve
   their current rows, validations, formatting, formula ownership and manual
   edits. Use a private job directory with restrictive permissions; remove
   temporary exports after validated completion. Do not print order details,
   payment digits, session cookies or tokens to logs.
2. For unattended work use the installed `amazon-orders` Python library with
   `auth_forms=[]`, verify the persisted session, and explicitly mark that
   verified session authenticated without calling `login()`. See the reference
   for the verified read-only sequence. Use closed stdin, a finite timeout, no
   credentials in arguments and no debug output. Fetch complete, paginated,
   full-detail history for the current and previous years. Validate the entire
   result, unique nonempty IDs, dates, totals, pagination and per-record errors.
   An empty or partial result is not proof of an empty account. Compare field
   coverage against verified prior snapshots, including payment method and last
   four. Never replace a previously populated value with a missing value. A
   missing payment field on an existing order is not a deletion: preserve the
   sheet and trusted baseline and inspect transactions. Process independently
   validated orders only; defer ambiguous payment components and report them.
   Reconciled mixed payments are represented as separate components. Stop all writes if account identity, order history coverage or sheet
   structure is uncertain, or the session expired. Never open an unattended
   login flow. See the reference for transaction reconciliation constraints.
3. Do not assume digital-order filters provide a separate complete source. In a
   verified check, both `digital` and `digital-orders` filters returned the
   ordinary first page; normal history included IDs prefixed with `D`. Do not
   import either filtered output as an independent source without a fresh
   verified comparison. State that completeness of other digital products
   remains unknown.
4. Read all existing order IDs and item rows within the exact known ranges;
   check duplicate IDs and row capacity. Compare source and sheet using IDs,
   not row position. Plan genuinely new orders with their item multiplicity;
   never duplicate an order, collapse identical line items, or infer owner from
   a last-four match alone. For existing orders, update source-owned fields only
   when a retained verified source baseline proves the live value is unchanged
   since the prior import. Preserve all formulas and manual fields. Record a
   conflict when baseline, current sheet or identity is ambiguous; never silently
   overwrite a manual change. Reconcile item additions as a multiset, and leave
   ambiguous duplicates, removals and manual categories untouched for review.
5. Categorize new items from their actual titles using existing categories where
   defensible; clearly mark uncertain suggestions. Do not alter existing item
   categories, card-person mappings, selections, or any other manual value.
   Do not copy Amazon Gift Card labels onto bank cards solely from shared digits.
   If a new payment label is needed, defer it for a new linked dashboard control
   and owner assignment; do not guess identity. Preserve the user's selections.

## Apply and verify

- Before a write, reread the exact target rows and confirm identity, existing
  values, capacity and permissions have not changed. Prepare a private journal
  with source IDs, intended rows and prior state. Use a single atomic Sheets
  `spreadsheets.batchUpdate` where possible, writing Amazon-provided strings as
  literal strings, never as formulas. Preserve the current locale's formula
  separators and pre-existing formula cells; insert item inclusion formulas for
  new item rows. Never put sensitive payloads or credentials in shell arguments.
- After a timeout or uncertain mutation, do not replay it. Inspect the target
  and journal first; reconcile per order and stop on partial or ambiguous state.
  No automatic deletion or silent repair of existing rows is authorized.
- Verify every planned order and item, counts, uniqueness, checkbox and formula
  behavior, source-to-sheet totals and a dashboard readback. Report new orders,
  updates requiring review, digital coverage, missing data and errors separately.
  Preserve source snapshots and evidence outside disposable directories only
  while needed for reconciliation. Retain no redundant temporary copies.
- On a scheduled run, use the same checks and stop on expired credentials,
  identity uncertainty, missing runtime or a global coverage or schema conflict.
  Defer independently ambiguous orders. Do not open login or MFA prompts
  unattended. Notify only on a meaningful change, failure, or needed user action.
  Explicitly state if the run was partial or did not write.
