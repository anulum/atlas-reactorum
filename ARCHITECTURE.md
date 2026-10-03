<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
ATLAS REACTORUM — architecture
-->

# Architecture

Atlas Reactorum is a static evidence library with an offline interactive
front end. There is no server, no database and no runtime dependency.

## Shape

```
01_nuclear/  02_chemical_biochemical/  03_hybrid_emerging/   literature catalogues (TSV)
05_global_reactor_map/imports/                               source layers + per-round validators
metadata/                                                    audits, inventories, provenance, checksums
04_interactive_presentation/                                 the atlas itself
    scripts/build_datasets.py                                integrates every layer
    map/                                                     canvas map engine
    data/                                                    generated, never hand-edited
```

## Data flow

Source catalogues and per-round enrichment overlays are folded, in a fixed
order, into one integrated record set by `build_datasets.py`. Each source
layer has its own builder function taking explicit paths; `main()` orchestrates.
Optional layers may be absent. Required inputs for a selected layer must be
complete and valid.

Fusion defaults to the pinned IAEA FFDB catalogue. Its namespace package
decodes the complete visible-data selection and checks its artifact digest,
original-response linkage, acquisition date, all 174 TSV
rows and the complete field-provenance object before integration. Missing or
changed required inputs refuse the build before an output directory is created.
The selection keeps every typed dictionary member, source tuple and raw/display
index while excluding the rendering container. Its authored header identifies
the projection; its digest is distinct from the privately retained original.
The offline build makes no upstream request and has no implicit fallback.
`--fusion-source historical` explicitly selects the retained earlier route;
its original-source and rights limitations remain separate.

FFDB source identities retain their exact publisher name, country and
organisation. Presentation identifiers derive deterministically from those
source identities. Of 174 source rows, 137 carry publisher map coordinates
and 37 retain absent pairs. Historical overlays and supplemental coordinates
do not fill those absences. Six supplemental fusion observations remain
separate context records. Source identity and map location do not establish
physical-device identity, operating dates or current operation.

Generated outputs are written twice: as JSON, and as a JavaScript file that
assigns a global. The second exists because the atlas must load over
`file://`, where fetching a sibling JSON file is blocked.

The build is deterministic. The same sources always produce byte-identical
outputs, which is what makes `SHA256SUMS` meaningful and what catches a
refactor that changes behaviour.

## The map engine

`04_interactive_presentation/map/` — seven single-responsibility modules,
loaded as classic scripts because ES modules are blocked over `file://`.
Equal Earth is the default projection because it is equal-area: visual density
on the map is honest density on the globe. Coastline geometry is recovered by
inverting the bundled plate carrée basemap, so reprojection needs no additional
data and introduces no third-party licence. See `map/README.md`.

## Evidence model

Three things are kept in separate fields and never merged: the physical
principle, the maturity of the technology, and the strength of the evidence. A
record states what its source establishes and carries an explicit caveat about
what it does not. A site record is a publisher's row, not a verified reactor
vessel.

## Verification

`validate.sh` checks the presentation and runs the map engine's tests.
`tools/preflight.py` proves the datasets reproduce and that documented paths
exist. `browser-check.py` drives the loaded page over the DevTools protocol.
`tests/test_entry_point.py` runs each build script as a subprocess and deletes
a published artefact, because a check that never ran once read as a check that
passed.
