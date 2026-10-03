<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/fusion/enrichment/VALIDATION_REPORT.md
-->

# Validation report

Validation date: 2026-10-02 (public compilation selection; original layer date 2026-09-27)

Result: **PASS**

## Machine checks

- Base dataset exists with 146 records.
- Public base SHA-256: `6ce4b68d1904d0785a67a15891963496002c6671e52c95e2ffd6247827cbaab3`. The complete original base has a separate frozen digest.
- `enrichment.tsv` contains 11 unique keys and every key exists in the base dataset.
- `new_facilities.tsv` contains 11 unique keys and no key or case-folded display name collides with the base dataset.
- Both data files have the exact 18-column fusion schema.
- All records have an HTTPS source, source role, retrieval date, reuse statement and verification note.
- Dates are ISO year, year-month or full-date values.
- Coordinate pairs are complete when present and require a precision note.
- The source registry has 14 unique source IDs, valid HTTPS URLs and the correct retrieval date.

Command:

```text
$ python3 validate_enrichment.py
PASS: immutable base hash verified; 11 enrichments and 11 new facilities valid
```

## Coverage audit

| Measure | Count |
|---|---:|
| Base records audited | 146 |
| Public base records missing a complete coordinate pair | 146 |
| Base records with unknown status | 1 |
| Existing records enriched | 11 |
| New named physical devices added | 11 |
| Coordinate overrides/additions | 0 |
| Current operating devices newly added | 1 |
| Historical devices newly added | 10 |

The zero coordinate additions are intentional. None of the selected primary sources published a device-point latitude/longitude. Campus addresses, company headquarters and city centroids were not converted into machine coordinates.

## Interpretation limits

- FuZE is marked operating only to the extent explicitly stated by Zap Energy for 2023; the evidence note preserves that temporal qualifier.
- JT-60SA is described as in an upgrade outage within commissioning, based on the implementing agency's 2025 update; this avoids presenting the machine as continuously operating.
- NSTX-U remains under construction based on PPPL's February 2025 report; a future expected start is not recorded as an achieved operation date.
- Tore Supra and WEST share hardware lineage. The historical Tore Supra row must not be counted as a second current device.
- This enrichment is a primary-source tranche, not a complete world history of every plasma experiment.

The public base intentionally omits the separate original Wikidata values. This PASS establishes source schema, identity and declared data consistency, not independent factual verification or a grant over the cited primary sources. Full original input validation requires --base-selection frozen with the exact original input paths.
