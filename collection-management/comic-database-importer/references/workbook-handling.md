# Workbook Handling

## Inspect first

Before changing a workbook, download its original and retain an untouched
temporary backup. Inspect all sheets and determine the actual header row,
column meaning, populated range, validation rules, formula patterns, comments,
formatting, column widths, and personal extensions. Do not infer the current
layout from a previous import.

The currently known `Comics_NIF_CM.xlsx` layout normally has headers on row 24
and these main columns:

| Column | Meaning |
| --- | --- |
| A | Variant |
| B | Themes |
| C | Catalog Code |
| D | Publisher |
| E | Series |
| F | Edition |
| G | Name |
| H | Date Issued |
| I | Issuing Periodicity |
| J | Issue Type |
| K | Issuing Number |
| L | Genre |
| M | Cover Price |
| N | Currency |
| O | Writer |
| P | Cover Artist |
| Q | Cover picture file name |
| R | Back picture file name |
| S | Description |

Some sheets have user-defined columns after S. Preserve them and their meaning.
The sheet named `do not delete or modify` is infrastructure: never change it.

## Sheet selection and duplicates

Sheets generally group a character or collection, not necessarily one series.
Choose the sheet that best matches its existing contents. Do not create,
delete, or rename a sheet without an explicit request.

Known placement examples are guidance, not a replacement for inspection:

- Lobo, Archie, standalone *The Incredible Hulk*, *The Amazing Spider-Man*,
  and Spawn belong in `Varie`.
- Silver Surfer belongs in `Silversurfer`.
- *Conan the King* belongs in `Conan`.

Search all sheets before insertion. Evaluate duplicates using Publisher, Series,
Issuing Number, Date Issued, Catalog Code or UPC, and Variant together. Do not
insert an apparent duplicate automatically. If the physical copy is a genuine
different variant, determine whether existing conventions justify a separate
row.

## Values and image fields

Mirror the workbook's comparable values. Current examples include `First
edition`, `Monthly`, `Bimonthly`, `Irregular`, `Booklet`, `Superhero`,
`Fantasy`, `United States dollar $ [2]`, and `Canadian dollar $ (CAD) [101]`.
Store cover dates as real Excel dates, normally the first day of their month.

Do not reinterpret `Variant`. `Direct Sales` and `Newsstand` are normally
description text, for example `Direct sales edition.` or `Newsstand edition.`,
not Variant values. A genuine national variation can be a Variant only when
that matches the workbook's demonstrated convention.

Populate the cover or back image filename only when the supplied image is an
appropriate individual photograph or scan of that specific cover. An image
containing multiple comics is not automatically a cover-file reference.

## Safe insertion and verification

Insert at the first suitable available row on the chosen existing sheet. Do not
rewrite a workbook wholesale. When extending past the populated area, copy the
structure, formatting, validations, formulas, comments, and applicable
conventions from a compatible nearby row, then replace only the required data.

Before saving, check all proposed rows, issue numbers, UPCs, dates, prices,
currencies, selected sheets, duplicate results, formula errors, and integrity
of other sheets. Compare identified and inserted counts.

Some legacy XLSX files contain OpenXML comments with empty authors. If a parser
rejects that structure, operate only on a temporary copy and apply the smallest
non-visible repair needed to parse it. Preserve user-visible content and, as
far as the chosen tooling permits, metadata, comments, styles, and validations.

After an authorized replacement upload, retain the original Drive file ID,
download the uploaded file again, and verify the added rows in that downloaded
copy.
