<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
ATLAS REACTORUM — contributing
-->

# Contributing

## Gates

Every change must pass all of these before it lands. A gate that cannot run is
a failure, not a pass.

```bash
make lint typecheck
make test
make validate preflight
```

`make test` enumerates every production Python source directory, including
standalone importers and validators. Measuring only the two central generators
would omit acquisition, provenance, browser and repository tools. Focused
verification selects the dedicated tests and the complete owning source scope;
it does not replace the complete repository gate. Coverage is 100 per cent,
statement and branch, without excluded entry points or a lowered threshold.
The locked development environment and native Node, Chrome and shell tools
are required; see [Validation](VALIDATION.md) for commands and current scope.

`validate.sh` also runs the native taxonomy citation, exporter and detail
serializer tests at 100 per cent line, branch and function coverage. The
[citation contract](metadata/taxonomy_audit/README.md) requires all current
catalogue identities and bound values to match before products are rewritten.
Bound text fields require nonempty single-line strings, and bound source URLs
require a nonempty array of anonymous HTTPS links. Principle, strength and
challenge citations must match the complete current wording and link a source
present in the entry's references. Source-copy
provenance distinguishes a known publisher retrieval from a retained original
whose retrieval date is unknown; an inspection date must not fill that gap.

Preflight requires Python, Node and the shell inventory tools used by `make
build`. Run `python tools/preflight.py --check reproducibility --workspace
/absolute/external/workspace` to rebuild all 18 release products in a newly
owned temporary tree. The workspace must already exist outside the candidate;
the default is the operating system temporary directory. `--timeout` bounds
each builder (1,800 seconds by default). `--root` selects another complete
candidate. Accepted files remain intact on success and failure.

Documentation checks cover all public Markdown, including import READMEs,
relative links with fragments and URL-encoded paths. Header checks require the
seven-line branding header on Python, shell and CommonJS scripts. Environments,
caches and private records are pruned before traversal; owned symlinks and
unreadable source trees fail rather than escaping the candidate boundary.

## Rules that are not negotiable

1. **Sources are verbatim.** Never edit a source value to satisfy a check.
   Schema field names such as `organization` and `normalized_status` are the
   published data contract and are not re-spelled; prose is British English.
2. **Absence stays absence.** A missing coordinate is not zero; a missing
   capacity is not 0 MW; a missing status is `unknown`, never blank.
3. **No inference.** Reactor type, vessel count, fuel cycle, capacity and
   status come from the source or not at all.
4. **Guards raise, never assert.** `python -O` strips assertions.
5. **No fake tests.** Tests run against the real catalogues and the real
   basemap. Synthetic rows are built from the production column set read out of
   the real sources, so a schema change breaks the tests rather than letting
   them pass against a shape the builder no longer accepts.
6. **Split by responsibility.** A function that assembles several source layers
   is several functions.

## Preserving source bytes

Stage the intended files explicitly, then run `make hooks`. Review and stage
any formatter changes to owned code or documentation before committing.
Its formatting hooks
leave TSV, JSON, NDJSON, CSV, GeoJSON, FFDB frame files and generated
presentation data intact. The read-only conflict, credential and size checks
still inspect these files, and source validators still require their recorded
hashes. EditorConfig leaves their encoding, line endings and final-newline
choice to the existing file; do not run an editor formatter on captured data.
Regenerate derived products through their owning builder after a reviewed
source change, then rebuild the inventory and checksums.

The `.nojekyll` file is an empty presence marker. Its attribution is recorded
in `REUSE.toml`; it has no text to format.

## Adding a data layer

A new bulk source needs, before any record is merged: publisher, licence,
retrieval date, selection rule, coordinate semantics, status semantics, and an
explicit statement of what its records do *not* establish. Where redistribution
is restricted, a catalogue-only record is the correct outcome.

Each layer ships its own builder, source registry, rights note and validator,
and its own coverage delta. The default fusion layer is the pinned
[IAEA FFDB catalogue](05_global_reactor_map/imports/fusion/ffdb/README.md).
Its complete visible-data selection, manifest, TSV and field provenance must agree
before the map builder creates outputs. Missing or altered required FFDB
inputs fail; they never select the historical import implicitly. Historical
selection is explicit and does not establish its acquisition or publication
rights.

The browser tests load the full real presentation in an isolated native Chrome
profile over loopback. The normal sandbox is the default. On a host explicitly
configured for trusted local assets without that sandbox, use
`ATLAS_BROWSER_NO_SANDBOX=1 .venv/bin/python -m pytest tests/test_browser_checks.py`.
This option changes only the test fixture's browser launch; all checks remain
active. Keep the two browser modes distinct in verification records.

## Before you refactor a builder

Checksum the generated datasets first, and compare after. Two separate defects
were caught only by that guard; nothing else would have found them.
