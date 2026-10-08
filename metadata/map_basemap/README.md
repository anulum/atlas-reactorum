# Country boundaries

The interactive facility map includes every land-boundary feature from
[Natural Earth Admin 0 land boundaries, 1:50 million](https://github.com/nvkelso/natural-earth-vector/blob/ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_50m_admin_0_boundary_lines_land.geojson),
version 5.1.0, retrieved over verified HTTPS on 2026-10-08.

The retained original has SHA-256
`2faac4f6b34386f3d21b6e018cf151f241f00e5c936d44dd17d7d9bfb147fa48`
and contains 390 features, 393 polylines and 19,859 geographic vertices.
The build preserves every coordinate and original `FEATURECLA` classification.
International boundaries are solid; disputed, indefinite, control-line and
indeterminant frontier classifications are dashed. This cartographic snapshot
is a geographic reference; it does not settle territorial disputes.

Natural Earth data is [public domain](https://www.naturalearthdata.com/about/terms-of-use/).
The original GeoJSON keeps these terms; Atlas packaging and code retain AGPL.
The layer is bundled locally and works offline without a tile server or API key.

Run `python metadata/map_basemap/build.py`, or `make build`, to reproduce
`04_interactive_presentation/data/country-boundaries.json` and `.js` from the
pinned original. A modified source fails the SHA-256 check before products
are written. Runtime admission rejects malformed coordinates; original
classification text is retained. The renderer projects each line through the
same projection and viewport as the facility points, drawing borders beneath
the points at a fixed CSS-pixel width.
