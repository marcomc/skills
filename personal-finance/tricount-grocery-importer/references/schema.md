# Workbook contract

Resolve headers and IDs live. These are the configured workbook's established
columns; fail on a conflicting layout instead of shifting data blindly.

## Upstream

`Transazioni`: A imported transaction ID; B expense date; C/D expense year/month;
G amount; H currency; I description; J type; M merchant; R source folder;
S source JSON; T source row; U upstream import timestamp; W source entry UUID;
X native type; Y source status. The `Importazioni` tab is the upstream run log.
Read only relevant expense/refund records for Conad/Lidl; exclude balance and
transfer records. Source status changes are review events.

Archived JSON contains `Response[0].Registry`: original `title`, registry `id`
when available, and `all_registry_entry[].RegistryEntry.uuid`. Use the registry
ID, or a verified durable registry identity recorded in the private profile.
A Drive folder ID is a fallback identity requiring alias handling if moved or
re-exported elsewhere. Do not use a mutable JSON file ID as the transaction key.
If a historical JSON URL is gone, use the profile's source aliases or locate
an archived replacement; validate registry identity, exact entry UUID, date,
amount and description before recording the alias. Multiple copies of the same
registry are not multiple Tricounts. Preserve old aliases for future matching.
Do not store public share tokens in the ledger. Preserve an explicit title
period as `YYYY-MM`; for multi-month titles keep the title and leave period
blank with an explanation. Never substitute the receipt month for the title.

## Product database: Righe verificate

| Columns | Contract |
| --- | --- |
| A:I | Date, year, receipt description, family, recorded amount, received packs, verification notes, evidence URL, legacy transaction ID |
| J / L | Computed grouped family / store; preserve formulas |
| K | Entered store: Conad or Lidl |
| M:N | Documented total weight kg / receipt gross price per kg |
| O:P | Immutable line ID / linked product ID on a negative discount row |
| Q:T | Quantity quality, comparable product, total received normalized quantity, unit |
| U:V | Promotion/format note / verified multiple-buy offer |
| W | Documented savings already included in E, informational and nonnegative |
| X:Y | Negative analytical share of an existing discount / allocation evidence |
| Z:AK | Provenance fields below; preserve existing A:Y when backfilling |

Z stable source key; AA registry identity; AB original Tricount title;
AC explicit Tricount period; AD source entry UUID; AE upstream transaction ID;
AF source JSON URL; AG source folder URL; AH receipt identity;
AI provenance status; AJ provenance verification timestamp; AK source fingerprint.
AJ is not the original product import time when backfilled.

For new linked rows, I uses the upstream transaction ID; preserve historical I
values during backfill. Standalone Lidl rows use `LIDL:<receipt-id>`.

Future stable line IDs derive from physical receipt identity + immutable line
ordinal, not row position or mutable classification. Preserve historical O IDs.
Keep the receipt identity independent of its Tricount assignment; compare archived
file aliases, digital receipt IDs and content before importing a new source key.

## Source ledger: 21 Registro importazioni

One entry per source transaction, plus standalone receipts. Columns A:U:
source key, Tricount title, period, expense date, store, source UUID, upstream ID,
JSON URL, folder URL, evidence URLs, state, line count, net lines, source amount,
difference, last check, source fingerprint, notes/next action, registry identity,
receipt identities, upstream row reference. L/M/O are derived from product
provenance, not manually maintained totals. Model many-to-one receipt links
explicitly if discovered; assign spending once, do not duplicate products to
make each source transaction reconcile individually.

Suggested states: `Da acquisire`, `Scontrino mancante`, `Illeggibile`,
`Parziale`, `Da riconciliare`, `Importato verificato`, `Presente — da verificare`,
`Presente — scarto da verificare`, `Presente — solo Lidl`.
A missing receipt is a processed attempt, not a completed import.

Historical provenance backfills may establish exact links without establishing
extraction completeness. Mark those rows present, preserve them, and reconcile
before completing any pending remainder. A changed fingerprint does not prove
an amount change; inspect the changed fields before corrections.

## Planner JSON and usage

The planner is local/read-only. Normalize live data into this structure:

```json
{
  "sources": [{
    "source_key": "tricount:registry-1:entry-1",
    "upstream_id": "import-1",
    "source_uuid": "entry-1",
    "fingerprint": "sha256-current-source",
    "receipt_keys": ["lidl:receipt-1"]
  }],
  "existing_lines": [{
    "source_key": "tricount:registry-1:entry-1",
    "legacy_transaction_id": "import-1",
    "receipt_keys": ["lidl:receipt-1"]
  }],
  "ledger": [{
    "source_key": "tricount:registry-1:entry-1",
    "state": "Importato verificato",
    "fingerprint": "sha256-previous-source"
  }]
}
```

Run `python3 scripts/plan_import.py snapshot.json --out plan.json`.
Normalize receipt aliases to the same physical ID before planning. Hash relevant
source content (registry, UUID, date, merchant, amount, currency, type/status,
attachments), excluding volatile run timestamps and JSON file revision IDs.
The helper cannot prove an unidentified photo matches a receipt, and its `new`
result is not permission to bypass receipt identification or total checks.

## Validation before completion

- Reconcile E totals to the receipt, then receipt to the upstream transaction.
  Separate card payments, loyalty vouchers, refunds and non-product movements.
- Confirm O uniqueness, valid P targets, one discount allocation path, and
  conservation of X shares. W must not lower net again.
- Read back the added stable IDs and ledger state; rerun the planner. A verified
  unchanged import must become `skip`, not `new`.
- Check current formula range limits before extending beyond existing grids.
  Extend lists, filters and validations as needed without overwriting formulas.
- Preserve numeric cell types on writes; read unformatted values and compare
  complete aggregates against the source rows.
- Reconcile each visible summary tab to current source-backed data; identify and
  preserve stale prototypes rather than presenting them as current results.
- Test priced and missing-format products and both empty-to-populated and
  populated-to-empty filter transitions in the rendered sheet; an empty filter
  must show a clear no-data state. Preserve stable
  year/store series and colors; isolate any presentation-only numeric anchors
  from analytical totals.
