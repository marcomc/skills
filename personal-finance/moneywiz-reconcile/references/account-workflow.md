# Account workflow

## Evidence and efficient discovery

Capture a complete source interval once and reuse it until new activity, changed
scope or a stale precondition invalidates it. Consult the private export inventory
before requesting another statement. For incremental archives, start the next
interval the day after the last covered date and end yesterday, unless the user
specifies otherwise. Record timezone and coverage; same-day exports are provisional.

Compare balances at the same cutoff. For imports stopping yesterday:
`provider balance at cutoff = live balance - sum(signed later movements)`.
Include credits as well as expenses; distinguish posted from pending money. Verify
that this cutoff applies to the current provider/import run.

After resolving the variables from the current session, check actual help and use:

```sh
moneywiz --db "$db_file" identity --app "$moneywiz_app"
moneywiz --db "$db_file" snapshot --account "$account_id" \
  --until "$cutoff_timestamp" --timezone "$account_timezone"
moneywiz --db "$db_file" accounts --format json --diagnostics
moneywiz --db "$db_file" transactions --account "$account_id" \
  --all-fields --with-categories --with-tags --limit 0 --format json --diagnostics
moneywiz --db "$db_file" categories --user "$user_id" --full-name --format json
moneywiz --db "$db_file" holdings --account "$account_id" --format json --diagnostics
moneywiz --db "$db_file" record --gid "$record_gid"
```

For `snapshot` and `transactions`, `--until YYYY-MM-DD` includes only through that
date's midnight in `--timezone` (default UTC), not the rest of that day. Use an
offset-qualified timestamp for a precise inclusive cutoff, or complete reads and
explicit local-time filtering. Diagnostic list JSON contains `rows` and
`completeness`; exit `3` is partial and blocks dependent write planning. Recover the
missing evidence for that operation without treating unreadable rows as absent.
Limits and default cutoffs must not hide future-dated errors; read affected IDs
directly as well.
If parsing fails, stop dependent conclusions. Independent read-only SQLite inspection
with `mode=ro` and observed schema may recover identity/relationships. Never replace
missing holdings with zero, hide load errors or choose physical aliases arbitrarily.

## MoneyWiz account scope and reminder notes

The current MoneyWiz account inventory is the operational checklist. Resolve every
account from the active store by owner, currency, product and active/archive status.
If the user maintains a reminder or task list for account checks, match and read the
corresponding entry's title, notes, occurrence and completion state. Reminder
entries provide source/method runbook information; they do not define account scope.
Missing, duplicate, ambiguous or stale mappings are explicit work items.

Group current MoneyWiz accounts under the stable reporting categories in the private
profile. Use those groups for checklist reporting and coverage; still preserve each
account's distinct identity, currency, product and active/archive status.

The notes may identify the institution website, portal, statement, email, app or
other source route; resolve that route before live work and retain it in the private
profile. If a mapped note lacks the source, method, account/product identity,
coverage cutoff, balance/holdings/debt scope or account-specific restriction needed
for the check, update the existing reminder note after obtaining the information
from the private profile and current authorized source. Use the concise format
`Source; method; verified through; exception`; preserve historical evidence and do
not write unverified guesses.

Classify each mapped account as bank-auto-updating or manually updated. For a
normal transaction-reconciliation run, inspect the source only for accounts with
unreconciled rows, and cover the interval containing those rows plus any linked
counterpart legs needed to verify them. Do not review already-reconciled history or
require a full statement by default. If a pending row conflicts with reconciled
history, the CLI read is incomplete, or a possible duplicate, omission or date/balance
gap needs a wider comparison, recommend the smallest specific expansion and wait
for the user's request or authorization before reviewing that wider history. An
explicit request for broader activity, balance, holdings or debt review takes
precedence.

Track checklist coverage separately from ledger flags:

| Checklist outcome | Required evidence |
| --- | --- |
| Source-verified | For a requested broader account check: source route, cutoff, requested balance/holdings/debt and activity compared with the ledger |
| Verified with no new activity | For a requested wider activity check: current source checked and no source event is missing from the ledger |
| Valuation-only difference | Activity is covered; the remaining difference is a documented quote or valuation scope issue |
| Unresolved | Source, identity, coverage or ledger comparison is incomplete |
| Intentional skip | User-authorized skip with the reason retained privately; not provider-verified |

Do not complete or advance a reminder for an unresolved or intentional-skip
account. Do not treat zero unreconciled rows, an empty CLI result or an already
completed reminder as proof that a separately requested source, balance or holdings
check was performed. An account with no unreconciled rows does not require a routine
transaction-source check under the normal reconciliation scope.

## Internal transaction graph

| Object | Required evidence |
| --- | --- |
| Account | Store identity, ID/GID, owner, currency, product, active/archive status |
| Provider event | Source/reference, amount/currency, effective date, observation time |
| Ledger row | ID/GID, entity, account, amount, original currency/FX, dates, payee, category splits, notes, flags |
| Transfer edge | Both IDs, reciprocal sender/recipient links, account identity, source proof |
| Planned action | Source event, disposition, expected old values, dependencies, delta, status/readback |

Resolve counterparty from provider reference/product, active account identity,
reciprocal metadata, then amounts/currencies/dates and descriptions. Similar archived
products must not win a match. Salary, interest, refunds and external receipts are
not automatically owned-account transfers. Funding and subsequent FX are separate.

