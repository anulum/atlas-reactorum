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
Comparison changes must preserve stable identities, ordering, complete-profile
snapshot hashes, original claims/source locators and explicit rights. Run the
dedicated `tests/taxonomy_comparison.test.cjs` native contract suite and
`tests/test_taxonomy_comparison_browser.py` real navigation/download cases.
Malformed or stale shared states must refuse visibly; new input values must not
be inferred or numerically merged across incompatible declared contexts.

Learning paths must name an explicit goal and question, bind their answer to an
unchanged original claim and keep the same profiles, citations, rights and
missing values in both reading depths. Run `tests/learning_paths.test.cjs` and
`tests/test_learning_paths_browser.py` against the complete actual presentation.
Version links bind both data and authored learning content; stale versions must
refuse. Native keyboard, mobile, assessment and file-download checks do not
substitute for a human comprehension study.

make lint includes make native-test-docs, which requires native contracts
on the complete research integration, dataset-integrity and native browser
test files, including the shared Chrome fixtures and protocol decoders. This
check runs without the general test-method docstring exemptions. Owned browser
fixtures wait for the exact page URL after startup and navigation; a DevTools
HTTP response or navigation acknowledgement alone does not establish that the
intended page is committed. Ambiguous and unsafe targets still refuse.

The locked development environment and native Node, Chrome, Poppler
`pdftotext` and shell tools are required; see [Validation](VALIDATION.md) for commands and current scope.

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
/absolute/external/workspace` to rebuild all 22 release products in a newly
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

Use `make build VENV=/absolute/development/environment` and
`make test VENV=/absolute/development/environment` to carry the selected Python
into child processes, including taxonomy validation. Preflight
passes its own interpreter to the taxonomy child. Keep explicit `ATLAS_PYTHON`
selection/refusal and the real configured-environment regressions in
`tests/test_release_rebuild.py`; packages on an unrelated ambient PATH must not
be required by a selected development environment.

The `.nojekyll` file is an empty presence marker. Its attribution is recorded
in `REUSE.toml`; it has no text to format.

## Evidence corrections

Use the history workspace in the taxonomy section to inspect an exact original
revision, then supply proposed wording, an anonymous HTTPS source, a page or
section locator, a reason and your contributor name. The form prepares a local
pending-proposal download. Provide that unchanged JSON to a curator with your
contribution; the form does not submit it. Keep the original proposal alongside
any decision so its hash and source-bound original revision remain reviewable.

Follow the [curator commands](metadata/evidence_history/README.md) to record an
explicit `accepted-for-editing` or `rejected` decision with the review source,
locator, reviewer and date. These are recorded identities, not authenticated
signatures. Acceptance authorises consideration of a source edit; it applies no
data changes. A curator must separately review and edit the original catalogue
inputs, regenerate the evidence profiles, explicitly import the successor into
a new journal file, retain the old journal, and rebuild all generated products.
Imports validate complete original profiles and preserve prior snapshots.

Run the dedicated native history, correction, renderer and CLI suites in
`validate.sh`, and `tests/test_evidence_history_browser.py` against the actual
page. Preserve exact linked revisions, disabled exports on refusal, pending
proposal custody and real native controller coverage. Date fields retain their
own meanings; unknown source publication or event dates remain unknown.

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
For an immutable public historical replay, use `--fusion-source historical
--historical-bundle /absolute/public-snapshot`. The builder verifies all nine
source and registry files before creating outputs and records their hashes.
Run `tests/test_historical_fusion_build.py` and the historical input/round-2/
round-3 owning suites; preserve source bytes when writing reports separately.

The browser tests load the full real presentation in an isolated native Chrome
profile over loopback. The normal sandbox is the default. On a host explicitly
configured for trusted local assets without that sandbox, use
`ATLAS_BROWSER_NO_SANDBOX=1 .venv/bin/python -m pytest tests/test_browser_checks.py`.
This option changes only the test fixture's browser launch; all checks remain
active. Keep the two browser modes distinct in verification records.

## Before you refactor a builder

Checksum the generated datasets first, and compare after. Two separate defects
were caught only by that guard; nothing else would have found them.

## Research imports

Preserve the original browser comparison contract when adding research consumers.
The reader must validate the whole original source snapshot and refuse changed
claims, sources, rights, order or compatibility results. Run
`tests/test_research_comparison.py` for the actual Python API/CLI and Chrome
download path, and `tests/research_comparison.test.cjs` for the original native
contract. Execute the real `examples/research/comparison.ipynb` with Jupyter;
retain execution evidence outside public source. Do not replace expected hashes
with hashes computed from an untrusted import or promote metadata compatibility
to a scientific result.
