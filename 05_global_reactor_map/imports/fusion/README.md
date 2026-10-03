<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/fusion/README.md
-->

# Historical fusion compilation and offline inputs

The default atlas build uses the separately attributed [IAEA FFDB selection](ffdb/README.md).
This directory provides an explicit historical selection of 146 FusionBenchmark
records. FusionBenchmark / Hadamard LLC's dated publisher permission describes
the compilation, classifications and provenance annotations under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The public selection retains six original importer-normalised fields:
name, country, configuration, device_subtype, status and organization.
All 876 nonempty values and the original 146 reference identities are preserved.
Source URLs, roles and retrieval dates are attributed original-import references
and acquisition metadata. They do not license the linked works or establish
current status or independent physical accuracy.

Separate original Wikidata aliases, coordinates and operation dates are absent
from this public table, together with their coordinate-precision notes. The
18-column schema retains empty slots so exact-ID overlay consumers remain
compatible. This is field selection, not reconstruction of unavailable raw pages.
The [rights description](source_rights.json) records attribution, normalisation,
evidence limits and source-specific conditions.

Three enrichment passes and eleven primary-source additions remain distinct
layers. The FusionBenchmark grant does not license those sources. Their
registries, dated claims and source terms must be consulted separately.

## Build the public historical selection

From the repository root:

```bash
python 04_interactive_presentation/scripts/build_datasets.py --fusion-source historical
```

This option uses the selected source root and preserves the existing partial-tree
build API. It does not grant rights to caller-supplied replacement data. To verify
and snapshot all nine checked-in public input hashes, sizes, schemas and row
counts, use historical_inputs.py with --selection public. The complete original
route below always performs that verification and captures an owned snapshot
before dataset export. Neither route downloads or automatically selects a source.

The selected public base has no coordinates or operation dates; subsequent
attributed overlays supply their own values. Reports therefore describe this
selection's actual gaps. Both historical selections retain 146 base identities,
11 additions and all three overlay passes.

## Reproduce complete original historical inputs

The complete original 146-row/18-column table and its original registries and
overlays are external inputs. They are not distributed as the public table.
The [input manifest](frozen_input_manifest.json) declares all nine original
hashes, schemas, row counts and byte sizes. The original base SHA-256 is
5ad43c86982c9aa0514c5bb0e6c7ece2b5f5e35a064ac2282899bba003bd7c16.

Supply a directory with exactly those relative input paths using lawful access
and the sources' usage conditions. File possession, a checksum or a licence
declaration does not itself grant redistribution. The source payload remains
separate from any generated presentation.

To create a verified owned copy:

```bash
python 05_global_reactor_map/imports/fusion/historical_inputs.py \
  --source-root /path/to/complete-inputs \
  --destination /path/to/new-owned-snapshot --selection frozen
```

To build a separate complete historical presentation, first place the retained
supplemental context file in its output directory:

```bash
mkdir -p /path/to/historical-output
cp 04_interactive_presentation/data/facilities-supplemental.json /path/to/historical-output/
python 04_interactive_presentation/scripts/build_datasets.py \
  --fusion-source historical-full --historical-bundle /path/to/complete-inputs \
  --data-dir /path/to/historical-output
```

The full option requires the explicit bundle and verifies all nine original
inputs before export. It cannot fall back to the public subset, download data or
use changed original values. Dataset input hashes disclose the actual selection;
generated facility records preserve the original fields and overlays. The
checked-in default presentation continues to use FFDB and contains no historical
146-row payload.

## Native validation and gap reports

Base validation accepts an explicit dataset and report path:

```bash
python 05_global_reactor_map/imports/fusion/validate_fusion_facilities.py \
  --dataset /path/to/owned-inputs/fusion_facilities.tsv --report /path/to/report.md
```

Round-one validation accepts explicit base, enrichment, additions and registry
paths. Its default base selection is public; use --base-selection frozen only
with the exact original base hash. Round-two and round-three validators accept
--fusion-root, --base-selection and an optional --report-root so reporting can
leave immutable source inputs untouched:

```bash
python 05_global_reactor_map/imports/fusion/enrichment_round2/validate_enrichment_round2.py \
  --fusion-root /path/to/owned-inputs --base-selection frozen \
  --report-root /path/to/round2-reports
python 05_global_reactor_map/imports/fusion/enrichment_round3/validate_enrichment_round3.py \
  --fusion-root /path/to/owned-inputs --base-selection frozen \
  --report-root /path/to/round3-reports
```

Both gap-report generators accept the same explicit input root and separate report
directory. Counts are computed from selected inputs, without substituting
historical coverage numbers for the public subset.

## Acquisition boundary

The former live acquisition command now refuses every URL before opening it.
The original collector is retained in protected historical custody. It is not a
current collection grant. Refresh through new permitted sources requires distinct
source evidence and does not overwrite historical acquisition claims.
