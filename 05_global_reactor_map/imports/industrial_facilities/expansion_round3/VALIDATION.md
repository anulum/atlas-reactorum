<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round3/VALIDATION.md
-->

# Validation report

Validation date: **2026-09-28**

Command:

```bash
python3 validate.py
```

Result:

```text
PASS: 722 licensed UK facility records; deterministic rebuild; no inferred reactors, capacity, status, or coordinates
```

## Verified assertions

- Exact 18-column output schema and 11-column compact-snapshot schema.
- 722 output records and 722 snapshot records.
- 722 unique `stable_id` values and 722 unique source record IDs.
- Stable-ID set exactly matches `uk-prtr:<source_record_id>` for the snapshot.
- No stable-ID collision with the current base layer or round-two expansion.
- Every record is from reporting year 2024 and matches one of the documented NACE prefixes.
- Every output record has a name, operator, numeric in-range source coordinate, classification, source URL, licence, and verification note.
- Every record is labelled `United Kingdom` and uses an HTTPS official source URL.
- All `reactor_type_if_explicit` and `capacity` values are blank.
- All status values explicitly say that operating status is not asserted.
- Manifest contains the official raw-source URL, 5,619,305-byte size, 5,802 raw rows, 722 selected rows, and SHA-256 `f3f10db63ad7e7980d40454abdd47bcd4cd45aeabe69ad0130607916c3bc4841`.
- Rebuilding from the compact snapshot leaves the output SHA-256 unchanged (`fdc53c72b00d28cc6b3b11134045a9c39d82c550680425349a32a954d6377bd7`).

## Coverage breakdown

| NACE division | Records |
|---|---:|
| 10 — food products | 338 |
| 11 — beverages | 52 |
| 17 — paper and paper products | 36 |
| 19 — coke and refined petroleum | 18 |
| 20 — chemicals and chemical products | 225 |
| 21 — pharmaceuticals | 39 |
| 22 — rubber and plastic products | 14 |
| **Total** | **722** |

The 18 records with a blank Annex I activity code remain included because the systematic filter uses the populated NACE main economic activity, not Annex I activity. This is documented source absence, not inferred data.

## Interpretation limits

Passing validation means the layer faithfully and reproducibly represents the selected public-register fields. It does not verify facility operations independently, establish present operating status, locate individual equipment, or prove that any facility contains a reactor.
