<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round5/VALIDATION.md
-->

# Validation report — industrial expansion round 5

Historical source capture: **2026-09-28**

Coordinate correction and read-only validation: **2026-09-30**

Result:

```text
PASS: 393 process-specific records from two reusable official sources; deterministic and no inferred vessel/status claims
```

## Verified assertions

- Exact 18-column output schema and 18-column compact-snapshot schema.
- 393 output records and 393 selected-source records.
- 362 UK REPD anaerobic-digestion planning-project records and 31 ADEME hydrogen-production site records.
- 393 unique stable IDs, exactly derived from the documented source keys.
- No stable-ID collision with the base layer or expansion rounds 2, 3 and 4.
- Every UK row matches the exact source technology and Great Britain jurisdiction rule; every French row has source `site_type == Production`.
- Every output point is numeric and in range; every UK snapshot retains numeric British National Grid coordinates.
- All status values are identified as source-published and not independently verified.
- All 31 French reactor-type fields are blank because ADEME does not publish a row-level production pathway.
- All 362 UK technology values are explicitly qualified as a source technology label, not a vessel design or count.
- The source-gap matrix covers anaerobic digestion/biogas, hydrogen production, wastewater treatment, refining, gasification/ammonia and fermentation.
- Only the two sources marked `IMPORT` in the matrix are built.
- A normal rebuild from the compact snapshot is byte-for-byte deterministic.

## Counts and hashes

| Artifact or measure | Result |
|---|---:|
| Output records | 393 |
| United Kingdom records | 362 |
| France records | 31 |
| Populated explicit-technology/reactor field | 362 |
| Blank French reactor-type fields | 31 |
| Populated explicit capacity field | 307 |
| Output SHA-256 | `4baa015e69de21434475a8d2d6c16189c649ac5159aa4ebafa73d7ff654780f5` |
| Selected snapshot SHA-256 | `90622a076bfab044aafa456cc544101c38f3872c6a42eeee4c996d3cecc8707d` |

The source manifest records these live inputs retrieved on 2026-09-28:

- UK REPD July 2026 CSV: 5,087,389 bytes; 14,657 raw rows; 362 selected rows; SHA-256 `84c1b5f958a934d8b4b86ec88f50bdcf43830ded7ff2efc27bffca0c98695035`.
- ADEME hydrogen API response: 51,920 bytes; 89 raw rows; 31 selected rows; SHA-256 `c818ce60aed135fadbb0e82c6200c295da860523862e9bce83bfb36e3b1f20d0`.

Live-source hashes may change when publishers update their services. The committed compact snapshot is the reproducible evidence input for normal offline builds.

## Interpretation limits

- REPD counts planning projects/records, not necessarily distinct physical facilities. The layer does not merge possible reapplications or revisions.
- REPD status is an administrative development status from the source and is not independent evidence of current operation.
- The WGS84 coordinates for UK records are a documented coordinate-system conversion of source-published British National Grid points, not geocoded or survey-verified positions.
- ADEME points may be parcel locations or commune coordinates; row-level precision is not supplied.
- ADEME says production in the dataset is mainly electrolysis, but that dataset-level description is not assigned to individual sites.
- Register absence does not establish that a facility or process does not exist. Deferred and backlog sources remain documented in `source_gap_matrix.tsv`.


## Corrected coordinate regression

The original parameter direction error was corrected on 2026-09-30. Only the
latitude/longitude cells of 362 UK records changed; all other observations and
all 31 French records stayed unchanged. An explicit independent PROJ 9.8.1
pipeline checked all 362 corrected points with maximum difference 0.000843 m.
The original coordinate displacement was 139.8–272.8 m. Transformation-step
accuracy remains limited by the approximate Ordnance Survey method and does not
verify source-point accuracy. Validation now runs its reproducibility build into
a temporary output and never rewrites the requested input tables.
