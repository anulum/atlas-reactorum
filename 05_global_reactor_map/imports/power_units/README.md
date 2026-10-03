<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/power_units/README.md
-->

# Open power-reactor unit layer

This layer contains **1,823 fission or unspecified-type power-reactor unit records** in 62 countries/areas and 590 named plants/projects. It is derived from the August 2026 Global Energy Monitor (GEM) Global Nuclear Power Tracker map export. The two source records explicitly labelled `fusion` are excluded because fusion devices are represented in a separate atlas layer.

The source snapshot is pinned by SHA-256 in `scripts/build_from_gem.py`. Rebuild and validate with:

```bash
python3 scripts/build_from_gem.py --source source_data/gnpt_map_2026-08.geojson --out power_reactor_units.tsv --date 2026-09-27
python3 scripts/validate.py power_reactor_units.tsv
```

## Interpretation limits

- GEM calls its capacity field unit **nameplate capacity**. It is preserved as `nameplate_mw`; it is not relabelled as net or gross electrical power.
- The map export does not provide construction, criticality, grid-connection, commercial-operation, permanent-shutdown or thermal-power fields. Those columns remain blank.
- `operating`, `construction`, `announced`, `cancelled` and other statuses are GEM tracker classifications as of the source release, not a live regulator feed.
- One physical site may have many unit records. The older WRI layer remains as a separate plant-level discovery layer and is not silently merged with these units.
- Consequential facts should be checked with the responsible regulator and operator.

## Attribution

Adapted from **Global Nuclear Power Tracker, Global Energy Monitor, August 2026 release**, under CC BY 4.0. The adaptation filters two fusion-labelled proposals, maps fields, preserves source links, and adds explicit caveats. See `source_registry.tsv`.
