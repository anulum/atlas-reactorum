<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/fusion/enrichment_round2/README.md
-->

# Fusion facility enrichment round 2

Date: 2026-09-28

This directory provides a bounded, non-destructive overlay for the effective 157-record fusion layer: 146 rows in `../fusion_facilities.tsv`, the prior exact-ID overlay in `../enrichment/enrichment.tsv`, and 11 prior additions in `../enrichment/new_facilities.tsv`.

`enrichment_round2.tsv` contains only exact stable-ID matches already present in that integrated layer. Non-empty cells replace the corresponding integrated value; blank cells mean no change. It adds primary-source operation milestones, fills four missing organization/country relationships, updates the current JT-60SA lifecycle description, and adds two CEA-published Cadarache host-campus coordinate pairs.

The two coordinate overlays are deliberately campus-level. CEA publishes the GPS point for its Cadarache centre and separately identifies WEST and its Tore Supra predecessor there. The precision note prevents those coordinates from being mistaken for surveyed device-building points. No city centroid, automatic geocoding, map click, or coordinate inference was used.

## Files

- `enrichment_round2.tsv`: exact-ID patch using the full fusion schema.
- `source_registry.tsv`: source roles, publishers, rights notes, and an explicit FusDIS exclusion record.
- `gap_report_summary.tsv`: before/after missingness for priority fields.
- `gap_report_by_country.tsv`: post-overlay raw missingness by country.
- `GAP_REPORT.md`: interpretive report, including applicability caveats.
- `generate_gap_report.py`: reproducibly merges the base, round 1, and round 2 and rebuilds reports.
- `validate_enrichment_round2.py`: validates IDs, schema, dates, coordinate policy, provenance, immutable-base checksum, effective record count, and report regeneration.

## Scope and interpretation

Raw blank counts are not always defects. `last_operation_date` should normally remain blank for operating, planned, and under-construction records, and `first_operation_date` is not applicable to unbuilt programmes. Configuration, subtype, and status were already populated for all 157 effective records before this pass.

Only factual metadata is transcribed from sources. GOV.UK material is identified under the Open Government Licence v3.0; other pages retain their publishers' copyright and are used only as cited evidence for facts. No IAEA FusDIS page or bulk dataset was accessed, scraped, or redistributed.

## Rebuild and validate

```bash
python3 generate_gap_report.py
python3 validate_enrichment_round2.py
```

The validator also confirms the base file remains at its recorded SHA-256 and does not modify any base or presentation file.

## Historical input selections

The public base retains the six attributed compilation fields and reference metadata.
Separate original Wikidata values are omitted. Complete original input is an explicit
frozen bundle; original custody hashes do not grant source redistribution.
See [the historical input contract](../README.md). Validators default to the exact
public base hash; --base-selection frozen selects the exact original base hash.
Gap counts describe the selected inputs, so public and frozen reports differ.

## Factual selection and source expression

These rows select and normalize isolated device facts with original Atlas
summaries. Source articles, reports, figures, slides and tables are not
redistributed. A source copyright notice is retained; it is not an open
licence over the source work. Government-laboratory hosting does not make
a contractor's article a federal-government work. Explicit OGL material
keeps its separate attribution and terms. The publisher compilation grant
for the historical six-field base does not license these additions or
overlays. See the [data rights map](../../../../04_interactive_presentation/data/source_rights.json)
and this directory's source registry for the precise row scope.
