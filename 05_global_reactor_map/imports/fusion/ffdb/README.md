<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — IAEA FFDB source import
-->

# IAEA FFDB source import

This layer reproduces the complete visible IAEA Fusion Facility Database
snapshot captured on 2 October 2026: 174 catalogue records, of which 137 have
a publisher map location. It uses pinned local source bytes and never downloads
or refreshes data during a build.

The presentation builder selects this layer by default. It decodes
`visible_data.frames` from this directory and requires both cached products
to match that capture before writing map outputs. The inventory records all
four input digests. Production builds do not depend on test fixture files.

```bash
python 05_global_reactor_map/imports/fusion/ffdb/build_from_ffdb.py
python 05_global_reactor_map/imports/fusion/ffdb/build_from_ffdb.py --output /existing/parent/new-directory
```

The first command validates the registered source. The second writes
`fusion_facilities.tsv` and `field_provenance.json` into a new directory.
Existing output directories are refused. Both normal Python and `python -O`
retain the same input guards.

Facility identifiers encode the exact facility name, country and organisation
with the `iaea-ffdb:` prefix. Rendering tuple positions are view-local source
references, not persistent device identifiers. A change in a publisher identity
creates a different source-specific identifier.

The presentation's `id` is the `iaea-ffdb:` prefix followed by the SHA-256 of
the exact source `stable_id`. This preserves safe URL/DOM identifiers while
retaining the full publisher identity in `stable_id` and field provenance.
Source IDs are not matched to historical FusionBenchmark IDs by name alone.

```bash
python 04_interactive_presentation/scripts/build_datasets.py
python 04_interactive_presentation/scripts/build_datasets.py --fusion-source historical
```

The second command selects the attributed six-field historical compilation and its
separate overlays. The complete original route is --fusion-source historical-full
with an explicit --historical-bundle; all nine frozen input hashes and schemas must
pass. See the [historical input contract](../README.md).
There is no automatic fallback when a pinned FFDB input is missing or changed.
Historical overlay values and supplemental coordinates do not fill FFDB fields.
The original supplemental records remain separate context observations.

The table retains the source configuration, type, design, ownership and status
as supplied. Missing map locations and operation dates stay absent.
Map coordinates retain their decoded numeric precision; their displayed aliases
are separately stored in field provenance. A publisher map location does not
establish physical-device granularity or survey-grade accuracy.

These are dated discovery records, not an independent scientific review or a
reconstruction of the historical 146-record FusionBenchmark import. Source
classification groups are not silently converted into scientific confinement
categories. Older devices, subsequent generations and company designs require
their own identity and field evidence.

See [RIGHTS.md](RIGHTS.md) for the source-specific permission and attribution
boundary. The version-two source registry records distinct artifact and original-response
SHA-256 values, the original size and the acquisition date;
every derived record retains raw source cells and their display aliases.

## Visible-data selection

The 37,968-byte framed artifact is an authored data projection, not an unchanged
publisher response. Its first frame explicitly declares
`atlas-ffdb-visible-data-selection-v1`, the publisher URL, acquisition date and
original-response digest. Its second frame retains all typed dictionary members
and the complete Table/Main tuple, raw-value and display-alias indices. Rendering
configuration, software and credentials are excluded. The full original response
and permission-page HTML are preserved outside the public source tree.

`selection.select_visible_data(payload, retrieved_date)` selects directly from
the original response. It validates both views before projecting them and does
not reconstruct cells from the derived TSV. Selecting an existing projection
keeps its original digest and date and reproduces identical artifact bytes.

The pinned original-response digest is
`a87305137acebaaa3acf4dee2992324061c9d0e3eed433f1abe3cf49e1f9d037`;
the selected-artifact digest is
`640bae831a78d72503f6de9c7107c7c3b511cf117f83d2fe39a778d6cf045d06`.
Field provenance records both. Presentation records expose the artifact digest
in `ffdb_source_sha256`, retain `ffdb_original_response_sha256`, and identify
the selection in `ffdb_source_kind`. Digests bind bytes; they do not supply
independent source-rights or scientific approval.
