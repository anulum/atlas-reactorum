<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/fusion/enrichment/README.md
-->

# Fusion facility enrichment

This directory is a non-destructive overlay for `../fusion_facilities.tsv`. It does not rewrite the 146-row base dataset or any presentation/current file.

## Files

- `enrichment.tsv` supplies reviewed field values for existing `stable_id` keys. Blank cells mean “no override”.
- `new_facilities.tsv` contains genuinely absent devices supported by primary laboratory, government-laboratory or operator sources.
- `source_registry.tsv` records source roles, retrieval dates and reuse treatment.
- `validate_enrichment.py` checks schemas, keys, URLs, dates, coordinates, duplicate names and the immutable base SHA-256.
- `VALIDATION_REPORT.md` records the audit result and deliberate limitations.

Both data files use the base fusion schema so they can be reviewed and merged mechanically. Overlay application should replace a base field only when the matching enrichment cell is non-empty. New rows should be appended only after downstream review.

## Audit method and scope

The 146 base records were audited for empty coordinate pairs, unknown status, unknown country and obvious omissions against primary institutional histories and current programme pages. The audit found 132 base records without coordinates and one record (`fusionbenchmark:fuze`) with unknown status.

No coordinate was added. Primary sources generally identify a laboratory, city or campus but do not publish a machine-point latitude/longitude. Geocoding an address or copying a headquarters/campus centroid would create an inferred point, so those cells remain empty. This is a deliberate quality result, not an omission concealed by the pipeline.

The enrichment resolves the FuZE status as last explicitly confirmed by its operator, adds countries and operating dates to selected historical base records, and refines two current construction/commissioning records from primary programme updates. A status with a qualifier is retained verbatim rather than collapsed into a false present-tense claim.

## New-record selection

`new_facilities.tsv` is a documented first enrichment tranche, not a claim of complete historical coverage:

- LM26 is included because General Fusion explicitly states that the named physical machine is built, commissioned and operating, with first plasma in February 2025.
- The four IPP historical devices come from the laboratory's systematic inventory of important former tokamaks and stellarators.
- Model C, ATC, PDX and PBX-M are named physical PPPL experiments in the national laboratory's own history.
- Tore Supra is retained as a historical operating phase with an explicit note that the hardware was transformed into the existing WEST device; it is not a second current machine.
- ZETA is included as a documented named physical UKAEA experiment, with its first operating date from the agency's historical publication.

Concept-only power-plant studies without a secured device identity or site were not added merely because they appear in old surveys. Company headquarters are never used as device locations. No site coordinate is inferred from a city, address, campus or organization headquarters.

## Provenance and reuse

Rows reproduce concise factual metadata, not expressive text, imagery or diagrams. Source copyright remains with each publisher. Each row carries its primary source URL and a note explaining exactly what was verified. Government and national-laboratory pages are treated as authoritative factual evidence; the compilation does not imply endorsement by the source organizations.

## Validate

From this directory:

```bash
python3 validate_enrichment.py
```

The validator checks the exact selected base hash. The default public selection and explicit original frozen selection have distinct pinned hashes in the historical input manifest.

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
