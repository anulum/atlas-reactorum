<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/enrichment/README.md
-->

# Research-reactor enrichment patch

This directory contains a small, evidence-led patch for the 172-row parent discovery layer. It does not replace the base dataset and does not modify any presentation files.

## Patch semantics

`research_reactor_enrichment.tsv` uses the parent dataset's 19-column schema and is keyed by `stable_id`. A non-empty cell in a factual field is a reviewed replacement or addition. A blank cell means **no change**; it must never erase the base value. Provenance columns describe the enrichment source, not the older base assertion.

The patch adds or improves ten exact-identity records:

- six U.S. university reactors from current U.S. NRC facility pages; and
- McMaster, Polytechnique Montréal, RMC and ZED-2 from CNSC open material, with one exact-name McMaster coordinate from the CNSC open geospatial service.

The resulting improvements are 10 statuses, 10 reactor-type descriptions, 10 thermal-power values, 10 operators, four purpose descriptions and one coordinate pair. No first-criticality or shutdown date is added because the reviewed regulator pages generally publish operating-licence/start-of-operation dates, which are not silently re-labelled as first criticality.

## Identity and precision rules

Rows were added only when the base name unambiguously identifies the same physical reactor as the official record. Campus, city and site records were not treated as reactor units. McMaster is the sole coordinate addition because the CNSC geospatial service contains an exact named `McMaster Nuclear Reactor` feature. Its precision text says explicitly that it is a facility point, not a surveyed core location.

`operational` is used only where a current regulator registry lists the facility as operating, or for ZED-2 where the CNSC report and 2026 operator evidence agree on active use. Licensed power is treated as thermal only because the regulator sources explicitly describe research-reactor power levels in thermal units. Exact unit conversions are documented per row.

## Rights and exclusions

U.S. NRC web material is a U.S. Government work and is not subject to copyright. Government of Canada/CNSC material used here is under the Open Government Licence - Canada 2.0. Retain attribution to both agencies when redistributing the patch.

Canadian Nuclear Laboratories material was used only to corroborate ZED-2 identity, design and continued activity; its prose was not copied and it is not presented as openly licensed. The IAEA Research Reactor Database was not scraped, queried in bulk, copied or redistributed because an unambiguous open bulk-redistribution licence was not found.

## Validation

From this directory:

```bash
python3 validate_enrichment.py
```

The validator checks the exact schema, base-key membership, unique patch keys, controlled statuses, coordinates, numbers, dates, HTTPS provenance, allowed licences and the rule that every patch changes at least one factual field relative to the base row.
