<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/enrichment_round5/README.md
-->

# Research-reactor enrichment, round 5

This directory is a self-contained, non-destructive exact-ID overlay for the 172-row research-reactor catalog. It adds eight high-value official-source records from Brookhaven National Laboratory, Idaho National Laboratory, Oak Ridge National Laboratory and the Belgian Nuclear Research Centre. The base dataset, rounds 1-4, integrated catalogs and presentation files are not modified.

## Files

- `research_reactor_enrichment_round5.tsv`: patch keyed by existing `stable_id`; blank factual cells mean no change.
- `source_registry.tsv`: included, companion and deliberately excluded evidence with rights decisions.
- `generate_gap_report.py`: deterministic effective-state merge and field-completeness report generator.
- `field_completeness_summary.tsv`, `field_completeness_by_country.tsv`, `field_completeness_report.md`: before/after reports across every base ID.
- `validate_enrichment_round5.py`: schema, value, provenance, report and immutability checks.

## Evidence rules

Every row is an exact named-device match to an existing base ID. First-criticality values are populated only when an official operator source explicitly says criticality; operation or commissioning dates are not substituted. Thermal power records the explicitly identified steady-state, rated or maximum operating level, with distinctions preserved in notes. No values are taken from the IAEA Research Reactor Database.

No coordinates are added. None of the selected official sources published a numeric coordinate pair, and names, addresses, campuses or cities were not geocoded or converted to points. This is why coordinate completeness is unchanged even though coordinates remain a reported priority field.

The source material remains under source copyright. Only isolated factual assertions are normalised here; prose, figures, tables and database portions are not reproduced. The excluded thesis is recorded to make the first-criticality omission for BR2 auditable.

## Apply semantics

Overlay rows use the base 19-column schema. Join on `stable_id`, then replace only fields whose patch value is non-empty. Provenance fields describe this overlay and should be retained alongside earlier provenance rather than treated as a destructive replacement.

## Validation

Run:

```bash
python3 validate_enrichment_round5.py
```

The validator regenerates reports and checks exact base-key membership, duplicate IDs, controlled status values, numeric power, partial dates, HTTPS provenance, registry coverage, no coordinate changes, and SHA-256 immutability of the base and all four earlier overlays.
