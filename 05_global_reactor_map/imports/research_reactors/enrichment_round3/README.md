<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/enrichment_round3/README.md
-->

# Research-reactor enrichment, round 3

This directory is a third standalone overlay for the 172-row research-reactor discovery table. It targets high-impact gaps in countries not covered by rounds 1 and 2 and does not modify the base dataset or presentation.

## Contents and scope

`research_reactor_enrichment_round3.tsv` uses the base dataset's 19-column schema and is keyed by `stable_id`. Non-empty factual cells are reviewed additions or replacements. Empty cells mean **no change** and must never erase a base value.

The ten rows cover Belgium, Brazil, Finland, Ghana, Jordan, the Netherlands, Nigeria, Slovenia, South Africa and Switzerland. They provide ten status overlays, six detailed reactor types, six thermal-power values, nine operator overlays, ten purpose descriptions, four first-criticality dates and one shutdown date. No coordinates are added.

No `new_facilities.tsv` is included. This round was deliberately restricted to exact stable-ID matches already present in the base.

## Evidence rules

- Identity must be exact by reactor name or an unambiguous acronym/expanded-name pair.
- Only regulator, government commission, public nuclear institute or primary operator sources are used.
- A commissioning, inauguration, service-entry or elapsed anniversary statement is not transformed into first criticality.
- Date precision is retained exactly as published.
- Power is thermal only where the source explicitly identifies reactor or fission power. W and kW conversions to MW are exact and documented.
- `operational` requires a current source describing the reactor as operating, in use, or performing contemporary activities.
- No campus, organisation or site centroid is used as a reactor coordinate.

## Reuse and rights

The Dutch regulator applies CC0 1.0 to website text unless a specific copyright notice is shown; none is shown on the HOR page. The remainder of the overlay is an original selection and normalisation of isolated factual assertions from pages that reserve copyright or do not provide an unambiguous open licence. `source_registry.tsv` preserves these distinctions and does not claim to relicense source expression. No prose, images, tables or substantial database portions are copied.

The IAEA Research Reactor Database was not scraped, bulk queried, copied or redistributed because no unambiguous open bulk-redistribution licence was found.

## Validation

Run from this directory:

```bash
python3 validate_enrichment_round3.py
```

The validator checks schema, unique base-key membership, controlled statuses, coordinates, numeric power, date syntax and calendar validity, HTTPS provenance, rights declarations, exact source-registry coverage, and that every row changes at least one factual field.
