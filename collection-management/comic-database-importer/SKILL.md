---
name: comic-database-importer
description: Import one or more photographed comic books into a Google Drive XLSX collection database while preserving its workbook structure and collection conventions.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Comic Database Importer

Use this skill when the user asks to identify photographed comics and add them
to their personal comic collection workbook on Google Drive. Do not use it for
general comic research without a requested workbook update.

## Inputs and authorization

Accept a Google Drive XLSX URL or reference, one or more images, and any
collection-specific instructions. The usual filename is `Comics_NIF_CM.xlsx`,
but treat the provided file, its ID, location, name, and layout as mutable.

Use the available Google Drive and spreadsheet/workbook capabilities. Before
any Drive or workbook mutation, confirm that the request authorizes an update.
If the request is research-only, return a proposed import rather than saving or
uploading a file. Never expose credentials or share the workbook.

## Workflow

1. Download an untouched temporary copy and inspect every worksheet before
   editing. Identify header rows, used columns, formulas, styles, comments,
   validations, and the collection's existing vocabulary. Read
   [workbook-handling.md](references/workbook-handling.md) for the current
   workbook-specific invariants and safe-edit procedure.
2. Inspect the images natively before researching. Group front/back and
   repeated photographs of the same physical issue; split images containing
   several comics into distinct candidate issues. Extract visible identifying
   evidence, especially the cover, issue number, publisher, date, price,
   country markings, and UPC/barcode. Do not rely only on OCR.
3. Verify each distinct candidate online. Prefer Grand Comics Database
   (comics.org); use reliable bibliographic, publisher, or specialist sources
   to fill gaps and resolve conflicts. Do not invent missing facts. Record an
   uncertainty rather than guessing, and prefer a primary bibliographic source
   when sources conflict.
4. Search the complete workbook for duplicates before selecting a target sheet.
   Choose the most coherent existing collection sheet from its actual contents;
   do not assume a sheet maps one-to-one to a series. Never create a sheet
   unless the user explicitly asks.
5. Prepare a row using formats and values already established in comparable
   entries. Preserve all unrelated content and workbook behavior. Read
   [workbook-handling.md](references/workbook-handling.md) before inserting.
6. Validate the proposed rows and workbook integrity, then save a separate
   temporary updated copy. Replace the existing Drive file only when the
   request authorizes it, preserving its Google Drive file ID. Re-download the
   replacement and re-check the inserted rows.

## Reporting

Report the number of distinct comics identified, inserted, skipped as
duplicates, and left unresolved; list the destination sheets, key identifiers,
and any uncertainty. Clearly distinguish a saved-and-reverified import from a
proposal that was not uploaded.
