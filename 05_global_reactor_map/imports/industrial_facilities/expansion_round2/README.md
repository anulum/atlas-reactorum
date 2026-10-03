<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round2/README.md
-->

# Industrial facility discovery expansion — Canada and Australia

This isolated round-two layer adds **1,776 facility-level discovery records** outside the existing EEA/EPA coverage:

- 908 Canadian facilities from the 2024 National Pollutant Release Inventory (NPRI) geolocation file.
- 868 Australian facilities whose latest National Pollutant Inventory (NPI) report is 2024/2025.

These rows identify public-register facilities and their reported industry classifications. They do **not** identify individual process vessels, reactor counts, reactor designs, production recipes or internal plant layouts. `reactor_type_if_explicit` is blank for every row because neither selected facility register publishes that field.

## Systematic selection

Canada uses the latest filed report year `2024` and these NAICS prefixes:

- `311` — food manufacturing
- `3121` — beverage manufacturing
- `322` — paper manufacturing, including chemical pulp
- `324` — petroleum and coal products
- `325` — chemical manufacturing

Australia uses latest report year `2024/2025` and these ANZSIC 2006 Division C class prefixes:

- `11` — food product manufacturing
- `12` — beverage and tobacco product manufacturing
- `15` — pulp, paper and converted paper product manufacturing
- `17` — petroleum and coal product manufacturing
- `18` — basic chemical and chemical product manufacturing
- `19` — polymer product and rubber product manufacturing

No name-based cherry-picking occurs. Source sector, class and main-activity labels are preserved. Register inclusion thresholds mean this layer is not a census of all facilities in either country.

## Files

- `industrial_facilities_round2.tsv` — 18-column import-ready layer matching the existing industrial discovery schema.
- `selected_source_snapshot.tsv` — compact, field-minimised snapshot used for deterministic offline rebuilds.
- `source_snapshot_manifest.tsv` — official raw-source URLs, retrieval date, byte counts, SHA-256 hashes and selected-row counts.
- `build_dataset.py` — live refresh and deterministic snapshot-to-output builder.
- `source_registry.tsv` — authoritative source and licence registry.
- `validate.py` — schema, provenance, coordinate, scope and reproducibility checks.
- `VALIDATION.md` — validation and coverage report.

## Snapshot and rebuild strategy

A historical rebuild reads the committed compact snapshot and writes only the
explicit output. It does not access the network or modify any historical input:

```bash
python3 build_dataset.py --output /tmp/industrial-facilities-round2.tsv
python3 validate.py --data /tmp/industrial-facilities-round2.tsv
```

`validate.py` defaults to this directory's four historical tables. Its `--data`,
`--snapshot`, `--manifest` and `--registry` options allow isolated copies. It checks
exact table schemas and row widths, the archived 1,776-record country/source
counts, provenance, coordinates and the non-inference rules. It then executes the
actual offline producer into a temporary file and compares bytes. Requested inputs
are never rewritten by validation; a failed or timed-out rebuild returns failure.
Checks also apply under Python's `-O` option. No report file is implicitly written.

A refresh requires separate snapshot, manifest and output paths:

```bash
python3 build_dataset.py --refresh \
  --snapshot /tmp/industrial-round2-refresh/snapshot.tsv \
  --manifest /tmp/industrial-round2-refresh/manifest.tsv \
  --output /tmp/industrial-round2-refresh/industrial-facilities.tsv
```

Refreshes use the current calendar date by default; `--date` permits an explicitly
dated captured source. `--canada-source` and `--australia-source` accept saved raw
CSV files. Otherwise the official registers are downloaded over verified HTTPS
with a bounded body and socket timeout. Institutional mirrors can be supplied via
`--canada-url`, `--australia-url` and a trusted `--ca-file`; the manifest's source
URLs continue to identify the upstream register. The socket timeout does not
bound the complete transfer duration. Certificate checking is never disabled.

Outputs cannot replace historical files, source inputs or the CA file. Individual
TSVs are replaced atomically; snapshot and manifest are not a multi-file
transaction. Review refreshed data and provenance as a new dated candidate. The
validator deliberately enforces the accepted 2026-09-27 snapshot, including its
fixed date and counts, so it refuses an unaccepted refreshed candidate.

The compact snapshot excludes street addresses, business registration numbers,
facility websites, full report histories and pollutant quantities. Test sources
contain all genuine selected source rows plus real year/industry exclusion
controls, with only the columns required by the importer and explicit upstream
licence/attribution records. Full raw source captures remain outside this library.

## Coordinates and status

Coordinates are copied directly from the public registers and labelled as published facility points whose positional accuracy was not independently verified. No address geocoding, city centroid, company-headquarters point or coordinate inference is used.

“Latest report” is not silently converted into “operating”. Status text says only that the latest selected report is for 2024 or 2024/2025 and explicitly leaves operating status unasserted.

## Attribution and licence

Contains information licensed under the Open Government Licence — Canada.

Australian NPI facility data © Commonwealth of Australia, Department of Climate Change, Energy, the Environment and Water, sourced 2026-09-27, licensed under Creative Commons Attribution 4.0 International. This compilation modifies the source by filtering fields and records and normalising them into a common schema.

The licences do not imply endorsement by either government.
