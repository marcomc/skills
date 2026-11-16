---
name: bitwarden-entry
description: Create Bitwarden vault entries using the user's existing templates. Use when adding a credential, key, token, card, identity, or other item to Bitwarden.
---
<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Create Bitwarden entries

1. Confirm the requested vault, destination folder, item purpose, and authorization. Read the local CLI registry and prefer the installed Bitwarden CLI. Verify the active account and session without displaying secrets.
2. Inspect the current items in `000 Templates`; select the matching item explicitly named as a template. For OAuth credentials, API keys, and tokens, use `API - Template`. Other observed templates cover bank accounts, debit and credit cards, passports, SIMs, software licences, and Wi-Fi networks. Treat the live vault as authoritative; do not treat ordinary entries in the template folder as templates merely because they are there.
3. Construct a new item from the selected template's type, field names, field types, and applicable structure. Populate known values in corresponding fields, preserving empty fields where appropriate; place additional necessary information in clearly named fields or notes. Preserve the template itself. Avoid copying sample values, personal data, identifiers, ownership, attachments, or other unrelated metadata from it. If no template fits, use the native item type appropriate to the request.
4. Keep secret values out of terminal output, shell history, command arguments, and chat. Use protected input streams and process-local variables. Store only the authorized material and do not expose the template or other vault entries unnecessarily.
5. Before creation, check the exact destination for an existing matching item; avoid duplicates. Verify the new item by reading back its type, folder, field names, and values privately, without printing secrets. Report the item name and folder, and distinguish client credentials from access or refresh tokens.
6. If access, identity, template applicability, or a write result is uncertain, stop and resolve it before retrying a mutation. Do not automatically repeat an uncertain write.
