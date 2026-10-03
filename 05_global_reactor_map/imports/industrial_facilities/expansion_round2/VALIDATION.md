<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round2/VALIDATION.md
-->

# Validation report — industrial expansion round 2

Validation date: 2026-09-27

Result: **PASS**

```text
$ python3 validate.py
PASS: 1,776 licensed facility records; deterministic offline rebuild; no inferred reactor types or coordinates
```

## Dataset checks

| Check | Result |
|---|---:|
| Total records | 1,776 |
| Canada NPRI records | 908 |
| Australia NPI records | 868 |
| Unique stable IDs | 1,776 |
| Records with complete published coordinates | 1,776 |
| Inferred coordinates | 0 |
| Populated reactor-type fields | 0 |
| Populated capacity fields | 0 |
| Retrieval date mismatches | 0 |
| Non-HTTPS row sources | 0 |
| Output SHA-256 | `85c2802ba3739b7cceca5998bb6a2961a7aaca664913ae95753288d98117e892` |

The validator also rebuilds the final TSV from `selected_source_snapshot.tsv` without network access and confirms that its SHA-256 is unchanged.

## Selection checks

- Canada: every row has latest filed report year 2024 and a NAICS code beginning `311`, `3121`, `322`, `324` or `325`.
- Australia: every row has latest report year 2024/2025 and a primary ANZSIC code beginning `11`, `12`, `15`, `17`, `18` or `19`.
- Canada contributes 377 source-sector `Chemicals`, 358 `Other Manufacturing`, 94 `Pulp and Paper`, and 79 `Petroleum and Coal Product Refining and Mfg.` records. The broader source-sector label is retained even where selection is driven by a more specific food/beverage NAICS code.
- Australia retains the published primary ANZSIC class name as `sector` and the exact class plus source `main_activities` as `process_or_activity`.

## Source snapshots

The manifest records the exact live inputs used on 2026-09-27:

- Canada NPRI geolocations: 13,651,974 bytes; SHA-256 `2dcb73082aac50a95446600e1e86b28aec2c48da502265002c05176af4be8781`.
- Australia NPI facilities: 3,248,241 bytes; SHA-256 `a0be4c37d588b391ea81baf240f675b2c9f3d9ee0210f9c451c7371eac11d6c7`.

The full raw downloads are not retained. The compact snapshot contains only the selected public identity, operator, coordinates, classification, report year and source-link fields. It excludes street addresses, postal codes, business registration numbers, facility websites, full report histories and pollutant quantities.

## Interpretation limits

- A public register coordinate is not necessarily survey-grade and may represent a facility reference point rather than a process unit.
- Reporting in the latest period does not prove that a facility is currently operating; status text explicitly avoids that claim.
- NPRI and NPI inclusion depends on statutory reporting scope and thresholds. Absence does not establish that a facility does not exist.
- Industry classification supports facility discovery only. It cannot establish the presence, count or design of reactors, digesters, fermenters or other internal equipment.
