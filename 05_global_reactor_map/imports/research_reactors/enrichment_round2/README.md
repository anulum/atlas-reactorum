<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/enrichment_round2/README.md
-->

# Research-reactor enrichment, round 2

This directory is a second, standalone overlay for the 172-row research-reactor discovery table. It covers exact official-source matches outside the first U.S./Canada tranche and does not modify the base dataset or presentation.

## Contents and scope

`research_reactor_enrichment_round2.tsv` has the same 19 columns as the base dataset and is keyed by `stable_id`. Non-empty factual cells are additions or reviewed replacements. Empty cells mean **no change** and must never erase a base value.

The 12 rows cover Australia (3), United Kingdom (1), Japan (3), South Korea (1), Austria (1), Poland (1) and Czech Republic (2). They add 12 status overlays, 11 operators, nine reactor-type descriptions, nine thermal-power values, 10 purpose descriptions, and seven first-criticality plus three shutdown-date values. No coordinates are added: none of the reviewed sources provided a reactor-specific point whose identity and precision improved safely on the base.

No `new_facilities.tsv` is included. The reviewed sources did not establish a clearly missing named reactor with enough open, unit-level metadata to justify expanding the base in this pass.

## Evidence rules

- Identity must be exact by reactor name or an unambiguous official acronym/expanded-name pair.
- Start of operation, commissioning and licence issue are not treated as first criticality.
- Date precision is retained exactly: `YYYY`, `YYYY-MM` or `YYYY-MM-DD`.
- Licensed/rated power is stored as thermal only when the source explicitly describes reactor thermal power. Unit conversions are exact and noted.
- `operational` requires a current operator/regulator page presenting the reactor as operating or an active facility. Historical pages alone do not establish current operation.
- No city, campus, site or organisation centroid is used as a reactor coordinate.

## Reuse and rights

The GLEEP source is GOV.UK material under the Open Government Licence v3.0. Several national operator and regulator pages reserve copyright or do not state an open licence. For those sources the overlay records only isolated factual assertions—names, statuses, powers, dates and classifications—without copying source prose, images or a substantial portion of any database. Their copyright is retained and the overlay does not purport to relicense their content. `source_registry.tsv` records this distinction per source.

The IAEA Research Reactor Database was not scraped, bulk queried, copied or redistributed because no unambiguous open bulk-redistribution licence was found.

## Validation

Run from this directory:

```bash
python3 validate_enrichment_round2.py
```

The validator checks schema, unique base-key membership, controlled statuses, paired/ranged coordinates, numeric powers, date syntax, HTTPS provenance, declared rights basis and the requirement that each row changes at least one factual field.
