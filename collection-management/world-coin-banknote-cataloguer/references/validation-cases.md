# Validation Cases

These cases define observable behavior. Automated coverage lives in
`tests/test_catalogue_records.py`; image interpretation remains a reviewed agent
workflow rather than a static currency catalogue.

| Case | Input | Expected result |
| --- | --- | --- |
| New banknote | Canadian C$5 with a new exact serial. | `INSERT`. |
| Existing banknote | Canadian C$5 with an existing exact serial. | `SKIP EXACT DUPLICATE`. |
| Repeated new banknote | Two high-confidence records in one batch have the same new serial and exact metadata. | One `INSERT`; the later specimen is `SKIP EXACT DUPLICATE` and references the first decision index. |
| Conflicting new banknote | Two high-confidence records in one batch share a new serial but disagree on identity metadata. | All decisions for that serial are `NEEDS REVIEW`; no provisional insert remains. |
| Existing coin | Canadian C$1 2011, same design, stored quantity 1. | `UPDATE QUANTITY` to 2. |
| Different commemoratives | Two US quarters from 2015 with different reverse designs. | Two distinct records. |
| Ambiguous coin | Country, denomination, and year permit several designs; image is insufficient. | `NEEDS REVIEW`; do not guess. |
| Album year | Current year is 2026. | Integer `2026`, not string `"2026"`. |
| Currency correction | Ecuador 5 centavos 2000 was labelled ECS/sucre. | Propose `$`, `USD`, `Dollaro statunitense` from verified issue evidence. |
| Reordered photographs | Five fronts and backs; one object changes position. | Pair on serial, denomination, and design rather than position. |
| Globally unique pairing | A front has two locally equal candidates, while another front's serial constrains the complete assignment. | Accept the unique best complete assignment. |
| Globally ambiguous pairing | Several complete assignments have the same evidence-only score. | `NEEDS REVIEW` through an ambiguity error; photograph position cannot break the tie. |

For the paired-photograph case, structure observations with stable values such
as `serial`, `denomination`, `country`, `series`, `design`, and `position`, then
run:

```bash
python3 scripts/catalogue_records.py pair observations.json
```

Accept a pair only when the evidence is internally consistent. A position match
must never outweigh a serial, denomination, or country contradiction.