For FX retain both actual amounts, rate direction, fee amount/currency and rounding.
A small conversion is not automatically a fee. Never substitute today's market rate.
Use `transaction transfer` to replace supported imported rows atomically with a
zero-fee linked transfer. For unsupported shapes, use GUI fallback only for that
transfer operation. If it creates a new destination leg, verify it first, then
remove only the positively identified duplicate import using the CLI where supported.
Deleting a linked leg may delete its counterpart: inventory and plan both first.
Check that no duplicate or orphan survives.

## Refunds and instalments

Inventory current, savings and card accounts together. A provider refund may credit
current cash, reduce card debt or reverse a purchase. Follow evidence for that event;
historical patterns alone are insufficient. Before recreation prove there is no
existing representation. Afterward prove exactly one representation per source event,
preserving unrelated purchases and real transfers.

For accounts explicitly tracking instalment debt, preserve the original negative
purchase and link each actual funding payment as a positive transfer. Remove duplicate
negative instalment imports only after replacement funding is verified. Compare debt
to future instalments, not available wallet cash. This is an account policy, not a
universal rule for every payment-wallet account.

For a wallet compare actual currency balances. Card-funded purchases visible in
provider activity may belong solely in the card ledger. A blank instalment page does
not prove zero debt or authorize changing balance scope. A change to a future payment
setting does not authorize rewriting historical transactions.

## Investments, savings and adjustments

- Savings: verify receipts and effective dates before adding interest, bonus or
  prizes. An email without the amount is insufficient evidence of that amount.
- Units-based portfolios: verify security/type, quantity, quote unit (GBP versus GBX),
  commission, cash currency and funding. Use `transaction investment` for supported
  cash events, Buy/Sell and first Buy creating a manual investment holding. Confirm
  complete activity reads. During a single GUI fallback set security type before
  final price.
- Aggregate accounts: retain the confirmed policy. Income categorized as investment
  sale proceeds plus separate fees can be intentional; do not invent a holding,
  ticker or conventional quantity to imitate a units-based model.
- Record cash events and fees **before** adjustments. Native Adjust Balance creates
  a transaction; account Cash Balance/opening balance edits are different. Replace
  an identified premature same-session adjustment after missing events; preserve
  earlier historical adjustments.
- Establish whether the target is cash, total valuation or asset units. For crypto
  sum available and earning/staked units when the profile requires it. Source
  rounding and fiat quote differences do not prove missing units.
- Do not force investment values to agree using New balance when the policy forbids
  it. A verified staking-growth exception does not authorize cash/stock adjustments.
- Use `transaction adjust-balance` for admitted ordinary balance, investment cash,
  asset quantity or aggregate investment-total targets. New adjustment dates must
  be strictly after the latest account transaction. Keep source valuation cutoff
  separate from the mutation date; do not change dates to force CLI admission.
  Use `transaction delete-adjustment` for the supported latest aggregate adjustment,
  or `transaction delete` for an admitted complete transaction/dependency group.

## Payees and categories

Start post-import review with:

```sh
moneywiz --db "$db_file" merge-duplicate-payees --show-plan
moneywiz --db "$db_file" merge-duplicate-payees --fuzzy-map "$private_review_csv"
```

Preserve reviewed CSV decisions; do not overwrite them with a candidate export.
Use loose/partial/case-insensitive discovery, then verify original notes, description,
location and reference. Country-only payees lack identity; a country suffix on a real
merchant is not itself wrong. Similar names can be separate branches, cities or dated
interest events. Pending/rejected fuzzy pairs are no-ops.

Use `payee merge --kind exact` or `--kind fuzzy` for one reviewed source/survivor
pair; fuzzy requires its approved row via `--fuzzy-map`. Repeat with fresh inventory
for subsequent pairs. The legacy `merge-duplicate-payees --apply` remains blocked;
that does not block the separate W09 writer. Native Payees > Edit > Merge is a
fallback only for an unsupported single merge operation. Choose the survivor and
deselect it afterward because selection persists; return to CLI for the next pair.

Use `transaction assign` for guarded payee/category split replacement and
`transaction edit` for supported scalar fields. In a GUI fallback, set payee first,
then final category/description: selecting payee can replace both.
Verify **all category links and split amounts**; adding one link may leave incorrect
links behind. Use the transaction-only action unless historical bulk scope is approved.

Use consistent source-backed history and provider details. If needed, research the
merchant with minimal name/region/currency context; do not send account IDs, private
notes or full financial records to web search. Retain confirmed purchase-specific
mappings privately and leave uncertain cases unresolved.

## Completion evidence

Use `transaction reconcile` or `transaction unreconcile` for source-verified flag
changes. Select commands and handle per-operation fallback through
[CLI operations](cli-operations.md); GUI completion always returns routing to CLI.

For each account retain source interval, complete ledger coverage, balance scope,
verified/remaining IDs and reminder state. Re-read both transfer legs and flags after
all changes. Zero unreconciled rows only covers the verified active scope, not archived
backlogs. Reminder notes can use `Source; method; verified through; exception`.
Read its current occurrence before completing it; never tick its successor merely
to repair a stale note. Preserve intentional skips and unresolved checks.
