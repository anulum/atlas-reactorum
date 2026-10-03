<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round4/VALIDATION.md
-->

# Validation report

Validation date: **2026-09-28**

Command:

```bash
python3 validate.py
```

Result:

```text
PASS: 93 reusable SwissPRTR records plus seven-jurisdiction source-gap audit; no inferred facilities or reactor claims
```

## Verified assertions

- The source-gap matrix contains exactly Japan, New Zealand, Switzerland, South Korea, India, Brazil, and South Africa.
- Switzerland is the matrix’s sole round-four import decision; every other source remains an evidence-backed backlog item.
- Exact 18-column output schema, 14-column compact-snapshot schema, and 12-column matrix schema.
- 93 output rows and 93 snapshot rows.
- 93 unique `swiss-prtr:<Facility ID>` stable IDs and 93 unique source facility IDs.
- No stable-ID collision with the base, round-two, or round-three industrial layers.
- Every snapshot row is a 2024 SwissPRTR point source matching one of the seven documented NACE divisions.
- Every output row has a name, owner, classification, provenance, reuse statement, and numeric coordinate within broad Swiss bounds.
- Original source LV95 values are retained and lie within plausible Swiss LV95 bounds.
- Every `reactor_type_if_explicit` and `capacity` value is blank.
- Every status explicitly says operating status is not asserted and carries the source’s 2024 completeness warning.
- Normal offline rebuilding is deterministic.

## Snapshot evidence

- Official workbook size: 3,106,306 bytes.
- Official workbook SHA-256: `895c1b4105787be5ef878893bc9249beacd5e2b64e2ffccc9e8246d8dd797bd5`.
- Parsed data rows across 2007–2024: 22,860.
- Selected unique 2024 facilities: 93.

## Coverage

| NACE division | Facilities |
|---|---:|
| 10 — food products | 14 |
| 11 — beverages | 1 |
| 17 — paper and paper products | 4 |
| 19 — coke and refined petroleum | 1 |
| 20 — chemicals and chemical products | 37 |
| 21 — pharmaceuticals | 34 |
| 22 — rubber and plastic products | 2 |
| **Total** | **93** |

## Interpretation limits

Validation confirms faithful transformation of the selected public-register fields and internal consistency of the audit artifacts. It does not independently verify facility operations, establish current operating status, identify equipment or reactors, or make the Swiss register complete where its publisher says the latest years remain partially unreleased.
