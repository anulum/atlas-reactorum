<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round7/README.md
-->

# Industrial round 7 source bundle

These tools preserve complete Swiss SFOE biogas and Italian ARPAE bioenergy
source observations. A facility observation does not establish a reactor
vessel count, reactor design or current operation.

The native source readers require the complete five-member Swiss CSV archive
and the complete Italian layer/count/ID/feature capture. The selector retains
153 Swiss plants and 268 Italian biogas-classified records from 330 Italian
features. Annual Swiss production rows remain separate source relations.

The offline builder accepts the exact 28-column contract declared in
`contracts.SNAPSHOT_FIELDS` and produces all 18 consumer fields declared in
`contracts.FIELDS`. It preserves original capacities, including zero;
operator whitespace and dash sentinels; reference dates; classification text;
and publisher notes. Swiss CHP capacity remains in kW without an inferred
electrical/thermal split. Italian fuel labels remain source classifications.
The reactor-design field remains empty.

`bundle.py` creates a complete portable source bundle from already captured
resources. It checks the original exact-resource grants and receipts before
writing the snapshot, discovery table, source registry, capture inventory,
rights notes and both manifests into a new external directory. Original HTML,
catalogue text and model media stay outside the bundle.

```sh
python /path/to/expansion_round7/bundle.py \
  --capture-directory /path/to/complete/original/custody \
  --output-directory /existing/external/directory/new-bundle

python /path/to/expansion_round7/validate.py \
  --directory /existing/external/directory/new-bundle \
  --capture-directory /path/to/complete/original/custody

python /path/to/expansion_round7/bundle.py \
  --frozen-directory /existing/external/directory/new-bundle \
  --output-directory /existing/external/directory/reproduced-bundle
```

Bundle validation checks every artifact byte, licence annotation, reviewed
source count, original receipt URL/hash/date and snapshot date binding.
Supplying `--capture-directory` additionally compares against complete original
raw custody. Without it, validation verifies the frozen bindings and does not
reacquire raw sources. An edited snapshot and newly calculated hashes are not
proof of original source parity; original-custody verification rejects such a
self-consistent edit. Frozen bundle reproduction performs no network requests.

Run the public scripts from any working directory using their absolute paths:

```sh
python /path/to/expansion_round7/build_dataset.py \
  --snapshot /path/to/selected_source_snapshot.tsv \
  --output /existing/external/directory/industrial_facilities_round7.tsv

python /path/to/expansion_round7/validate.py \
  --snapshot /path/to/selected_source_snapshot.tsv \
  --dataset /existing/external/directory/industrial_facilities_round7.tsv
```

The builder performs no network requests. The output must be a new file under
an existing directory outside the repository, with no symlink ancestors. It
refuses existing files and source aliases, then publishes complete bytes
atomically. Rerun into another new destination to compare reproducible bytes.

The read-only validator compares every consumer cell, record count and order
with the complete source projection. It also refuses stable-ID collisions
with the six earlier canonical industrial layers. It never rewrites its inputs.
This comparison does not independently reacquire raw sources or adjudicate
source rights. Those checks use the exact-resource custody interface in
`capture.py`; its native CLI requires `--directory`.

Production acquisition uses verified anonymous HTTPS, bounded reads and no
redirect following. It only creates a previously absent external custody
directory. Full terms-page HTML and source-model media are not public fixtures.
Dataset reuse terms remain source-specific: Swiss
`LicenseRef-opendata-swiss-terms-by` and Italian `CC-BY-4.0`.

Canonical tests use complete real publisher inputs and real TLS connections.
They include actual direct publisher acquisition and consequently require
upstream availability. `ATLAS_INDUSTRIAL7_CAPTURE_DIR` can select preserved
complete custody for session preparation; it does not disable the direct
publisher acquisition test.

## Bundle versions and provenance migration

New capture conversion writes bundle version 2. Its generated rights report
includes hidden repository provenance; the inventory binds those exact bytes.
Version 1 retains the original report and inventory and remains fully
verifiable. Ordinary `--frozen-directory` reproduction preserves its input
version and every artifact byte.

Request a version-one migration explicitly into a new external directory:

```sh
python /path/to/expansion_round7/bundle.py \
  --frozen-directory /existing/external/directory/version-one-bundle \
  --upgrade-provenance \
  --output-directory /existing/external/directory/version-two-bundle
```

The migration changes only the generated rights report and bundle inventory.
It preserves the original snapshot, source/grant manifest, discovery table,
source registry and capture inventory byte-for-byte. Source and grant schema
versions remain unchanged. Validation reconstructs every artifact under the
declared version; changing only a version number or recalculating an altered
report's digest cannot satisfy that complete binding.

## Map integration

The complete seven-artifact frozen bundle in this directory contributes all
421 observations to the offline presentation. From the repository root run:

```sh
python 04_interactive_presentation/scripts/build_datasets.py
```

The consumer validates every bundle member before creating any map, company
or inventory export. All seven input hashes are recorded in
`04_interactive_presentation/data/dataset-inventory.json`. A checkout without
any bundle artifacts can build the earlier layers; presence of even one member
requires the complete valid bundle. This rule also applies under Python `-O`.
The Python JSON and JavaScript assets carry the same complete records.
