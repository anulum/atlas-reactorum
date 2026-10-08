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
| `interactions.js` | Pointer gestures, wheel zoom and keyboard dispatch |
| `accessibility.js` | Source-row button list, remaining count and live announcements |
| `engine.js` | Projection, index, viewport and raster orchestration |

Load order matters; `engine.js` must come last.

The projection API carries JSDoc contracts for both loading modes. `forward`
accepts longitude and latitude in degrees and returns plane coordinates;
`inverse` returns geographic degrees. `get` rejects an unregistered identifier,
and `list` returns the two registered projections. `bounds` samples the world
in degree increments, using one degree when the step is omitted or zero. These
contracts preserve the existing coordinate formulas and lookup behavior.

The quadtree carries the input point's payload type through insertion, range
queries and nearest-point lookup. A query can append to a caller-owned result
array; child insertion requires a subdivided node. Viewport construction starts
at unity when the configured zoom interval permits it and clamps that initial
value to the nearest limit otherwise. World/screen conversion, pan and zoom
use the same viewport state; world-edge clamping can move an edge zoom anchor.

The renderer accepts the canvas operations it actually uses, so the same
painters work with a real 2D canvas and the call-recording test adapter.
Unregistered domain names, including JavaScript prototype property names,
use the unknown-domain colour. Graticule spacing is measured in degrees:
omitted, null and zero spacing retain the 30-degree default. Nonnumeric,
nonfinite, negative and non-advancing steps refuse before any canvas state
changes; they cannot trap the drawing loops.

The engine retains the original row's type and object identity through
projection, spatial lookup, focus and selection. Coordinate input accepts
numbers or nonblank numeric strings within longitude ±180° and latitude ±90°;
booleans, arrays, objects, missing values and blank strings remain unmapped.
Clicking an aggregate glyph zooms into it before considering individual records.
Pointer movement beyond four CSS pixels remains a drag even if it returns to
its starting point. The release click is consumed; a fresh deliberate click
works normally. Cancelled gestures also suppress compatibility clicks.
Changing projection rebuilds focus against the current index; filtering out the
focused row clears it, so Enter cannot select a removed record. Construction
requires a container and either an explicit document or the container's owner
document. Both browser and Node consume the same eight dependency modules.
The engine delegates interaction and accessibility through those shared owners;
selection callbacks still receive the original point and source row. An absent
canvas context leaves drawing inert while the accessible controls remain usable.

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
visually hidden list of up to 200 real focusable record buttons alongside it.
An explicit remaining-count note asks readers to narrow the filters. An
`aria-live` region announcing the focused record. The canvas itself keeps
`tabindex="0"` at every dataset size and supports arrow-key panning,
`+`/`-` zoom, `0` to reset and `Enter` to open the focused record.

## Tests

```bash
cd 04_interactive_presentation/map && node --test tests/*.test.js
```

The tests exercise the shipped dataset and basemap, analytic coordinate cases
and the production map modules: quadtree
range and nearest queries are verified against brute force, clustering is
verified to conserve every record, and the renderer is checked against a
recording context for draw ordering and balanced canvas state.

Run `make native-map-runtime` for complete source-bound qualification. Its
dedicated Node cases use genuine DOM Windows and a Cairo canvas; Chrome loads
the complete maintained page and dispatches native pointer input. All nine
map sources must retain their current bytes and execute every observed native
function and region across those two runtimes. These V8 execution regions are
reported separately from Node's line/branch/function coverage. The recording
adapters in the retained original tests do not satisfy this runtime gate.

The native cases recover the actual SVG coastline, reproject all mapped
facility rows, retain their identities through index queries and verify density
counts. Canvas defaults produce identical PNG bytes, and invalid graticule
spacing refuses without changing the raster. Actual missing module, document,
canvas capability and source-coordinate cases exercise refusal boundaries.
