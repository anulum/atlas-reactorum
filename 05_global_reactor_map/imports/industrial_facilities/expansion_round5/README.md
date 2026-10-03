<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round5/README.md
-->

# Industrial facility expansion round 5 — process-specific depth

Round 5 adds a deliberately narrow, process-specific discovery layer from two official, reusable sources:

- **362 United Kingdom anaerobic-digestion planning-project records** from the July 2026 Renewable Energy Planning Database (REPD), restricted to England, Scotland and Wales.
- **31 French hydrogen-production sites** from ADEME's register of supported hydrogen production and distribution projects, restricted to rows explicitly labelled `Production`.

The accompanying `source_gap_matrix.tsv` records seven further source decisions spanning wastewater treatment, biogas, fermentation/biofuels, refining, hydrogen, gasification and ammonia. Sources that lacked a safe combination of reusable terms, source-published coordinates, facility-level modelling and deterministic access remain explicit backlog or deferred items.

This is **not a reactor or vessel inventory**. The layer does not infer vessel count, vessel design, production route, feedstock, gas output or present status. REPD's explicit source technology label is preserved as `Anaerobic digestion`, with a qualification that vessel design and count are not published. ADEME does not assign an individual production pathway to each selected row, so all French `reactor_type_if_explicit` fields are blank.

## Systematic selection

The builder applies only two exact source-field rules:

1. REPD: `Technology Type == Anaerobic Digestion` and `Country` is `England`, `Scotland` or `Wales`. All source development statuses are retained. Northern Ireland's 22 matching rows are excluded because REPD uses a different national coordinate grid for those records; the builder does not guess or mix grid systems.
2. ADEME: `site_type == Production`. Distribution-only sites are excluded. Every matching row in the retrieved API response is retained.

No record is selected by facility name, operator, location, capacity, expected process route or perceived importance.

REPD is a planning-project database rather than a deduplicated physical-facility register. Revised or successive applications can refer to the same physical site. The 362 records must therefore be interpreted as source projects/site records, not as 362 independently confirmed plants.

## Coordinates, status and capacity

REPD publishes X/Y project points. For Great Britain rows, the builder converts British National Grid coordinates to WGS84 using the inverse Transverse Mercator and approximate seven-parameter Helmert method documented by Ordnance Survey. OS limits the transformation step to 3.5 m at 95% confidence; this does not independently verify the source point. Original easting and northing values remain in the compact snapshot.

ADEME publishes latitude and longitude. Its metadata says the point is the parcel when known and otherwise the commune coordinate; it does not identify the basis for each row. No geocoding or coordinate refinement is performed.

Statuses and capacities are copied only from explicit source fields and labelled as source-published. Status is not independently verified. A project's planning status is not treated as proof of current operation. Blank capacity remains blank.

## Files

- `industrial_facilities_round5.tsv` — 18-column, import-ready discovery layer.
- `selected_source_snapshot.tsv` — field-minimised selected-source snapshot used for offline rebuilding.
- `source_snapshot_manifest.tsv` — live source URLs, retrieval date, byte counts, hashes and row counts.
- `source_gap_matrix.tsv` — process-specific source audit and evidence-backed import decisions.
- `source_registry.tsv` — data, licence, coordinate-method and backlog evidence sources.
- `build_dataset.py` — live refresh and deterministic snapshot-to-output builder.
- `validate.py` — schema, scope, provenance, stable-ID, cross-round and reproducibility checks.
- `VALIDATION.md` — recorded validation result and interpretation limits.

## Snapshot and rebuild strategy

A historical build reads the accepted compact snapshot and writes an explicit
separate output without network access or input mutation:

```bash
python3 build_dataset.py --output /tmp/industrial-facilities-round5.tsv
python3 validate.py --data /tmp/industrial-facilities-round5.tsv
```

The validator reads five complete tables and all four prior industrial layers;
missing or malformed layers fail. Options `--data`, `--snapshot`, `--manifest`,
`--registry`, `--matrix` and repeated `--other-layer` accept isolated copies.
The actual producer runs into a temporary output with a finite `--timeout`.
Failure, timeout or mismatch rejects reproducibility without rewriting inputs.
Checks also apply under Python's `-O` option.

Refresh writes separate source/provenance candidates:

```bash
python3 build_dataset.py --refresh \
  --snapshot /tmp/industrial-round5-refresh/snapshot.tsv \
  --manifest /tmp/industrial-round5-refresh/manifest.tsv \
  --output /tmp/industrial-round5-refresh/industrial-facilities.tsv
```

Saved originals use `--repd-source`, `--ademe-source` and `--ademe-metadata`.
Otherwise verified anonymous HTTPS downloads the two sources and ADEME metadata.
Trusted mirrors use `--repd-url`, `--ademe-url`, `--ademe-metadata-url` and optional
`--ca-file`; manifests continue to identify upstream origins. Body sizes and
socket timeouts are bounded; socket limits are not a whole-transfer deadline.

Refresh dates default to the current calendar date or an explicit `--date`.
ADEME's data timestamp comes from `dataUpdatedAt`, rather than the separately
edited description timestamp or a fixed historical date. Complete responses are
required: the JSON total must agree with returned rows. Provider `_id` values
can change after reimport; persistent facility keys use the documented tuple.

Historical files, source/metadata inputs and CA files are protected after
symlink resolution. Individual TSV replacements are atomic; snapshot/manifest
are not a multi-file transaction. Review refreshes as separate candidates.
The validator enforces the accepted historical date/counts until acceptance.

Portable fixtures preserve all genuine selected raw records and actual exclusion
controls, with only required fields. Their metadata records licences, source
hashes, attribution, current provider-ID differences and changes. An independent
PROJ reference contains all 362 original BNG points for coordinate regression.
Full raw captures and unused address/provider-actor fields stay outside the library.

The snapshot excludes street addresses, postcodes and unrelated source fields. It retains the minimum public identity, operator, coordinates, source classification/status, explicit capacity, project label and source row identifiers needed to reproduce and audit the layer.

UK stable IDs use the REPD reference ID: `uk-repd:<Ref ID>`. ADEME's API row `_id` is retained for traceability but is not used as a persistent key because it is service-generated. French stable IDs use the first 16 hexadecimal characters of SHA-256 over the documented tuple `site_nom|projet|station_code_commune`.

## Attribution and reuse

UK REPD data are licensed under the **Open Government Licence v3.0**. French ADEME data are licensed under the **Licence Ouverte / Open Licence 2.0**. This compilation filters, transforms and normalises those sources. Neither publisher endorses the derived layer.


## Coordinate correction on 2026-09-30

The original converter negated Helmert parameters that already represented the
OSGB36-to-WGS84 direction, applying the opposite direction a second time. This
shifted the 362 British points by approximately 140–273 m. The correction removes
that second inversion and regenerates only their latitude/longitude from the same
original published BNG points. All other project fields and all French records
remain unchanged. Every corrected point was independently checked with an explicit
PROJ pipeline using the Ordnance Survey parameters, with differences below 1 mm.
The original input/output versions are retained with internal regression evidence.
This correction does not improve or independently verify the source point itself.
