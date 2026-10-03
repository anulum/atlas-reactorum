<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/enrichment_round4/README.md
-->

# Research-reactor enrichment, round 4

This directory provides a fourth standalone exact-ID overlay and a reproducible field-completeness audit for the 172-row research-reactor discovery dataset. It does not modify the base dataset, earlier overlays, or presentation code.

## Overlay scope

`research_reactor_enrichment_round4.tsv` uses the base 19-column schema. Empty factual cells mean **no change**. Its 14 rows cover nine countries not represented in earlier enrichment rounds: Algeria, Argentina, China, France, Germany, India, Italy, the Philippines and Sweden.

The overlay adds lifecycle status, detailed design, thermal power, operator, purpose and dates only where exact identity is supported by a regulator, government, national atomic-energy body or primary operator. Fuel, coolant, moderator and reflector details are normalised into `reactor_type` and explained in `verification_notes`, because the base schema has no dedicated columns for them.

No coordinates are added or changed. No new facilities are introduced.

## Completeness reports

- `field_completeness_by_country.tsv`: every country at the effective state after round 3 and after round 4.
- `field_completeness_summary.tsv`: global known/unknown counts and completion percentages by field.
- `field_completeness_report.md`: concise human-readable comparison.
- `generate_completeness_report.py`: deterministic report generator.

The type audit treats the exact generic placeholder `research reactor` as incomplete. Shutdown-date counts measure field population, not whether a shutdown date is applicable to an operating reactor.

## Evidence and reuse

Exact reactor-name or unambiguous acronym matches are required. Commissioning, inauguration and service entry are not treated as first criticality unless the source explicitly says criticality. Date precision is preserved. Thermal power is used only when explicitly identified; exact W/kW-to-MW conversions are documented.

Argentina.gob.ar content is licensed CC BY 4.0 unless otherwise stated. Other sources are used only for isolated factual assertions, with source copyright retained; no prose, figures, tables or substantial database portions are copied. Rights decisions and companion sources are recorded in `source_registry.tsv`.

The IAEA Research Reactor Database was not scraped, bulk queried, copied or redistributed.

## Validation

Run:

```bash
python3 validate_enrichment_round4.py
```

The validator checks schema, exact base-key membership, coordinates, controlled statuses, powers, calendar-valid dates, HTTPS provenance, rights declarations, registry coverage and report regeneration.
