---
name: gmail-coupon-cataloguer
description: Review Gmail offers with agent judgment, maintain an existing Google Sheets coupon catalogue, label and archive verified imports, and clean up old promotional coupon mail while protecting purchase records. Use when asked to update the coupon database or run its established maintenance workflow.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Gmail Coupon Cataloguer

Build a useful database of discounts for future purchases. Perform the review
yourself; use CLI tools for retrieval and writes, not the application's importer
or a keyword classifier as the final decision maker.

## Scope and local profile

- Load the private profile from `GMAIL_COUPON_PROFILE`, or
  `$HOME/.config/gmail-coupon-cataloguer/profile.json`. Read the field contract
  and CLI notes in [references/operations.md](references/operations.md).
- A request to run the established maintenance workflow includes incremental
  import, labeling, archiving and the configured retention cleanup. Honor
  overrides such as analysis only, no cleanup, a date range or a different
  retention period. Merely discussing or installing this skill makes no changes
  to Gmail or Sheets.
- State the resolved scan range, timezone and cleanup cutoff briefly, then
  perform the requested work. Reuse existing authorization without repeated
  confirmation. If the account or destination cannot be resolved, ask only for
  the missing information.
- Use the existing account, spreadsheet and labels. Do not run or deploy project
  code, change filters, configure forwarding, create scheduled jobs or reorganize
  labels as part of routine catalogue maintenance.
- Keep credentials, resource IDs, message bodies and personalized redemption
  links out of repository files and routine output. Keep private run state
  outside both the repository and installed skill directories.
- Before retention cleanup after a label reorganization, reconcile configured
  protective-label names with the live labels by prior IDs or verified merge
  evidence. Update the private profile only after the mapping is proven; an
  unresolved mapping stops cleanup.

## Start from the latest imported email day

1. Inspect the live sheet's headers and all populated email-date cells. Parse
   typed Sheets dates and locale-formatted strings; never sort displayed dates
   lexically. Use the source email date, not expiry or row insertion time.
2. Default to the most recent valid source email date in the sheet, including
   the whole day in the profile timezone. If the sheet is empty, use the
   profile's initial scan policy, normally January 1 of the current year.
   Investigate malformed or future dates rather than silently trusting them.
3. Before starting a new range, reconcile any pending offer or Gmail mutation
   from the private ledger. Re-read the exact Sheet row and source message;
   finish a verified row's label and archive step without appending it again.
   If a previous run is incomplete, resume from the earlier of its saved start
   day and the sheet-derived day. Rows written before an interruption must not
   move the next scan past unprocessed messages.
   Revisit unresolved messages from the ledger even when they fall outside the
   newly calculated range.
4. Capture a scan end instant and persist the pending range before writes.
   Express date boundaries as Unix seconds to avoid Gmail's implicit timezone.
   Include local midnight itself using a conservative overlapping boundary.
5. Enumerate every page in the range, including archived mail. Exclude Spam,
   Trash and drafts from new-offer discovery unless requested otherwise.
   Do not exclude whole labeled threads or assume a coupon label proves import.

## Review actual offers

Read subject and sender metadata first, then visible plain text and HTML where
needed. Search terms help prioritize candidates; inspect the remaining range
for generic subjects, unfamiliar languages and image-only promotions before
claiming complete coverage. If volume or an API failure prevents completion,
save progress and report the uncovered portion.

- Accept explicit reusable discount codes, personalized codes, discount links,
  claim links and in-app or registration offers when they provide a concrete
  benefit toward a future purchase. Capture eligibility and required steps.
- A shop homepage or ordinary "Shop now" link is not automatically a discount
  link. Verify the offer and preserve its actual redemption destination.
- Exclude historical discounts on completed orders, ordinary account credits,
  payment receipts without a new offer, authentication codes, order numbers,
  generic advertising and referral invitations that only promise earned rewards.
- A receipt can contain a valid new coupon: catalogue that offer while retaining
  the original document as protected purchase history.
