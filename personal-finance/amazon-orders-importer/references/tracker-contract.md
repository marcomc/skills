# Tracker contract

Read live headers and formulas and stop on mismatch; this describes the tracker
at the time the skill was authored, not permission to repair a changed schema.
Use the configured spreadsheet and confirm its parent and account independently.

## Annual tabs

| Column | Meaning | Owner |
| --- | --- | --- |
| A | ISO date | Source |
| B | Order ID | Source and stable key |
| C | Original order total in EUR | Source |
| D | Payment method as returned | Source |
| E | Primary payment label | Literal or formula linked to `Pagamenti` |
| F | Person | Sheet formula; maintained through `Carte` |
| G | `Attivo` or `Annullato` | Source |
| H | Month | Existing sheet formula |
| I | Selected payment components | Sheet formula from `Pagamenti` |
| J | Refund amount | Source; order-level refund |
| K | Total payment components | Sheet formula |
| L | Refund included for the selected methods | Sheet formula |

Rows 2–2001 have formulas in F, H, I, K and L; some E cells are also
formulas linked to `Pagamenti`. Never overwrite existing formula cells.
They also define the dashboard's supported row range; fail closed before
appending beyond it. Do not equate a payment label with a card charge when
Amazon shows multiple payment methods or a gift card.

## Articles and cards

`Articoli` columns A:O are year, date, order ID, payment label, formula-derived
person, title, ASIN, reported price, quantity, suggested category, order status,
inclusion formula, estimated allocated spending, item weight and month. Preserve
existing category values. Some D cells link to `Pagamenti`; preserve them.
Rows 2–2001 contain formulas in E and L:O; copy or
extend them safely for imported rows without overwriting them. Annual tabs and
article calculations currently support up to row 2001. Never append beyond
that bound without safely extending every dependent range and chart. Treat the
source's line items as a multiset: identical records in a single order may be
legitimate. Do not deduplicate them away.

`Pagamenti` columns A:M are year, order date, order ID, payment label, person,
component type, amount, order status, inclusion, selected amount, provenance,
quality and month. Rows 2–3500 have formulas in E, I, J and M. An order may
have multiple component rows; never collapse card and gift balance. Unknown
cards use `Non disponibile`; do not infer them from masked digits.

`Carte` columns A:D are payment label, person, inclusion formula and total.
The actual inclusion checkboxes and year selections are on `Dashboard`; preserve
all selection values. New labels require a corresponding dashboard control,
linked formula in `Carte`, blank owner and translated total formula. Validate
all linked formulas and chart ranges before writing. Categories are maintained
in `Categorie` rows 2–36 and referenced by article validation; preserve existing names
and assignments. Category costs are estimates allocating gross order totals in
proportion to item weights; missing quantities count as one. Keep this limitation
visible and check that category totals reconcile with represented orders. Do not
silently omit new categories or cards from summaries and charts: extend their
ranges when safe, otherwise report them for review.

## Baselines and provenance

The initial protected year exports are the first source snapshots, not proof that
a later source fetch is complete. Compare a stable configured anchor with both
that snapshot and the sheet, alongside the account greeting from the same CLI
session. For changes to existing source-owned values, compare sheet, prior
verified source and current source field by field. A source value may be
updated only if the sheet still equals the previous verified projection. Blank
or missing baselines, changed sheet values, duplicate order IDs and conflicting
item identities require review, not a guess. Preserve newer manual values.

After verified changes, retain an atomic private baseline for the next run and
its import receipt. Do not replace a good baseline with partial source data.
The CLI's successful exit or a nonempty response alone is not coverage proof.
For ambiguous writes, reread the full affected rows before deciding anything;
never replay the same mutation solely because its response was lost.

## Noninteractive Amazon session

Use the Python interpreter from the installed `amazon-orders` environment. The
following pattern checks the existing session without invoking its login forms:

```python
from amazonorders.conf import AmazonOrdersConfig
from amazonorders.orders import AmazonOrders
from amazonorders.session import AmazonSession

config = AmazonOrdersConfig(data={"domain": "amazon.it"})
session = AmazonSession(config=config, auth_forms=[])
if not session.check_session(verify=True):
    raise RuntimeError("Amazon session requires user sign-in")
session.is_authenticated = True
orders = AmazonOrders(session).get_orders(
    year=2026, keep_paging=True, full_details=True
)
```

Resolve the domain and years from private configuration and the current date;
the literals above are examples. Verify the greeting through this same session
with a read-only account-page request and `persist_cookies=False`; compare it
with the configured expected greeting. No login, CAPTCHA or OTP handler is
called. A successful session check alone does not establish account identity or
complete history; confirm the configured anchor and all source results too.

On the observed account, a later full-detail fetch omitted payment references
for many previously populated orders, including an individual detail request.
`full_details=True` and a successful response do not establish field coverage.
When payment data disappears on an existing order, preserve its live payment
fields and trusted baseline; record the missing data and do not infer removal.
Check the transaction source, but never replace existing manual or previously
verified payment data without a clear, reconciled per-order comparison.

## Transaction reconciliation

Use `AmazonTransactions` with the same verified session and complete pagination;
confirm identity as above. Transaction signs distinguish charges and refunds.
Group all available records by exact order number, retaining multiple payments
and refunds separately. Compare payment method, masked digits, currency and
amounts; never match a card by last four alone. A gift-card balance and a bank
card can both pay one order. The annual schema has only one primary payment label; use `Pagamenti` to
represent each verified component separately. Do not infer the bank-card charge
from the full order amount or convert a gift-card label by matching digits.

For new orders, the maintained importer requires complete item data, exact
order IDs on every transaction, configured payment labels and reconciled card
and gift charges. It defers incomplete, mismatched or unknown components. It
updates existing status and refunds only when the previous baseline still
matches the sheet; changed amounts or item details are deferred. Verify every
written cell and
never replay an uncertain mutation. `Statistiche` is independent of the
Dashboard filters; the Dashboard and `Categorie` follow selected payments.
Do not claim complete transaction history solely because pagination finished:
this account's 1500-day request returned almost no 2023–2024 history.
Targeted `get_transactions(order_id=...)` can retrieve older records, but on this
account some responses included unrelated order numbers. Verify every returned
order ID before using any transaction and defer mismatches; a filtered request
is not proof that all its rows belong to the requested order.
