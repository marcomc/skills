# UI and runtime techniques

Observed techniques, not fixed coordinates or permanent API guarantees. Use only
the current computer-use tool's documented interface. MoneyWiz GUI/URL techniques
below apply only to a single operation that CLI could not complete. After verifying
it, return automatically to CLI; provider authentication uses its own source route.

## Capability and database identity

Distinguish installed `moneywiz`, its bundled API and a development API checkout.
Inspect runtime metadata before assuming a checkout edit updates the installed tool.

```sh
moneywiz --version
moneywiz --db "$db_file" identity --app "$moneywiz_app"
moneywiz --db "$db_file" compatibility --format json
```

The 0.3.0 CLI provides bounded W01–W09 transaction and payee writers, including
approved fuzzy pairs. See [CLI operations](cli-operations.md) and installed help.
The legacy `merge-duplicate-payees --apply` remains blocked; use `payee merge` for
admitted exact/fuzzy pairs. Revalidate admission per operation and current runtime;
a model checksum or version match does not enable every writer.

Before authorized Core Data apply let sync settle, close MoneyWiz and verify it stopped.
Follow the recovery policy; use a consistent SQLite backup with a read-only source
connection when snapshotting, including WAL contents. Plain copying an active main
file may be incomplete. Process checks are not an exclusive lock. Reopen the intended
app afterward, read records and verify sync; result counts do not prove remote acceptance.

`identity` discovers supported apps/stores and rejects ambiguous selections. Explicit
`--db`, `--app`, `--model` and store-local `--owner` bind the intended runtime;
`MONEYWIZ_APP` and `MONEYWIZ_MODEL_PATH` are also supported. Discover the current
compiled model, not a hardcoded number. Apply/recover must match the reviewed plan's
app, model, store and owner; edition-specific admission remains operation-specific.

For `CreditCardAccount.statement_day` failures preserve the full traceback: a historical
build first rejected nullable `Account.info`, then `as_dict()` failed before
subclass initialization. The last exception does not prove a missing statement column.
Record the limitation and use a supported read fallback; defer code repairs.

## MoneyWiz URL actions

The [official URL contract](https://help.wiz.money/en/articles/4525440-automate-transaction-management-with-url-schemas)
uses account **names without spaces**, payee names and category hierarchy paths, not
database IDs. `memo` supplies notes; encode parameter values. A ticker used as payee
does not populate a security symbol.

Verify a new app/account route with `save=false`; after targeting is proven and creation
authorized, `save=true` can reduce entry work. Dispatch to the discovered app explicitly:

```sh
open -a "$moneywiz_app" "$moneywiz_url"
```

The action is asynchronous and returns no record ID. Compare before/after to prove
exactly one expected record with correct account, date and fields. If nothing appears,
inspect the current editor and selected account before retrying. The observed UI
sometimes retained the selected account or failed from another account.
Verify through CLI where possible, then start the next operation with CLI. An unknown
native-writer outcome must be resolved before dispatching an equivalent URL action.

Do not invent URL parameters for edits, deletes, reconciliation, Buy/Sell or linking
FX imports. Documented transfers lack destination currency amount/rate. Holding price
updates may affect every matching symbol in the specified currency, so are not scoped
transaction edits.

## Native MoneyWiz interaction

- Select the row until highlighted, then double-click. An unselected double-click
  may only select. Prefer row right-click for Edit/Delete/Change Category.
- Maximize wide ledgers: an AX action can target a row centre off-screen. Resolve
  the full current description before destructive actions. Never derive deletion
  coordinates from a scaled or stale screenshot.
- Refresh AX after navigation, field edits or errors. A visibly open menu absent
  from AX can be used through current screenshot-grounded pointer input.
- When linked dates must align, select the **Send date day**, press Up then Down,
  observe Receive date update, and save once. Direct AX text assignment can omit
  the control event. Preserve genuine distinct source dates unless the profile
  explicitly requires alignment.
- Earlier experiments used two saved date changes; later verified visual nudges
  worked in one edit, including converted FX. A second Save click may only commit
  focus. Check editor closure and both persisted dates; diagnose before retrying.
- Search `=amount` and semicolon-combined terms can isolate a row. For visible
  verified rows use the blank tick-column cell. Never toggle an existing tick.
  Bulk actions require verified selection scope/count and final flag readback.
- Set security type before price. Asset Adjust Balance uses asset currency, not
  fiat valuation currency. Fixed-decimal fields can interpret digit sequences at
  eight places: always verify the rendered value before saving.
- On an incorrect deletion stop the batch. Inventory surviving links and use
  verified Undo/recovery, or reconstruct the saved preimage when authorized.
  Check amount, currency, dates, metadata, links and flags before continuing.

## Browser and authentication

Use existing authorized browser profiles and saved-login autofill. Cookie layers and
native Passwords overlays can hide login fields; dismiss them before diagnosing a site
failure. Use the configured password manager's autofill when allowed.
Verify asynchronously filled values before submitting.

Use native SMS suggestions where available. Authorized email verification uses the
configured CLI or connector; do not switch clients without a task-specific reason.
Do not retain OTPs or approval URLs. Complete device approval in the initiating browser
session. Restart expired logins from the provider landing page, not an old session URL.

Follow profile Remember me/trusted-device preferences. A menu-only Safari tree was
recovered with Command+L, Escape, Tab; try focus recovery before declaring failure.
Distinguish tool connection timeouts from observed device locks. Avoid identical retry
loops; retain source captures and take the next supported route.
