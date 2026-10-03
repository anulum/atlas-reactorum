<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/fusion/enrichment_round3/README.md
-->

# Fusion facility enrichment round 3

Date: 2026-09-28

This is a self-contained, non-destructive exact-ID overlay for the effective 157-record fusion layer. It integrates the immutable 146-row base, the round-1 overlay and 11 round-1 additions, then round 2 before measuring and applying round 3. It does not alter any integrated catalog or presentation file.

Round 3 focuses on official operator, institution, and government sources. It adds or refines device milestones for LHD, JT-60U, FTU, SMART, ADITYA-U, T-15MD, DIII-D, OMEGA, TCV, Z, ATC, PLT, ST, and MAST. Exact precision is preserved: year- or month-only values remain year- or month-only when a source does not publish a day.

No additional official numeric site coordinate passed the required evidence threshold. Postal addresses, map pins, city centroids, and third-party geocoding were not converted into coordinates. The sole remaining organization gap, T-3, is also left unknown because reviewed official material did not state an exact operating relationship clearly enough.

Files:

- `enrichment_round3.tsv`: 14 exact-ID overlay rows using the full fusion schema.
- `source_registry.tsv`: source roles, rights notes, retrieval dates, and explicit FusDIS exclusion.
- `gap_report_summary.tsv` and `gap_report_by_country.tsv`: deterministic coverage reports.
- `GAP_REPORT.md`: human-readable findings and applicability caveats.
- `generate_gap_report.py`: merges the layers and rebuilds reports.
- `validate_enrichment_round3.py`: validates schema, exact IDs, provenance, dates, no-coordinate policy, immutable base checksum, coverage totals, and report regeneration.

Only factual metadata is transcribed. GOV.UK material is covered by the Open Government Licence v3.0 where noted; other sources retain their stated copyright. IAEA FusDIS was not accessed, scraped, or redistributed.

Run:

```bash
python3 generate_gap_report.py
python3 validate_enrichment_round3.py
```

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
