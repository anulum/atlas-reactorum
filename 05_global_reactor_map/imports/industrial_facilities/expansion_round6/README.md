<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round6/README.md
-->

# Industrial facility expansion round 6 — Brazil biofuels and U.S. landfill gas

Round 6 adds **1,131 official, reusable source records** that materially deepen South American biofuel coverage and U.S. landfill-gas process coverage:

- 431 records from Brazil's EPE ethanol-plant layer;
- 88 records from Brazil's EPE biodiesel-plant layer;
- 70 records from Brazil's EPE biomethane-plant layer; and
- 542 operational landfill-gas energy project records from U.S. EPA LMOP.

These are source plant/project records, not a count of reactor vessels or necessarily a count of unique physical sites. Every `reactor_type_if_explicit` field is blank. Explicit plant classifications and energy-use technologies are retained in `process_or_activity`, where they cannot be mistaken for reactor designs.

## Import test

A source was imported only when this round established:

- an official public publisher and facility/project-level source;
- explicit redistribution terms;
- source-published coordinates rather than geocoding or headquarters locations;
- process, product or technology fields usable without inferring internal equipment; and
- deterministic bulk access suitable for a compact offline snapshot.

See `source_gap_matrix.tsv` for the complete decision record and `RIGHTS.md` for the redistribution evidence and attribution language. Deferred and backlog entries are not approved imports.

## Systematic selection

The EPE import retains **every row** in the three official ArcGIS plant layers. It does not filter by name, status, capacity, feedstock or apparent importance. This deliberately preserves source distinctions such as operating, construction and expansion rows at the same location instead of merging them into an inferred facility. The ethanol layer also contains source types labelled `Açúcar` and `Aguardente`; those exact types remain visible and are not silently relabelled as ethanol-fermentation plants.

The LMOP import retains **every row** in EPA's operational-project feature layer. The 542-row count matches EPA's published September 2024 total. The layer is voluntary and not exhaustive. It represents operational landfill-gas energy projects, not all landfills and not a claim that each project has an anaerobic-digestion vessel.

## Preserved assertions and non-inference boundary

The layer preserves only explicit source fields:

- EPE plant-layer classification, plant type, source status/authorization, published capacity and biomethane feedstock;
- LMOP project category, energy-use technology, project parties, start date, published MW or landfill-gas flow; and
- publisher-supplied latitude and longitude.

It does not infer fermentation, anaerobic-digester design, biomethane upgrading technology, biodiesel reaction technology, reactor count, vessel type, capacity where blank, current status beyond the source label, or a more precise coordinate.

EPA states that LMOP coordinates are the best available but are not intended to be exactly precise; they may represent a landfill centre or entrance. EPE does not state survey accuracy for the plant points. All output precision and status fields carry these limits.

## Stable IDs and duplicate semantics

The upstream ArcGIS layers do not publish a durable, globally scoped plant/project identifier for every row. Each snapshot therefore retains the source `OBJECTID` as `source_row_id` and creates a deterministic 16-character SHA-256 key from the source name, `OBJECTID`, and selected identity fields. Output IDs use these namespaces:

- `br-epe-ethanol:<hash>`
- `br-epe-biodiesel:<hash>`
- `br-epe-biomethane:<hash>`
- `us-epa-lmop:<hash>`

This is stable for the committed snapshot and deterministic rebuild. A future live refresh can legitimately change an ID if the publisher republishes a layer with new object IDs. The builder never uses business registration numbers in output IDs, and the compact snapshot excludes them.

Multiple source rows can refer to the same physical location, especially separate operating and expansion records. They are retained as distinct source assertions. No fuzzy entity merge is performed.

## Files and rebuild

