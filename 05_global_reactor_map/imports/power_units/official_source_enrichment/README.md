<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — power unit documentary projection
-->

# Power unit documentary projection

This offline revision covers every originally blank operator or reactor-class cell in the frozen GEM August 2026 unit layer: **930 decisions across 783 of its 1,823 units**. There are **54 qualified fills** (41 operator, 13 reactor class), **35 held candidates** and **841 bounded unknowns**. All pre-existing scalar values, source ordering, identities, capacities, owners, coordinates and tracker stages remain preserved. The original TSV and GEM export are unchanged.

A qualified value retains an explicit documentary role: actual or historical operator, intended or designated future operator, licensed project organisation, historical design or proposed design. An owner, applicant, vendor, contractor or national programme organisation is not automatically an operator. Planned and licensed projects do not establish physical electricity generation. Known inconsistent model/class pairs are retained as source cells rather than silently repaired.

Held and unknown decisions leave the original field blank. Unknown means no qualified support in the reviewed sources for this revision; it does not claim absence elsewhere. Author review is completed. Independent review remains **null**, and neither software admission nor a source institution's name constitutes independent scientific acceptance or endorsement.

## Reproduce and verify

From the repository root:

```bash
python3 05_global_reactor_map/imports/power_units/official_source_enrichment/build_power_projection.py 05_global_reactor_map/imports/power_units/power_reactor_units.tsv 05_global_reactor_map/imports/power_units/official_source_enrichment
python3 05_global_reactor_map/imports/power_units/official_source_enrichment/build_power_projection.py 05_global_reactor_map/imports/power_units/power_reactor_units.tsv 05_global_reactor_map/imports/power_units/official_source_enrichment --check
python3 04_interactive_presentation/scripts/build_datasets.py
```

`primary-sources.json` holds 179 referenced custody entries: 33 qualified documents, 129 context-only documents and 17 capture-attempt records. `primary-fields.json` records the complete field decisions and source-scope observations. `primary-projection.json` binds both inputs and the original TSV by SHA-256 and retains every projected row and decision. Its release consumer reconstructs the whole product before use and refuses changed, duplicate, linked, partial or unreproducible inputs. Entirely absent bundles preserve historical builds; partially present bundles refuse them.

The original baseline SHA-256 is `42d46f0426f47886aba872a3711c242dc2c32b3b0f4b535d727d151ed1b77f3b`. Documentary dates retain year, month, day, month-range or unknown precision and their stated basis. Capture timestamps are separate UTC custody metadata. Complete native PDF, HTML, facsimile and spreadsheet documents can support a selection only with explicit qualification; failed requests and non-documents remain separate capture attempts.

Python `power_contract.py`, `power_projection.py` and `power_bundle.py` own offline admission. Browser and Node `power-source-contract.js` and `power-field-contract.js` admit the same original cells and refusals. The actual facility builder resolves citation metadata for standalone downloads; map details show role, documentary scope, date meaning, held candidates and failed captures. Facility schema **1.4.0** adds `power_field_decisions`. JSON retains complete records; CSV adds `reactor_type`, `model`, `source_status` and a JSON-encoded `power_field_decisions` cell.

## Rights

Only citation and independently worded factual metadata are distributed here. Original publisher documents, imagery and spreadsheets are not embedded or relicensed by this bundle. A successful HTTP capture is not redistribution permission. The unchanged GEM source/adapted rows retain their CC BY 4.0 attribution; Atlas code and editorial metadata retain the repository licence. See the adjacent `.license` sidecars and the parent [source attribution](../README.md#attribution).
