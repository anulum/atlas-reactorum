<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round4/README.md
-->

# Industrial facility expansion round 4 — global source-gap audit and Switzerland import

Round 4 has two outputs:

1. An evidence-backed matrix covering Japan, New Zealand, Switzerland, South Korea, India, Brazil, and South Africa.
2. A legally reusable **93-record SwissPRTR discovery layer**, the only reviewed source that satisfied the complete import test in this round.

The import identifies public-register facilities and preserves their source classifications. It does **not** identify individual vessels, reactor counts, reactor designs, production recipes, capacity, or present operating state. `reactor_type_if_explicit` and `capacity` are blank in every output row.

## Import decision test

A source is imported only when all of the following are established from official evidence:

- facility-level records with stable public identifiers;
- source-published coordinates, not address geocoding or headquarters points;
- source process/industry fields supporting systematic chemical, biochemical, food, paper, petroleum, pharmaceutical, or polymer selection;
- explicit reusable terms suitable for republication;
- a reproducible bulk download or API route.

Public visibility alone is not treated as an open licence. A map marker alone is not treated as a bulk coordinate field. Internal reporting requirements are not treated as published data.

## Jurisdiction audit result

See `jurisdiction_source_matrix.tsv` for field-by-field evidence. In summary:

- **Switzerland — import:** the official SwissPRTR workbook has facility IDs, owners, NACE/PRTRO classifications, and CH1903+/LV95 facility points. The official open-data catalogue assigns attribution-required open use.
- **Japan — backlog:** extensive annual facility files and a public map exist, but explicit reusable terms and bulk source-coordinate fields were not established.
- **New Zealand — backlog:** the current national location dashboard is for waste facilities, not a chemical/biochemical production register; no qualifying national PRTR source was found.
- **South Korea — backlog:** public PRTR facility/industry results exist, but no licensed, coordinate-bearing national bulk extract was established.
- **India — backlog:** OCMMS provides facility consent searches and industry types, while OCEMS covers monitored sectors; the reviewed routes lack the required combination of open reuse terms, source coordinates, and stable bulk access.
- **Brazil — backlog:** a national RETP was still an active regulatory proposal in 2026, not an operational released dataset.
- **South Africa — backlog:** SAAELIP/NAEIS collects facility GPS and process information internally, but no explicitly open, stable national facility export was established.

“Backlog” means the jurisdiction should be reassessed when the missing condition changes; it is not a claim that no relevant administrative data exist.

## Swiss systematic selection

The refresh reads all 22,860 data rows in the official 2007–2024 workbook, selects reporting year `2024`, restricts to source type `Punktquelle` (point source), and retains unique facilities whose NACE code begins with:

- `10` — food products: 14 facilities
- `11` — beverages: 1 facility
- `17` — paper and paper products: 4 facilities
- `19` — coke and refined petroleum: 1 facility
- `20` — chemicals and chemical products: 37 facilities
- `21` — pharmaceuticals: 34 facilities
- `22` — rubber and plastic products: 2 facilities

No facility name, owner, canton, pollutant, or presumed technology affects selection. Repeated pollutant/waste rows are collapsed only when the facility identity, owner, coordinates, NACE, industrial sector, and PRTRO activity fields agree. The official workbook warns that its 2023 and 2024 publication is not yet complete for some facilities, so this is not a complete industrial census.

## Coordinates

SwissPRTR publishes each selected point as CH1903+/LV95 north/east coordinates. The builder converts those published values to WGS84 using swisstopo’s official December 2016 approximate direct-transformation formula. Swisstopo states precision better than 0.12 arcseconds longitude and 0.08 arcseconds latitude throughout Switzerland. This is a coordinate-system transformation, not geocoding or location inference; the original LV95 values remain in the compact snapshot.

## Files and rebuild

- `jurisdiction_source_matrix.tsv` — seven-country gap audit and import decisions.
- `industrial_facilities_round4.tsv` — import-ready 18-column Swiss layer.
- `selected_source_snapshot.tsv` — field-minimised snapshot for deterministic offline builds.
- `source_snapshot_manifest.tsv` — raw URL, retrieval/reporting dates, byte count, row counts, and SHA-256.
- `source_registry.tsv` — import provenance, licence, coordinate-method, and audit evidence sources.
- `build_dataset.py` — live refresh and offline builder.
- `validate.py` — schema, audit coverage, stable-ID, scope, coordinate, and reproducibility checks.
- `VALIDATION.md` — recorded validation result and limits.

Offline rebuild and validation require only Python 3. The output must be explicit
and separate from the historical files:

```bash
python3 build_dataset.py --output /tmp/industrial-facilities-round4.tsv
python3 validate.py --data /tmp/industrial-facilities-round4.tsv
```

Validation reads the five tables without rewriting them. It requires the complete
base, round-two and round-three layers for stable-ID checks; missing or malformed
prior layers fail. Its `--data`, `--snapshot`, `--manifest`, `--registry`, `--matrix`
and repeated `--other-layer` options accept isolated copies. The actual producer
runs into a temporary output with a finite `--timeout`; failure, timeout or byte
mismatch rejects reproducibility. Checks also apply under Python's `-O` option.

A refresh additionally requires `openpyxl` and separate candidate paths:

```bash
python3 build_dataset.py --refresh \
  --snapshot /tmp/industrial-round4-refresh/snapshot.tsv \
  --manifest /tmp/industrial-round4-refresh/manifest.tsv \
  --output /tmp/industrial-round4-refresh/industrial-facilities.tsv
```

`--raw-source` accepts a saved original XLSX. Otherwise the official workbook is
downloaded over certificate-verified anonymous HTTPS; `--source-url` and a trusted
`--ca-file` permit a mirror. Manifest URLs still identify the upstream register.
The response body and expanded workbook content are bounded. Socket timeouts are
not a whole-transfer deadline. The workbook reader closes even when parsing fails.

Refresh dates default to the current calendar date; `--date` accepts a dated
capture. Outputs cannot replace historical files, inputs or the CA file, including
through resolved symlinks. Individual TSV writes are atomic; the snapshot and
manifest are not a multi-file transaction. Refreshed data must be reviewed as a
new candidate. The validator intentionally enforces the accepted historical date,
counts and jurisdiction decisions until a separate candidate is accepted.

The genuine field-minimised test workbook retains all 466 qualifying source rows,
including repeated facilities, the three translated headers and real exclusion
controls for year, source type and NACE. All 93 resulting facility records match
the historical snapshot. SOURCE.json records attribution, terms, hashes and the
reserialization changes; full raw workbook captures remain outside the library.

The compact snapshot excludes addresses, postcodes, business registry identifiers, pollutant names and quantities, waste quantities, employee data, and all other fields unnecessary for facility discovery.

## Attribution and reuse

Contains data from the Federal Office for the Environment FOEN, “Swiss Pollutant Release and Transfer Register (SwissPRTR),” sourced 2026-09-28 from the official dataset URL, under the opendata.swiss condition **Open use; source attribution required** (`terms_by`).

The compilation filters and normalises source fields and transforms the published LV95 coordinates using an official swisstopo formula. Neither FOEN, opendata.swiss, nor swisstopo endorses this derived layer.
