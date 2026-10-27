# Google Sheets Contract

## Contents

- [Live Inspection](#live-inspection)
- [Banknote Fields](#banknote-fields)
- [Coin Fields](#coin-fields)
- [Duplicate Actions](#duplicate-actions)
- [Safe Writes](#safe-writes)
- [Read-Back and Reporting](#read-back-and-reporting)

## Live Inspection

Use native Google Sheets read and edit operations. Before every write:

1. Read spreadsheet metadata and confirm the title and exact sheet names.
2. Read the live header row and preserve unused or historical columns.
3. Read all candidate duplicate rows and every row or cell to be updated.
4. Identify formulas, notes, validation, and formatting that the change must
   preserve.

The default workbook currently uses `Banconote` and `Monete`, but live metadata
is authoritative.

## Banknote Fields

The documented `Banconote` layout is:

| Column | Header | Meaning |
| --- | --- | --- |
| A | Album Babbo | Numeric catalogue or gift year. |
| B | Paese | Country in the workbook's naming style. |
| C | Type/category | Normally `Banconota`. |
| D | Valore | Face value with sensible numeric formatting. |
| E | Simbolo | Currency symbol. |
| F | Codice | ISO 4217 code when applicable. |
| G | Valuta | Human-readable currency name. |
| H | Serie | Issue or series year used by the collection. |
| I | Numero di Serie | Exact physical serial, including zeroes and suffixes. |
| J | Dritto | Specific obverse subject. |
| K | Rovescio | Specific reverse subject. |

## Coin Fields

The documented `Monete` layout is:

| Column | Header | Meaning |
| --- | --- | --- |
| A | Album Babbo | Numeric catalogue or gift year. |
| B | Paese | Country. |
| C | Valore | Denomination. |
| D | S.lo | Currency symbol. |
| E | Codice | ISO code when applicable. |
| F | Valuta | Currency name. |
| G | Serie | Mint or issue year. |
| H | Q.tá | Existing convention, normally `I`. |
| I | Note | Useful additional issue or variety information only. |
| J | Dritto | Specific obverse subject. |
| K | Rovescio | Specific reverse subject. |
| L | Quantitá | Number of matching physical specimens. |
| M | Tipo | Normally `Moneta`. |
| N | Valore base | Existing collection-value information; preserve it. |

Never place side descriptions in `Note` when dedicated side columns exist. If a
compatible coin sheet lacks them, ask before adding `Dritto` and `Rovescio`
unless structural modification was already requested. Insert them after `Note`
or at the most logical live-schema position, preserving and verifying all moved
data. Backfill historical rows only from high-confidence exact-issue evidence.

## Duplicate Actions

Use one of these explicit actions:

- `INSERT`: a new banknote specimen or distinct coin issue.
- `UPDATE QUANTITY`: another specimen of an exactly matching coin issue.
- `SKIP EXACT DUPLICATE`: an existing physical banknote with the same exact
  serial, or an already-accounted-for submitted object.
- `NEEDS REVIEW`: ambiguous issue, design, side pairing, serial, or match.

For banknotes, distinguish specimens by exact serial. For coins, match country,
denomination, currency, year or series, and exact design or commemorative issue.
Within one planned batch, an exact repeated new banknote serial is skipped and
its `batch_duplicate_of_index` points to the earlier specimen decision. If the
same new serial has conflicting metadata, every decision for that serial is
`NEEDS REVIEW`; none may be inserted until the conflict is resolved. These
decision indexes identify entries in the plan, never live sheet rows.

The helper keeps one `decisions` entry per photographed specimen. For coin
writes, use `coin_write_operations` as the executable write set; do not execute
coin decisions separately. Each actionable coin decision's zero-based
`coin_operation_index` points to its operation, and each operation includes the
zero-based `decision_indexes` and available `specimen_ids` that it covers.
Multiple specimens matching one existing row become one quantity write from
the live quantity to the final projected quantity. Multiple specimens of one
new exact issue become one insert operation whose `record.quantity` is the
aggregate count. Distinct issues remain separate insert operations. These
operations never invent a live row number for a new insert. `summary` counts
specimen decisions; `coin_write_summary` counts coin write operations.

Validate currency at the issue date rather than copying suspect legacy data. A
known example is Ecuadorian 5 centavos dated 2000: it belongs to dollarized
coinage and uses `$`, `USD`, and `Dollaro statunitense`, not ECS or sucre.

## Safe Writes

- Use narrowly scoped cell, row, or append operations; never rebuild the
  workbook.
- Write `Album Babbo` as a numeric value, such as `2026`, never as `"2026"`.
- Preserve serials and other identifier strings exactly.
- Copy or extend neighbouring formatting only where required by the live table.
- Preserve formulas, notes, validation, `Tipo`, `Valore base`, and unrelated
  content.
- Apply quantity updates from the value read immediately before the write. If
  the value changed since planning, stop and recompute instead of overwriting.
- Before each coin quantity operation, reread its target row and confirm its
  current quantity equals `old_quantity`; write `new_quantity` once for the
  aggregate operation. For inserts, write each `coin_write_operations` record
  once, including its planned `quantity`.

For requested historical backfills, read each row's country, denomination,
currency, issue year, notes, and existing design data. Research the exact issue
and fill side descriptions only at high confidence. Reuse a result only where
the design genuinely remained unchanged. Treat commemoratives, redesign years,
monarch changes, national-emblem changes, special mint sets, and multiple
same-year designs as separate ambiguity checks. Justified blanks are preferable
to false completeness.

## Read-Back and Reporting

Read back every changed range. Verify numeric types, exact serials, quantities,
side-column placement, adjacent cells, notes, formulas, validation, and visible
formatting. For inserted columns, verify the header, representative rows around
the change, and the last populated rows.

Report in the user's current language:

- banknotes and coins identified;
- rows inserted, quantities increased, and exact duplicates skipped;
- unresolved items and corrections to prior metadata;
- an item table with `Type`, `Country`, `Value`, `Series/Year`, `Serial`,
  `Dritto`, `Rovescio`, and `Action`.

Do not claim completion when read-back is unavailable or inconsistent. State
the exact unverified operation instead.
