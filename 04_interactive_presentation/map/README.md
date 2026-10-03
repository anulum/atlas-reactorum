<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 04_interactive_presentation/map/README.md
-->

# Atlas Reactorum — canvas map engine

Zero-dependency canvas renderer for the facility layer. Replaces the former
SVG point layer, which emitted one `<circle>` per record and could not survive
the full dataset.

## Why it was replaced

The SVG layer had four defects that scaled with the data:

| Defect | Consequence |
| --- | --- |
| One DOM node per record | 12,813 nodes rebuilt on every filter change |
| `filter: drop-shadow` per circle | Dense regions rendered as opaque black mass |
| No zoom, pan or aggregation | Density answered by shrinking dots to 1.6 px |
| `tabindex` forced to `-1` above 500 rows | Keyboard access vanished at full dataset size |

Plate carrée was also hardcoded inline, so high-latitude area was badly
distorted on a map whose subject is *where things are*.

## Modules

Each file has one responsibility and loads as a classic script. ES modules are
deliberately avoided: they are blocked over `file://`, and the atlas must run
offline from disk with no server.

| Module | Responsibility |
| --- | --- |
| `projection.js` | Plate carrée and Equal Earth, forward and inverse |
| `coastline.js` | Recovers geographic rings from the bundled SVG basemap |
| `quadtree.js` | Spatial index for viewport culling and hit testing |
| `cluster.js` | Screen-space density aggregation and glyph sizing |
| `viewport.js` | Zoom, pan, clamping and world/screen transforms |
| `renderer.js` | Canvas painting of ocean, graticule, land and clusters |
| `engine.js` | Orchestration, interaction, accessibility |

Load order matters; `engine.js` must come last.

## Design decisions

**Equal Earth is the default projection.** It is equal-area, so visual density
on the map is honest density on the globe. A facility map drawn on a
non-equal-area projection overstates concentration at high latitudes. The
easting denominator is derived as the exact derivative of the northing
polynomial rather than restated as a separate constant, and
`tests/projection.test.js` verifies the equal-area property numerically by
checking that the Jacobian determinant equals `cos(lat)` across the graticule.

**No new basemap data.** The bundled SVG basemap is authored in a plate carrée
viewBox, which is exactly invertible, so true longitude and latitude are
recovered from the geometry already in the repository. This keeps the atlas
free of an additional third-party data licence.

**Clusters are filled by majority and ringed by rarity.** Colouring purely by
rarity turned the entire map orange, because 2,192 fission records are spread
widely enough that almost every cluster contains one. Colouring purely by
majority hid the sparse fusion records. A cluster therefore reports its majority
domain as fill — honest proportion — and its rarest domain as an accent ring,
so a single fusion device inside four hundred chemical sites still announces
itself.

**Glyph area, not radius, encodes count.** Area-proportional encoding is what a
reader judges correctly. Radius is capped below half the cluster cell, because
glyphs wider than their cell overlap and render adjacent counts as one
unreadable number.

**Records without usable coordinates are dropped, never coerced.** A record
with a missing coordinate would land at 0°N 0°E — a location in the Gulf of
Guinea that no source ever supplied.

## Accessibility

A canvas is opaque to assistive technology, so the engine maintains a parallel
visually hidden list of real focusable buttons alongside it, plus an
`aria-live` region announcing the focused record. The canvas itself keeps
`tabindex="0"` at every dataset size and supports arrow-key panning,
`+`/`-` zoom, `0` to reset and `Enter` to open the focused record.

## Tests

```bash
cd 04_interactive_presentation/map && node --test tests/*.test.js
```

85 tests. They run against the real shipped dataset and the real basemap path
rather than fixtures, and check behaviour rather than implementation: quadtree
range and nearest queries are verified against brute force, clustering is
verified to conserve every record, and the renderer is checked against a
recording context for draw ordering and balanced canvas state.
