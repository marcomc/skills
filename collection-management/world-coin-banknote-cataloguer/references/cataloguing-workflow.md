# Cataloguing Workflow

## Contents

- [Object Inventory](#object-inventory)
- [Side Pairing](#side-pairing)
- [Research and Side Naming](#research-and-side-naming)
- [Confidence and Consistency](#confidence-and-consistency)
- [Special Items](#special-items)

## Object Inventory

Inspect every image at sufficient resolution. Assign `BANKNOTE-1`, `COIN-1`, or
another stable temporary ID to each physical object. Record an approximate
location such as `upper-left`, `middle-centre`, or `lower-right`, plus:

- object type, country, denomination, currency, colour, dimensions, and shape;
- all legible text, dates, serials, prefixes, suffixes, and mint marks;
- portraits, emblems, security features, monuments, animals, landscapes,
  artworks, events, edge details, and commemorative wording;
- the source image and which side appears to be visible.

Preserve serial letters and leading zeroes exactly. Keep observations separate
from researched conclusions.

## Side Pairing

Position is supporting evidence, never the sole match.

For banknotes, rank signals as follows:

1. Matching serial or another decisive unique mark.
2. Denomination.
3. Country and currency.
4. Exact series and design.
5. Dimensions and orientation.
6. Photograph position.

A serial mismatch, denomination mismatch, or country mismatch is a hard
contradiction unless the image reading itself is uncertain. When several notes
share a denomination, compare serials, prefixes, security features, and design
details before considering position.

For coins, compare denomination, year, country, apparent composition, diameter,
edge shape, portrait or effigy, commemorative theme, and finally position.
Multiple identical-looking coins may remain unresolved.

Use `scripts/catalogue_records.py pair` for a reproducible one-to-one proposal
when both sides have structured observations. Review its evidence and rejection
reasons; the score cannot repair inaccurate observations.

## Research and Side Naming

Search combinations of country, denomination, year, currency, serial prefix,
distinctive text, and `coin`, `banknote`, `obverse`, or `reverse`. Research the
exact issue whenever a design may vary.

Prefer sources in this order:

1. Central or national bank.
2. Official mint.
3. Government or national museum.
4. Specialist numismatic catalogues.
5. Numista.
6. Other reputable numismatic sources.

Use lower-authority sources to supplement, not displace, stronger evidence.
Keep the source URL and the claim it supports in the internal audit. If sources
disagree on obverse and reverse, prefer issue-specific official terminology and
investigate rather than silently choosing.

Descriptions must identify the subject, not its broad class. For example, use
`Canadian National Vimy Memorial`, not `building`, and `Bluenose schooner`, not
`ship`. Follow the live database's language and naming style. In the default
database, prefer concise Italian descriptions where practical while retaining
internationally recognized proper names.

Do not assume a portrait is the obverse. Map the issue's actual sides to the
collection's `Dritto` and `Rovescio` semantics.

## Confidence and Consistency

Use these internal levels:

- `HIGH`: definitive visual evidence or an authoritative exact-issue match.
- `MEDIUM`: a strong match with a secondary attribute still uncertain.
- `LOW`: multiple plausible issues or inadequate photographic evidence.

Research `MEDIUM` candidates further. Do not write uncertain key identifiers
for `LOW` candidates; request another photograph or retain blank cells.

Before any write, reject contradictions such as different denominations across
paired banknote sides, incompatible countries, or a design that cannot belong
to the identified issue. Do not merge same-year commemoratives based only on
denomination and date.

## Special Items

Tokens, medals, promotional pieces, private issues, and novelty objects may not
have a sovereign currency or ISO 4217 code. Record the supported classification
and useful identifying context without inventing currency fields. Preserve an
existing uncertain record unless stronger evidence and update authorization are
both available.
