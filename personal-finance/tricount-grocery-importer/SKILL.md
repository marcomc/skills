---
name: tricount-grocery-importer
description: Import new Conad and Lidl receipt products from Tricount exports already ingested by an upstream transaction service into an existing grocery Google Sheet. Use for incremental grocery imports, missing-receipt recovery, or provenance backfills without duplicating existing purchases.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Tricount Grocery Importer

Turn upstream Tricount transactions into traceable grocery receipt lines in the
existing analysis workbook. This is an on-demand Codex workflow, not an exporter,
upstream importer, scheduled job, or Apps Script installation.

## Configuration and source of truth

Read the private profile at
`~/.config/tricount-grocery-importer/config.json` (or the user-specified path).
It supplies account/client, workbook and folder IDs, sheet names, and user rules.
Never copy those identifiers, receipt data, credentials or shared Tricount keys
into the public skill collection. Verify configured identities against live
metadata; stop dependent writes on ambiguous destinations or schema drift.

Use the installed Google Workspace CLI when capable, otherwise an authorized
connector. Use browser controls for authenticated Lidl receipt history. Read
[schema.md](references/schema.md) before reading or changing data and
[receipts.md](references/receipts.md) before extracting receipt lines.

## Incremental workflow

1. Read the upstream import log and transactions, destination product rows,
   receipt catalogue, source ledger, equivalence and category mappings. Fetch
   all relevant pages/ranges; a partial read cannot establish absence. The
   upstream service's completion means transactions arrived, not that products
   have been extracted. Do not change the upstream service or its records.
2. Resolve exact source identity: exported Registry identity + entry UUID,
   upstream row ID, export JSON and folder, original Tricount title and its
   explicit period. Expense date/month is separate from Tricount period.
   Validate source UUIDs against exported JSON; read Drive copies first.
3. Build a read-only plan with `scripts/plan_import.py`. Its JSON contract is
   in [schema.md](references/schema.md). Inspect existing product rows as well
   as the ledger: interrupted writes and historical imports may lack a ledger
   entry. Any existing rows require reconciliation before additions, never blind
   append. In the default “new expenses” run, hold unchanged historical rows
   and report their status without redoing OCR. Reconcile them when evidence
   changes, a missing part is recovered, or the user requests repair/completion.
4. For new or retryable transactions, Conad uses archived receipt images and
   OCR; Lidl first uses an existing digital receipt, then authenticated purchase
   history, then Tricount photos when the digital receipt is unavailable.
   Missing/unreadable receipts remain pending, not successfully imported.
   Revisit pending entries when evidence changes or the user requests a retry.
5. Stage every product, discount and refund, retaining source text, evidence,
   quantities, stable line IDs, canonical product/family and store. Apply the
   profile's user corrections. Do not classify only examples or favorite items.
   Reconcile receipt totals before writes; record unresolved differences.
6. Re-read exact target rows and fingerprints immediately before committing.
   One writer owns the destination. Preserve A:Y values, existing IDs and
   formulas except for explicitly evidenced corrections. Use an atomic bounded
   Sheets batch for a receipt's rows and ledger transition where possible.
   After timeout/uncertain mutation, read back before retrying.
7. Verify saved rows by stable ID, exact decimal amounts, receipt identity and
   totals; then mark `Importato verificato`. A legacy equal total alone does
   not prove all products are correct. Keep partial/ambiguous rows present and
   flagged rather than inserting a second full receipt. Refresh mappings and
   verify native formulas, year filters, price comparisons and chart units.
   No Apps Script: preserve the workbook's native update mechanism.

## Idempotency and reporting

Deduplicate by source identity **and physical receipt**, not month, merchant,
filename, date+amount alone, or membership of a previously processed Tricount.
Multiple images/PDFs can show the same receipt; one receipt can cover multiple
Tricount entries. Keep those links without duplicating its product lines.
Changed or deleted upstream transactions require reconciliation, not a new row
or silent deletion. Preserve unmatched Lidl receipts with their own receipt ID;
never invent a Tricount link. Same content under a new export file ID is not a
new expense.

Report source Tricounts, transactions examined, added, already present, changed,
missing, unreadable and ambiguous; counts of lines and reconciled totals; link
the workbook. Preserve filters after validation. State what remains unresolved.
Store private run evidence under the profile's run directory. Retire temporary
OCR/download copies only after their durable Drive originals and import
readback are verified; preserve originals and pending-review evidence.

For large batches, bounded lighter subagents may extract or independently check
receipt groups when authorized. Give only the relevant files/schema; they
return candidates and confidence, while the coordinator reconciles and writes.
