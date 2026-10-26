---
name: world-coin-banknote-cataloguer
description: Identify, research, de-duplicate, and catalogue photographed world coins and banknotes in an existing Google Sheets collection database. Use for new collection batches, quantity reconciliation, exact-duplicate checks, or evidence-backed enrichment of existing currency records.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# World Coin and Banknote Cataloguer

Catalogue physical currency from paired or individual photographs with accuracy
ahead of completeness. Never infer an exact issue, design, side, year, serial, or
currency classification from insufficient evidence.

## Inputs and Defaults

- Accept one or more photographs containing coins, banknotes, tokens, or medals.
- Use the spreadsheet URL or ID supplied by the user. Otherwise default to
  `1lO2rCXVSvwm6Q4cEx2wcfs-pwg1EXo_65yFt2SLJnUg`, titled *Collezione Monete e
  Banconote da tutto il mondo per il babbo*.
- Unless the user specifies another album year, use the current calendar year.
  It must remain an integer through planning and Google Sheets writing.
- Follow the user's current language in the final report. Keep skill internals
  and generated audit field names in English.

## Required Workflow

1. Read [references/cataloguing-workflow.md](references/cataloguing-workflow.md)
   before analysing the photographs or researching an issue.
2. Inventory every visible object and assign stable temporary IDs before pairing
   sides. Do not silently omit obscured or unresolved objects.
3. Research each incomplete identification against the exact issue or series.
   Browse current authoritative sources; do not rely on memory for design facts
   that may vary by year or issue.
   For Canadian items, consult the known-good descriptions in
   [references/canadian-examples.md](references/canadian-examples.md) as examples,
   then verify the incoming exact issue against current authoritative evidence.
4. Read [references/sheets-contract.md](references/sheets-contract.md) before
   inspecting, planning, or changing a spreadsheet.
5. Inspect live spreadsheet metadata, sheet names, headers, target rows, and
   duplicate candidates. Treat the documented schemas as guidance, not as a
   substitute for the live workbook.
6. Build and check a candidate table before writing. The table must include the
   temporary ID, location, type, country, denomination, currency, year or series,
   serial when applicable, both side descriptions, confidence, existing match,
   and intended action.
7. Use `scripts/catalogue_records.py` when deterministic pairing, duplicate
   classification, quantity calculation, typed row preparation, or an audit JSON
   would reduce transcription risk. Its output is a proposal, not authority to
   override conflicting visual, source, or live-sheet evidence.
8. Write only high-confidence identifying data with narrow native Google Sheets
   operations. An explicit request to catalogue a batch authorizes ordinary row
   inserts and quantity updates; ask before adding or moving columns unless the
   user already requested the structural change.
9. Read back every written range and verify types, values, column alignment,
   neighbouring cells, notes, formulas, validation, and formatting before
   reporting success.

## Decision Rules

- A banknote with an exact existing serial number is the same physical specimen;
  a different serial is a separate specimen even when country, denomination,
  and series match. Missing or uncertain serials must not be used to collapse
  otherwise similar banknotes.
- Aggregate a coin only when country, denomination, currency, year or series,
  and the specific design or commemorative issue all match. Increase `Quantitá`
  rather than adding a redundant row. Same-year coins with different designs
  remain separate.
- Classify tokens, medals, private issues, and novelty pieces as such. Do not
  force ISO currency fields onto non-currency objects.
- `HIGH` confidence permits a write. `MEDIUM` requires more research. `LOW`
  becomes `NEEDS REVIEW`, with uncertain identifying cells left blank.
- If existing metadata appears wrong, report the evidence. Correct it only when
  the current request authorizes updates and the correction is high confidence.

## Invocation and Validation

Example: `Use $world-coin-banknote-cataloguer to catalogue these paired photos
in my default collection sheet.`

For implementation tests and expected edge-case behavior, read
[references/validation-cases.md](references/validation-cases.md). Run:

```bash
python3 -m unittest discover \
  collection-management/world-coin-banknote-cataloguer/tests
```

Return a compact item table and batch totals as specified in the Sheets contract.
Highlight only uncertainties, material corrections, database inconsistencies,
and requests for better photographs.
