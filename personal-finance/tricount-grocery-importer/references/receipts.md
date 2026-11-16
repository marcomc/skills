# Receipt acquisition and accounting

## Locate evidence

Reuse Drive files before downloading again. For Conad, use upstream JSON/folder
and source UUID to find the matching transaction in `transactions-*.csv` and its
`File Names` in `Attachments <title>`. Ignore Sesterce CSV for this mapping.
Reconstructed ordinal filenames are candidates, not verified receipt links.
Inspect the actual image date, merchant, total and products before accepting.

For Lidl, look for an already archived digital receipt, then open the authorized
account at `https://www.lidl.it/mre/purchase-history?&page=1`. Inspect actual
pagination and cover the relevant date range; never assume a fixed page count
or that page one contains everything. A website/authorization failure is not
proof that a receipt is absent. If unavailable in that account (for example,
another household member paid), search Tricount's archived photo attachments.
Save newly retrieved evidence in the configured Drive receipts folder with its
stable receipt ID. Preserve existing archived originals and sharing settings.

Match with receipt ID when available; otherwise corroborate date/time, store,
amount, source attachment linkage and products. Date + amount alone is not a
safe automatic match. Distinguish purchases and return vouchers, multiple PDFs
of one purchase, and equal-value separate purchases. Record ambiguous matches.
Do not fabricate product lines from the Tricount total when no receipt exists.

## Extract all lines

Extract native PDF text before OCR. OCR every relevant image/page, then visually
inspect ambiguous descriptions, quantities, decimal separators, line wraps and
promotions. Include all products, discounts and refunds, not only named examples.
Retain original descriptions and evidence alongside normalized categories.
When only part is legible, retain what is verified and label the receipt partial;
never balance a receipt with an invented product or discount.

Map products through the existing equivalence and family tables. Store is a
column, not a separate product table. Different brands may be equivalent, but
fresh/canned/frozen forms, food types and materially different pack contents
must not be merged without evidence. Private profile rules override defaults.

## Units and promotions

Use received quantity, including free items. Compare kg with kg, litres with
litres, eggs with eggs; a generic pack is not a cross-store unit. A verified
packaging source must match product variant and relevant period. Current retail
pages do not prove historical weight. Never infer eggs per pack from price alone.

- Two 250 g packs, total paid 2.99: E=2.99, F=2, S=0.5, T=kg.
  If gross 5.98 is documented, W=2.99; no extra negative discount. Net=5.98/kg.
- Gross product E=5.98 and a separate E=-2.99 linked with P: W=0;
  received quantity is still 0.5 kg, net=5.98/kg.
- Three identical packs for the price of two: received quantity includes all
  three. The nominal saving is one third only at equal pre-offer unit prices.
- `2 X 2.99` usually means quantity times price, not a 2-for-1 promotion.
- Mixed-item discounts may require proportional allocation. Keep negative E
  once; put negative X shares on products with sum equal to that discount,
  leave that discount's P blank and mark Y `Ripartito proporzionalmente`.
  The allocation is an estimate, not an observed individual checkout price.
- Store-wide Conad discounts remain separate unless a documented allocation is
  used. Lidl coupons usually link to products, but inspect rather than assume.
- Already reduced shelf prices count as the paid price. Quantify an additional
  embedded saving only with documented original price/offer evidence.

Do not equate “no promotion identified” with full price. Historical promotion
purchases do not establish how frequently the store offers those promotions.
Record missing formats, unallocated discounts and uncertain readings explicitly;
exclude them from verified price recommendations, while retaining real spending.