- `industrial_facilities_round6.tsv` — import-ready 18-column discovery layer.
- `selected_source_snapshot.tsv` — field-minimised, 17-column selected-source snapshot.
- `source_snapshot_manifest.tsv` — exact live query URLs, retrieval date, byte counts, hashes and row counts.
- `source_gap_matrix.tsv` — imported, deferred and backlog source decisions.
- `source_registry.tsv` — official data, rights and interpretation evidence.
- `RIGHTS.md` — licence and redistribution analysis.
- `build_dataset.py` — live refresh and deterministic offline builder.
- `validate.py` — schema, counts, rights, scope, coordinates, stable IDs, cross-round and reproducibility checks.
- `VALIDATION.md` — recorded validation result and limitations.

Normal rebuilds are offline and require an explicit separate output:

```bash
python3 build_dataset.py --output /tmp/atlas-round6-offline.tsv
python3 validate.py
```

Validation reads the accepted tables and all five preceding industrial layers.
It reproduces the dataset into a temporary output and never rebuilds in place.
Missing or malformed preceding layers fail instead of being skipped. Optional
`--data`, `--snapshot`, `--manifest`, `--registry`, `--matrix`, `--rights`
and repeated `--other-layer` select explicit validation inputs; `--timeout`
sets a finite positive native rebuild deadline.

A deliberate refresh queries all four official layers and their independent
count endpoints, then writes an isolated candidate:

```bash
python3 build_dataset.py --refresh \
  --snapshot /tmp/atlas-round6-refresh/selected_source_snapshot.tsv \
  --manifest /tmp/atlas-round6-refresh/source_snapshot_manifest.tsv \
  --output /tmp/atlas-round6-refresh/industrial_facilities_round6.tsv
```

Refresh uses today's calendar date by default; `--date YYYY-MM-DD` records an
explicit capture date. It refuses historical destinations and paths resolving
to any requested input, manifest, raw source, count response or CA file. Every
source is parsed and validated before writing. Individual TSV replacement is
atomic, but the snapshot/manifest/output set is not one multi-file transaction.
The historical validator checks the accepted 2026-09-28 counts and date;
changed live candidates require a separate source review before acceptance.

For offline source replay, add `--raw-dir /path/to/captured-responses`. This
directory must contain each source's `SOURCE.json` and `SOURCE-count.json`,
where SOURCE is `br-epe-ethanol`, `br-epe-biodiesel`, `br-epe-biomethane` or
`us-epa-lmop`. The count file is the actual independent ArcGIS JSON response,
not an invented count derived from a truncated feature body. All four source
files and four count responses are required. The refresh manifest records
canonical upstream URLs and hashes of the actual source bytes read.

Repeated `--source-url SOURCE=HTTPS_QUERY_URL` supports explicitly trusted
anonymous HTTPS mirrors; `--ca-file PATH` permits their trusted CA. The count
request keeps the query selection and uses `returnCountOnly=true`. Requests
verify certificates and bound response bytes, redirects and socket operations.
A socket timeout is not a whole-download deadline. No transport bypass is used.

A source response must have WGS84 EPSG4326 geometry, unique positive OBJECTIDs,
finite published points, finite numeric capacities and exactly the independent
count. A true transfer-limit flag or incomplete result refuses before writing;
this builder does not automatically page a growing layer. Acquire a complete
response across all pages before offline replay if a source exceeds its service
limit. Published attributes and service geometry must agree within one millionth
of a degree to accommodate decimal rounding; the published point is retained.
This is a consistency check, not a claim of survey accuracy. Blank/nonpositive
capacity stays blank, and no internal process/vessel inference is introduced.

The scripts require only Python 3's standard library.

## Attribution

Brazilian records contain data from Empresa de Pesquisa Energética (EPE), WEBMAP EPE biofuel plant layers, retrieved 2026-09-28, licensed under CC BY 4.0 and modified by field selection and schema normalisation.

U.S. records contain data from the U.S. EPA Landfill Methane Outreach Program, operational landfill-gas energy project map, September 2024 data release, retrieved 2026-09-28, published under CC0 1.0 / U.S. EPA public-use terms and modified by field selection and schema normalisation.

Neither publisher endorses this derived layer.
