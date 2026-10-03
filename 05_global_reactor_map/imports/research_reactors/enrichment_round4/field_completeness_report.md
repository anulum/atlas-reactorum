<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/enrichment_round4/field_completeness_report.md
-->

# Research-reactor field completeness

Generated 2026-09-28 from the 172-row base plus non-empty overlay values. The baseline is the effective state after rounds 1-3; the comparison includes round 4.

`unknown_or_generic_reactor_type` counts blank, `unknown`, and the generic placeholder `research reactor` as incomplete. Other fields count only blank or `unknown`. An unpopulated shutdown date is not necessarily a defect for an operating reactor; it is reported as field population, not applicability.

| Field | Unknown after round 3 | Unknown after round 4 | Reduction | Round-4 completeness |
|---|---:|---:|---:|---:|
| `unknown_status` | 96 | 85 | 11 | 50.6% |
| `unknown_or_generic_reactor_type` | 122 | 112 | 10 | 34.9% |
| `unknown_thermal_power_mw` | 147 | 136 | 11 | 20.9% |
| `unknown_operator` | 114 | 104 | 10 | 39.5% |
| `unknown_purpose` | 138 | 125 | 13 | 27.3% |
| `unknown_first_criticality` | 161 | 152 | 9 | 11.6% |
| `unpopulated_shutdown_date` | 133 | 131 | 2 | 23.8% |

Country-level counts for both stages are in `field_completeness_by_country.tsv`; machine-readable global totals are in `field_completeness_summary.tsv`.
