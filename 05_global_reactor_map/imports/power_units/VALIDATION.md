<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/power_units/VALIDATION.md
-->

# Validation report

Validated 2026-09-27 with `scripts/validate.py`.

- Result: passed
- Records: 1,823
- Countries/areas: 62
- Plants/projects: 590
- Coordinates: 1,823
- Statuses: 424 operating; 85 construction; 136 pre-construction; 327 announced; 63 shelved; 23 mothballed; 230 retired; 535 cancelled
- Blank source reactor type: 193
- Blank unit designator: 100 (plant name is used as the display fallback)
- Source GeoJSON SHA-256: `d85e489c2eed4cc67c9c2b2dec8548b00d0d591ac693cd56fd3388616c1c7c1f`

All stable IDs are unique and schema-safe, coordinates are in range, source URLs are HTTPS, source/role counts match, status values are controlled, and the fission layer contains no source record explicitly labelled `fusion`.
