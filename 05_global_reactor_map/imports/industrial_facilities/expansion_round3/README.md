<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round3/README.md
-->

# Industrial facility discovery expansion — United Kingdom

This isolated round-three layer adds **722 United Kingdom facility-level discovery records** from the official 2024 UK Pollutant Release and Transfer Register (UK PRTR). The existing base and round-two import layers contain no United Kingdom rows, so this is new country coverage rather than a replacement of those layers.

These records identify publicly reported facilities and preserve their source industry/activity classifications. They do **not** identify individual process vessels, reactor counts, reactor designs, production recipes, internal plant layouts, capacity, or present operating state. `reactor_type_if_explicit` and `capacity` are blank for every row.

## Systematic selection

The builder reads every one of the 5,802 facility rows in the official 2024 CSV and retains rows whose source `FacilityReport_NACEMainEconomicActivityCode` starts with one of these NACE divisions:

- `10` — manufacture of food products: 338 records
- `11` — manufacture of beverages: 52 records
- `17` — manufacture of paper and paper products: 36 records
- `19` — manufacture of coke and refined petroleum products: 18 records
- `20` — manufacture of chemicals and chemical products: 225 records
- `21` — manufacture of basic pharmaceutical products and pharmaceutical preparations: 39 records
- `22` — manufacture of rubber and plastic products: 14 records

No names, operators, locations, pollutant values, or expected technologies are used for selection. Source NACE labels and UK PRTR Annex I activity codes are retained. Register thresholds and the main-economic-activity filter mean this is a representative discovery layer, not a census of all relevant industrial facilities.

## Files

- `industrial_facilities_round3.tsv` — 18-column import-ready discovery layer matching the existing industrial schema.
- `selected_source_snapshot.tsv` — compact, field-minimised snapshot for deterministic offline rebuilds.
- `source_snapshot_manifest.tsv` — official raw URL, reporting/retrieval dates, byte count, raw/selected row counts, and SHA-256.
- `build_dataset.py` — live refresh and deterministic snapshot-to-output builder.
- `source_registry.tsv` — authoritative data, licence, and licence-evidence registry.
- `validate.py` — schema, provenance, coordinate, scope, stable-ID, cross-round, and reproducibility checks.
- `VALIDATION.md` — validation and coverage report.

## Snapshot and rebuild strategy

A historical build reads the committed compact snapshot and writes an explicit
output without modifying its inputs or accessing the network:

```bash
python3 build_dataset.py --output /tmp/industrial-facilities-round3.tsv
python3 validate.py --data /tmp/industrial-facilities-round3.tsv
```

The validator defaults to the four historical tables in this directory. Its
`--data`, `--snapshot`, `--manifest` and `--registry` options accept isolated
copies. It runs the actual producer into a temporary output and compares bytes;
a failed or timed-out rebuild returns failure without rewriting requested inputs.
Checks apply under Python's `-O` option too. The base and round-two layers must
also be readable, correctly shaped and free of duplicate or overlapping IDs;
missing prior layers are failures. `--other-layer` accepts explicit prior-layer
copies, and `--timeout` controls the native rebuild deadline.

A refresh requires separate snapshot, manifest and output paths:

```bash
python3 build_dataset.py --refresh \
  --snapshot /tmp/industrial-round3-refresh/snapshot.tsv \
  --manifest /tmp/industrial-round3-refresh/manifest.tsv \
  --output /tmp/industrial-round3-refresh/industrial-facilities.tsv
```

Refreshes use the current calendar date by default; `--date` permits an explicitly
dated captured source. `--raw-source` accepts a saved original CSV. Otherwise the
official annual CSV is downloaded over certificate-verified HTTPS with a bounded
body and socket timeout. A trusted mirror may be supplied with `--source-url` and
`--ca-file`; the manifest continues to identify the upstream source. The socket
timeout does not bound the complete transfer duration.

Outputs cannot replace historical files, source inputs or the CA file, including
through resolved symlinks. Individual TSVs are replaced atomically; snapshot and
manifest are not a multi-file transaction. Review refreshed data and provenance
as a new dated candidate. The validator enforces the accepted 2026-09-28 snapshot,
its 2024 reporting year and 722 records, so it refuses an unaccepted refresh.

The field-minimised test CSV retains all 722 actual selected source rows and one
genuine excluded-industry control. `tests/data/industrial_round3/SOURCE.json`
records source and fixture hashes, source-specific licence evidence, attribution
and the changes made. Full raw source captures remain outside the library.
The source's previous-national-ID reporting-year field is not the current
reporting year; 2024 comes from the authoritative annual source file.

The refresh applies only the seven documented NACE-prefix rules. The compact snapshot omits street address, postcode, employee count, operation hours, waste transfers, pollutant names and quantities, and all other fields unnecessary for facility discovery. It retains the public facility ID/name, operator, published point, reporting year, main NACE code/label, and Annex I activity code.

Stable IDs have the form `uk-prtr:<FacilityReport_NationalID>`. The validator checks uniqueness within this layer and disjointness from the current base and round-two stable-ID sets. It does not attempt fuzzy entity matching across jurisdictions.

## Coordinates and status

Latitude and longitude are copied directly from the UK PRTR CSV. No address geocoding, company-headquarters points, centroids, or inferred coordinates are used. Each output row labels the coordinate as a UK PRTR-published facility point whose positional accuracy has not been independently verified.

The reporting year is not converted into an operating claim. Every status states only that the facility was reported in UK PRTR for 2024 and explicitly says that operating status is not asserted.

## Attribution and licence

Contains public sector information from the Department for Environment, Food & Rural Affairs, sourced 2026-09-28, licensed under the Open Government Licence v3.0.

The UK PRTR implementation report specifically describes reuse of UK PRTR information under the OGL with Defra acknowledged as the source. This compilation modifies the source by filtering records and fields and normalising them into a common schema. The licence does not imply government endorsement.

## Country-source decision

The round prioritised the UK, New Zealand, and Japan. The UK PRTR was selected because the current official release combines reusable licence evidence, stable public facility IDs, source-published coordinates, and relevant source activity labels in a reproducible national file. No New Zealand or Japan records were added merely to increase country count: a comparably clear national source satisfying all of those requirements was not established during this round. This avoids geocoding, inferred facilities, and uncertain reuse rights.
