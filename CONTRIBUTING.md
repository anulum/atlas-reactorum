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
Keep authored fallback display rows separate from source-bound catalogue
entries; a missing identity or provenance must not be filled during a code
refactor. Panel changes must retain every original explanation, diagram and
source-link representation. Run the complete native presentation-component
cohort and its actual Chrome controls, and preserve the real normal/optimised
data-consumer integration cases when changing application wiring.
Page navigation binds the actual maintained document, controls and direct main
sections through `page-navigation.js`. Its handled keyboard keys cancel native
page scrolling after section movement is selected; focused inputs, selects and
textareas retain ordinary editing. Run `tests/test_page_navigation_browser.py`
with native Chrome for desktop/mobile movement, dialog dismissal and unavailable
targets. The ordinary `make test` discovers this cohort and requires execution
of every complete source-exact native controller region and function. Keep its
raw CDP evidence distinct from Node line/branch/function measurements.
Bind learning controls through the required HTML tag and namespace reader.
`application-data.js` admits the original wrapped or legacy arrays before the
application consumes their text, coordinate, reference and observation cells.
Other producer fields remain unknown and unchanged. Shape admission does not
certify source claims: original source/profile validators remain authoritative.
Run `tests/application_data.test.cjs` at the complete owning coverage floor and
`tests/test_application_data_browser.py` for real missing-source and malformed
input cases. An authored fallback never acquires a source identity or evidence
profile; the complete-application CLI refuses that incomplete source state.
Repeated controls retain their actual HTML tag/namespace through the native
reader, including empty filtered views. Map selections use admitted original
rows, and the engine owns its canvas keyboard controls; retired SVG circle
handlers do not represent a current point layer.
Keep version cells and FormData answers unknown until native admission, and
refuse authored answers outside their retained original examples. The native
cases use complete source-validated profiles; browser cases cover missing
answers and damaged actual controls alongside the original journeys.

`make lint` includes `make native-test-docs`, which requires native contracts
throughout the complete maintained test tree, including fixtures, shared
Chrome support and protocol decoders. Ruff also enforces these contracts
through the normal hooks and repository lint entry point. A new test file or
method cannot bypass documentation checks through a filename exemption.
Document the actual behaviour, invariant and assumptions being checked.

`make lint` also runs ShellCheck 0.9.0 and shfmt 3.8.0 through
`make native-shell`. Shell formatting uses four spaces, as declared by
EditorConfig. `make validate` runs `make native-javascript` with Node 24.21.0
before the presentation checks. Both native targets enumerate tracked and
new, unignored source through Git, including files in new directories;
missing files, symlink sources, absent tools and mismatched tool versions fail.
JavaScript syntax checks complement the dedicated semantic and browser suites.
The `native-shell` pre-commit hook runs that same complete shell gate. The
`native-python-types` hook runs strict MyPy discovery over every maintained
Python source, test, fixture and stub directory, including new roots.

Run `npm ci` with Node24.21.0 and npm11.19.0 to install the immutable native
JavaScript development graph. `make lint` includes ESLint10.12.0,
JSDoc65.1.0 and Prettier3.9.9; `make typecheck` includes TypeScript6.0.3
with `allowJs`, `checkJs`, `strict` and declaration checking. The same
commands run from the installed pre-commit hooks and hosted correctness CI.
Tracked and new JS, CJS and MJS files enter native discovery, including new
directories. Missing source, symlink source, unavailable tools and changed tool
versions refuse rather than becoming a pass.

Six literal presentation wrappers remain owned by their source-bound
generators: repository catalogue, retained evidence history, facilities,
companies, taxonomy audit and evidence profiles. Their output bytes are
checked by Node syntax, source/schema consumers and offline reproduction.
They are not handwritten modules for TypeScript inference or formatter writes.
The retained `taxonomy-expanded.js` editorial input contains executable
construction code and remains in lint, strict types and formatting.
Its authored tuples use `taxonomy-construction.js` in both browser and native
readers. Keep all original output objects and member order when changing code.
The taxonomy and citation byte pins must follow validated source changes;
code-only changes still require full row/source equality and owning migration.
Retain prior history snapshots and append an actual Atlas observation for the
new complete profile version. Generate current examples through the native
exporter and retain their explicit version hashes; an old version cannot become
an implicit alias for current data. Run the whole constructor/exporter coverage
cohort and actual five-producer reproduction before accepting these changes.
The exclusions name the six products individually; a new handwritten file
under `data/` still enters the native checks.

`make dependency-audit` audits both complete dependency locks through
`pip-audit --require-hashes` and `npm audit --include=dev`. Correctness CI
requires the audit job to succeed at every push and pull request; registry
errors and every advisory severity fail. Do not suppress failure, omit
development packages or raise a severity threshold. The dedicated audit-policy
test pins the actual Make commands and their blocking workflow wiring.

Owned browser fixtures wait for the exact page URL after startup and navigation; a DevTools
HTTP response or navigation acknowledgement alone does not establish that the
intended page is committed. Ambiguous and unsafe targets still refuse.

The locked development environment and native Node, Chrome, Poppler
`pdftotext` and shell tools are required; see [Validation](VALIDATION.md) for commands and current scope.

`make native-web` checks every tracked and new HTML/CSS source, including new
roots. HTML-validate uses its recommended semantic/accessibility rules with
the same void-element and doctype style as Prettier. Keep labelled landmarks
unique, use native sections for named regions, and declare button/input types.
The CSS Tree parser refuses recovery and checks property/at-rule grammar.
Every declared custom-property alternative, alias and fallback is resolved
before native value matching; missing dependencies, cycles and expansions
above 64 alternatives refuse. All conditional alternatives must satisfy each
consuming property's grammar. Formatting preserves the original cascade.
Run the dedicated CSS source cohort at its 100 per cent line/branch/function
floor and the public web-gate candidate tests. Missing tools/source fail.

