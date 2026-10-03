<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/DATA_DICTIONARY.md
-->

# Data dictionary

`data/reactors.tsv` is the normalised flat exchange table. `data/reactors.geojson` is a generated map view. The JSON schema remains the conceptual canonical model; this first release does not change it.

## Identity and classification

- `id`: stable source-prefixed identifier; checked-in WRI records use `wri-gppd-…` and optional Wikidata records use `wikidata-q…`.
- `name`, `aliases`: English display name and pipe-separated aliases.
- `record_kind`: schema-controlled kind (`facility`, `reactor_unit`, `experimental_device`, `project`, `claim`, `taxonomy_only`).
- `domain`, `reactor_type`, `subtypes`, `purpose`: broad domain and source-derived class/type. Multi-values use `|`.
- `status`: normalised schema status. `unknown` is preferred over inference without a cited assertion.
- `evidence_maturity`: evidence about physical/technical maturity, not commercial promise. The checked-in WRI nuclear-plant subset uses `established`; the optional Wikidata importer assigns `active_research` to fusion devices. These are coarse class defaults, explicitly not current-status or reactor-readiness verification.

## Location

- `site`, `city`, `region`, `country`, `country_code`: place fields; `country_code` is ISO 3166-1 alpha-2.
- `latitude`, `longitude`: WGS84 decimal degrees, map-ready.
- `coordinate_precision`: `exact`, `site`, `city`, `region`, `country`, `withheld`, or `unknown`.
- `coordinate_source`: URL identifying where the coordinate assertion came from.

## Organizations, technology and dates

`owner`, `operator`, `designer`, `regulator`, technical fields, capacities and dates mirror `reactor-map.schema.json`. Blank means not asserted by this import, never zero. Dates are ISO 8601 where source precision allows it.

## Provenance and verification

- `source_url`, `source_publisher`, `source_title`, `source_role`, `source_license`: record-level provenance.
- `source_quality_flags`: semicolon-delimited warnings. Every checked-in row states that it is plant-level rather than unit-level, lacks status/historic coverage, and has unverified coordinate precision. Optional Wikidata rows are explicitly labelled community-edited and non-authoritative.
- `last_verified`: retrieval/automated validation date, not proof that the real-world status was independently confirmed that day.
- `verification_notes`: required human-readable limitation and next verification step.

GeoJSON retains the core classification, provenance and quality fields in `properties`; geometry is Point `[longitude, latitude]`.

The integrated presentation dataset retains 1,631 verbatim source assertions: 1,092 end-use
labels and 539 feedstocks or fuel classifications. They supply purpose/use
for 1,342 records and fuel/feed classifications for 533 records. Six secondary
WRI categories remain classifications of whole plants. Per-field provenance
records the original cell, source identifier, capture date, licence and hash;
unknown reactor composition and current physical operation remain unknown.
The facility dataset uses schema 1.1.0. Multiple fuel categories use `; `
while their original cells remain separate in `field_observations`. Search, facility details and filtered
CSV/JSON retain these fields, and CSV carries the assertion array as JSON.