- Read image alt text and available MIME content first. If an offer is embedded
  in an image, inspect the attachment or image visually; use the browser only
  when CLI retrieval cannot make it readable. Never invent missing characters,
  percentages, expiry dates or terms. Leave unresolved candidates unimported.
- Understand English, Italian, German, Spanish, Portuguese and French offers.
  Use the meaning of the message: "check out", "confirmation" and "returns" alone
  do not establish an order, invoice or merchandise return.
- Do not redeem offers, submit forms, subscribe or make purchases during review.

## Write, verify, then label

1. Compare each accepted offer with existing rows and the private message ledger.
   Use the exact Gmail message ID plus offer identity. Across different messages,
   compare merchant, code or redemption destination, validity period, eligibility
   and benefit. A recycled code with different terms is not necessarily a duplicate.
2. Resolve existing Gmail UI links through source evidence where needed; opaque
   UI IDs and API message IDs are not interchangeable. Verify subject, sender,
   date and offer before associating an old row with a message.
3. Preserve the existing schema, formulas and unrelated rows. Write the code or
   usable redemption link, material conditions, source email date and Gmail link.
   Keep uncertain fields blank. Do not silently replace source links or rewrite
   historical rows merely to make deduplication easier.
4. Write offer strings as literal values, not untrusted formulas. Verify each
   written row by reading it back. Record pending and completed message-to-offer
   mappings so a retry after a successful write cannot append the same offer.
5. Only after the row or existing equivalent offer is verified, apply the coupon
   label and remove `INBOX` from the exact source message. Protect any embedded
   transactional information using the configured protective labels when clear.
   An unresolved duplicate or failed write leaves its source untouched.
   Complete and verify this Gmail step before moving to another message. If a
   transient request fails, re-read the row and message, then retry the pending
   mutation a bounded number of times; a successful but unconfirmed mutation
   must be reconciled before another attempt. Never append the offer again.
6. For multiple offers in one email, finish all accepted offers before labeling
   the message. Archive and label individual messages, not entire conversations.
7. Mark the discovery range complete only after every message has a recorded
   outcome and every intended write and Gmail mutation is verified. Retain
   unresolved visual or classification cases in the pending ledger for later
   review. If execution cannot continue, preserve the exact pending state and
   report the run as incomplete. Resume at the next available invocation
   without requiring the user to ask again.

A request to audit existing rows additionally authorizes checking each row
against its source and correcting confirmed false positives. Routine incremental
updates do not silently become a full historical sheet audit.

## Clean up promotional email older than twelve months

Cleanup has an independent historical range; it is not limited by the new-offer
scan start. Default to twelve calendar months, or the user's explicit override.

A message is eligible only when all of the following hold:

- It currently has the configured coupon label.
- Its received date is strictly before the local calendar cutoff day. Subtract
  calendar months, clipping the day when needed; do not approximate with 365 days.
- It has no configured protective label or protected descendant label.
- Its content is positively identified as disposable promotion, with no useful
  purchase, payment, booking, delivery, return, warranty, licence, account,
  subscription, support, medical, certification or personal correspondence
  information.

**Whether the offer was imported is irrelevant to cleanup eligibility.** Do not
require a matching sheet row or a saved redemption link before removing old mail.

Before a cleanup batch, re-read candidate labels, inspect ambiguous bodies and
attachment metadata, and check the conversation for transactional context.
Preserve mixed conversations, substantive replies, paid vouchers with possible
remaining value and uncertain cases. An absent protective label is not evidence
that a message is disposable. Automatic stars or importance are not substitutes
for the configured protections.

Persist exact candidate message IDs and the reasons for eligibility. Move only
those messages to Gmail Trash, never permanently delete or empty Trash. Skip
messages already trashed and preserve catalogue rows. Verify the final labels
of every affected message; retain unresolved operations for safe resumption.

## Report

Return the inclusive scan start, completion boundary, messages reviewed,
offers added or deduplicated, sources labeled/archived, old promotions trashed,
protected messages retained and unresolved cases. Report partial coverage or
failed verification explicitly. Do not claim coupon validity at checkout without
a separate authorized checkout check.