`make native-languages` refuses source and compiled backend formats whose
complete native lane has not been enrolled. It runs before owning checks and
on every commit; adding a Rust, Go, C/C++, HDL, generated foreign interface or
native binary cannot inherit a Python/JavaScript success. Source suffixes use
the exact lowercase spelling of their owning discovery pathspecs.
TypeScript declarations enter the existing native lint/compiler/format graph
through `*.d.ts`, with documentation required for declared aliases, interfaces,
members and functions. TypeScript implementation is a separate unqualified
lane. Any new native lane needs its complete contracts, native tooling,
runtime coverage, parity and blocking CI before first implementation.
Unknown source formats and unregistered extensionless names also refuse;
an unlisted language cannot inherit another lane's success. The gate lists
the current non-code asset suffixes and named metadata files explicitly.
That role routing does not certify their contents, sources or rights.

Python type discovery uses actual tracked/new `*.py` and `*.pyi` paths and
refuses missing or linked source. Separate native passes keep source/stub
counterparts and duplicate standalone basenames checked without false packages.
`make native-python-stubs` additionally requires a real `.py` counterpart and
the exact interface generated by mypy 2.3.1 `stubgen --no-import --parse-only
--include-private`, formatted by locked Ruff and prefixed by its source's
seven-line header. `stubtest` checks actual runtime symbols/signatures after
that declaration comparison. It alone cannot establish return annotation
correctness. Runtime implementation retains full documentation and tests;
generated `.pyi` files supply types rather than duplicating docstrings.

`make native-ffi` runs native Ruff over direct Python FFI imports. The existing
libc inotify test observer has one exact complete-source binding; any changed
byte or another FFI file needs fresh qualification.
The complete approved observer is byte-bound before exemption from the import
ban; every other discovered Python source must return zero native Ruff findings.
FFI controls preserve the actual gate sources and their hashes beside raw V8
receipts before candidate cleanup. Resolve native source URLs to their actual
filesystem paths, and keep runtime-refusal measurements distinct from approval
of that runtime or backend.
Native imports/loading in JavaScript are blocked by the ordinary linter until
their role is qualified.
These static checks do not prove arbitrary dynamic library behavior. Native
runtime/interface tests, exact source review and all applicable domain gates
remain required for a new backend; code coverage is not physical validation.

`make native-notebooks` checks every current/new notebook with the locked
native schema, Ruff notebook lint/format and nbQA strict mypy. Only ordinary
Python cells are currently qualified; kernel magics, skipped/empty cells and
other notebook languages need their own complete qualification before use.
`make native-notebook-runtime` additionally executes every unchanged cell
through the actual Jupyter CLI in a fresh kernel. Temporary source, kernel,
configuration and runtime files belong to the caller's working-disk workspace;
accepted notebooks are not overwritten.
The admission report retains the original native stdout as `execution_stdout`,
alongside the complete source digest and executed-cell count. Use
`tests/test_notebook_tools.py` for public CLI/Make source, tool, new-root,
type/format/contract and genuine kernel refusal controls; the dedicated
admission cohort also checks native stderr/display outputs and text encodings.
The research notebook uses public
object readers to keep container values unknown until their shape is admitted.
Those readers preserve original fields and values; the source-linked public
comparison reader retains scientific/source/rights validation responsibility.

Catalogue changes belong to their control owners, while `app.js` remains the
admission/startup wiring. Keep the original public selection, filter, download
and native map entry points tied to their actual returned owner types. Source
parent names and absent fallback identities must not be inferred from another
entry. Use each module's dedicated native/browser surface and require its
complete source coverage. Field-source consumers call the shared public HTML
serializer against admitted original records; do not extract declarations from
`app.js` into a fabricated Window. Complete CSV/JSON downloads and the public
normal/optimised browser CLI remain integration gates.

Map changes run `make native-map-runtime` and the original map test cohort.
The shared engine delegates pointer/key behavior to `map/interactions.js` and
source-row controls to `map/accessibility.js`; both loading modes consume the
same owners. Runtime qualification binds all nine complete sources to their
actual bytes, genuine DOM/Cairo execution and the complete Chrome page. Every
native function and region must execute across those runtimes. Keep this
measurement distinct from Node AST coverage, and retain the original
call-recording tests as behavior checks rather than runtime qualification.

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
Direct CLI commands require the locked Python build dependencies: select their
interpreter with `ATLAS_PYTHON`, or provide it as `python3` on `PATH`. The
native input checker validates complete wire shapes using the owning profile
schema before history and correction models enforce their semantic contracts.

Run the dedicated native history, correction, renderer and CLI suites in
`validate.sh`, and `tests/test_evidence_history_browser.py` against the actual
page. Preserve exact linked revisions, disabled exports on refusal, pending
proposal custody and real native controller coverage. Date fields retain their
own meanings; unknown source publication or event dates remain unknown.
Run `tests/test_evidence_history_inputs.py` when changing history input
admission; it exercises real producer packets and native safe refusals.

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
Native research commands require Python with the locked `jsonschema` build
dependency for complete profile wire admission; select it with `ATLAS_PYTHON`
or provide `python3` on `PATH`. The Python API defaults the native checker to
its own interpreter and honours an explicit nonempty `ATLAS_PYTHON` selection.
Whole original source validation remains required above that wire check.
History and research share the canonical UTF-8 reader; qualify both native
caller suites and its whole line/branch/function coverage when changing it.
