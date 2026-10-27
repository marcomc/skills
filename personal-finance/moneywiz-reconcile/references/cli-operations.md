# CLI operations

Use the installed `moneywiz` for each supported read and write. This mapping reflects
0.3.0; check installed `--version`, command `--help` and per-operation compatibility
before using it. A development checkout does not update an installed bundle.

## Reads and identity

| Need | CLI route |
| --- | --- |
| App/model/store/owner binding | `identity --app APP`; add explicit `--model`/`--owner` when needed |
| Complete reconciliation graph | `snapshot --account ID --until TIMESTAMP --timezone IANA` |
| Accounts | `accounts --format json --diagnostics` |
| Full ledger and relationships | `transactions --account ID --all-fields --with-categories --with-tags --limit 0 --format json --diagnostics` |
| Holdings | `holdings --account ID --format json --diagnostics` |
| Categories | `categories --user ID --full-name --format json` |
| Exact persisted record | `record --gid GID` |
| Runtime operation status | `compatibility --format json` or its supported `--capability KEY` selector |

Pass global `--db "$db_file"` for the resolved store. Parse the complete output and
its completeness diagnostics. Exit `3` means partial reads, not absent transactions
or zero holdings; block dependent plans until missing evidence is recovered. Keep
independent operations moving through CLI. Snapshot completeness includes the loaded
graph beyond the selected account; inspect the exact failed managers/identities.

`--until YYYY-MM-DD` is inclusive at local midnight, with UTC as default timezone.
It excludes the rest of that day. Use an explicit offset timestamp or full-ledger
analysis for the intended cutoff. Native cached balances are not bank verification.

## Write selection

For the request-based commands below, supply
`--request "$request_file" --plan "$plan_file"`.
Construct the typed JSON from current read-back, exact prior values,
source evidence and the documented operation contract; never invent fields or use
a generic entity/key-value plan. Consult the matching MoneyWiz Tools `doc/TRANSACTION-*.md`
or `doc/PAYEE-CONSOLIDATION.md` when request fields or admission are unclear.

| Operation | Plan builder |
| --- | --- |
| Income, expense or linked refund | `transaction create` |
| Supported scalar edits | `transaction edit` |
| Payee/category split replacement | `transaction assign` |
| Reconcile or reverse reconciliation | `transaction reconcile` / `transaction unreconcile` |
| Ordinary balance, investment cash, asset quantity or aggregate total | `transaction adjust-balance` |
| Latest aggregate investment-total adjustment deletion | `transaction delete-adjustment` |
| Supported generic deletion, including complete dependent groups | `transaction delete --target GID --reason TEXT --evidence-note TEXT --plan FILE` |
| Imported withdrawal/deposit replacement with linked transfer | `transaction transfer` |
| Investment cash event, Buy/Sell or first Buy creating a holding | `transaction investment` |
| Exact or approved fuzzy payee pair | `payee merge --kind exact\|fuzzy --source-gid GID --survivor-gid GID --evidence-note TEXT --plan FILE` |

Generic deletion and payee merge build plans from native read-only inventory, rather
than `--request`. Repeat `--target` for the complete refund/transfer dependency group.
Fuzzy merge also requires `--fuzzy-map "$private_review_csv"` with an approved pair;
pending/rejected pairs are no-ops. Preserve CSV decisions and re-read inventory after
each merge. `reassign-payees-by-id` remains a separate legacy supported interface;
legacy `merge-duplicate-payees --apply` is blocked, not an alternative W09 apply path.

## Execution and recovery

Let sync settle and keep the bound MoneyWiz app closed through plan preparation,
apply, recovery and native verification. Keep requests, plans, journals and financial
output private. Review the coherent operation and validate its exact digest:

```sh
moneywiz write validate --plan "$plan_file"
moneywiz --db "$db_file" write apply --plan "$plan_file" \
  --app "$moneywiz_app" --model "$model_file" --owner "$owner_id"
moneywiz --db "$db_file" write apply --plan "$plan_file" \
  --app "$moneywiz_app" --model "$model_file" --owner "$owner_id" \
  --reviewed-digest "$reviewed_digest" --apply
```

Apply without `--apply` only inspects. The digest binds reviewed bytes; it does not
authorize a mutation. Use the user's existing authority for the exact operation.
The writer creates a consistent backup and journal before mutation; never substitute
raw SQLite writes or copy only an active database's main file as a complete backup.

Read back durable IDs, fields, links, flags and financial deltas before advancing.
Reopen the intended app for application/sync verification when needed. After a
timeout, missing response or uncertain result, inspect the journal and persisted
state, then recover the same plan with its original runtime binding:

```sh
moneywiz write locations
moneywiz write journal
moneywiz --db "$db_file" write recover --plan "$plan_file" \
  --app "$moneywiz_app" --model "$model_file" --owner "$owner_id"
```

| Recovery evidence | Next action |
| --- | --- |
| Applied or verified no-op; postconditions match | Verify and advance; do not duplicate via GUI |
| Safe to retry; every persisted preimage unchanged | Correct the CLI issue and retry within authority |
| Unknown, mixed, stale or contradictory state | Preserve evidence; keep this operation pending and refuse duplicate CLI/GUI writes |

Recovery does not automatically restore a backup. `write cleanup` is retention
tooling, not routine reconciliation; its mutation needs applicable scope/authority.

## Bounded support and temporary GUI fallback

Consult current admission, not just the command's existence. In 0.3.0:

- Ordinary create/edit/assign/reconcile cover `CashAccount`, `BankChequeAccount`,
  `BankSavingAccount`, `CreditCardAccount`, `LoanAccount`, `InvestmentAccount` and
  `ForexAccount`. Scalar edits cover
  Deposit/Withdraw/linked Refund, not every special transaction entity.
- Aggregate investment-total adjustment supports reviewed fiat/crypto catalogs and
  native precision with an explicit reporting rate, for the admitted account shape
  without holdings, valuation history or cached investment cash. The amount remains
  in account currency. Other ordinary/cash/quantity adjustments and generic deletion
  use the reviewed GBP/EUR/USD/CAD contracts; quantity supports up to eight decimals.
  New adjustment dates must be strictly after the latest account transaction.
- Transfer replacement supports zero-fee paired transfers. Investment writes support
  existing-holding Buy/Sell and first Buy creating a manual InvestmentAccount holding;
  creating Forex holdings via Exchange remains outside that contract.
- Generic deletion retains holdings, including zero-unit holdings, and requires
  complete linked refund/transfer groups. Scheduled, Exchange, budget-transfer and
  unsupported void records are not generic deletion capabilities.
- Live admission depends on the exact reviewed app edition/build, compiled model,
  store and operation. Fixture-only admission does not permit live writes. Recheck
  those facts; do not hardcode a version as blanket authorization.

When the needed operation is unsupported or a resolved CLI failure prevents it,
use the [GUI techniques](ui-and-runtime.md) only for that operation within authority.
Resolve unknown write outcomes first. Verify the GUI result, let sync settle and
refresh CLI identity/read-back. Discard stale plans and close the app before another
native write. **The next operation always starts with CLI**, without a user prompt;
another GUI fallback needs its own operation-specific reason. Do not patch the
program, capability matrix or installed dependencies during bookkeeping.
