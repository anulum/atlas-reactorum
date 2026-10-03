<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
ATLAS REACTORUM — validation
-->

# Validation

The complete repository gate is `make verify`, comprising lint, strict types,
all Python source directories, native presentation tests and repository
checks. Focused checks use the dedicated tests and complete owning source
scope. They provide evidence for that scope, not a whole-candidate verdict.

## Gates

| Layer | Command | What it establishes |
| --- | --- | --- |
| Lint and format | `make lint` | Ruff rules, NumPy docstrings and formatting |
| Commit hooks | `make hooks` | The local and CI hook chain; formatters preserve captured and generated data formats |
| Types | `make typecheck` | Strict mypy across every source directory |
| Python tests | `make test` | Enumerates every production Python source directory; requires 100 % statements and branches |
| Map engine | `node --test 04_interactive_presentation/map/tests/*.test.js` | Projection, indexing, clustering and rendering behaviour |
| Taxonomy citations | `make validate` | Complete 135-entry input, 599 statements, exact principle/strength/challenge bindings, real export and detail serializer; 100 % lines, branches and functions for the three owning modules |
| Presentation | `04_interactive_presentation/validate.sh` | Actual assets, JSON schemas, interface language and native map/citation tests |
| Browser | `.venv/bin/python -m pytest tests/test_browser_checks.py` | Complete loaded presentation through native Chrome, including the public DevTools CLI |
| Licences | `.venv/bin/python -m reuse lint` | File-level attribution and licensing metadata; publisher grants remain a separate review |
| Source security | `.venv/bin/python -m bandit -r . -x ./tests -f json` | Unsuppressed production-source scan; current residuals are described below |
| Repository | `make preflight` | Reproducibility, documented paths, credential content and headers |
| Per-layer | Each import's own builder and validator | Source schema, provenance, earlier-layer immutability and declared failure behaviour |

The locked development environment supplies Python tooling. Native Node,
Chrome or Chromium and the shell inventory tools are also required. A missing
tool or a failed check is a failure, not a pass. Ruff security rules and a
Bandit result are separate evidence; a clean Ruff run does not dispose of
Bandit findings.

## Formatting and source integrity

`make hooks` runs the pinned development graph through the same entry point
as the pre-commit workflow. Newline and whitespace fixers omit byte-exact
TSV, JSON, NDJSON, CSV, GeoJSON and FFDB frame files, including test captures,
plus generated presentation data. Conflict, private-key, credential and size
checks remain active. Source-specific validators and the reproducibility
check continue to reject changed input hashes.

Git attributes disable text conversion for those data formats. EditorConfig
removes inherited encoding, indentation, line-ending and final-newline rules
for them, and disables whitespace trimming. These settings do not prevent a
separately enabled editor formatter from rewriting a captured response.
Compare original source hashes after editing configuration or running tools.
The empty `.nojekyll` presence marker is intentional and appears in the
inventory's empty-file report.

## Reproducibility and selected sources

`preflight.py` copies public source files into a fresh external temporary
tree, omitting all 18 expected offline release products. It runs the native
Node taxonomy exporter, Python dataset integrator, Python coverage report and
shell inventory builder, in that order. Every output must be created and
match its accepted bytes; staged inputs must remain intact, and undeclared
outputs fail. The accepted candidate is never deleted or overwritten.
A builder that does nothing cannot pass.

The inventory receipt's recorded UTC timestamp supplies `SOURCE_DATE_EPOCH`
to the shell builder. This reproduces its existing date exactly; no timestamp
or product is excluded. Missing products, tools, invalid receipts and process
timeouts fail. `--workspace /absolute/external/workspace` selects an existing
external temporary parent; `--timeout` bounds each builder.

The default fusion input is the pinned
[IAEA FFDB catalogue](05_global_reactor_map/imports/fusion/ffdb/README.md).
Before creating an output directory, the dataset integrator redecodes its
complete visible-data selection and validates its distinct artifact/original
response digests, acquisition identity, all 174 TSV rows and
complete field provenance. All four input hashes are recorded. Missing or
altered required inputs refuse the build without an implicit historical
fallback. `--fusion-source historical` explicitly selects the retained
earlier route and its documented limitations.

The current default snapshot contains 13,459 records, including 13,357
coordinate pairs, 98 companies and 135 taxonomy entries. Its 180 fusion records
comprise 174 FFDB source records and six separate supplemental observations.
Of the FFDB rows, 137 have publisher map coordinates; 37 retain absent pairs.
Old enrichment values do not fill their coordinates or operation dates.

This contract reproduces the offline build from frozen local inputs.
It does not refresh publishers, recover historical acquisition originals,
resolve source rights, verify physical-device identity or establish global
completeness.

## Native browser evidence

The browser tests use a separate temporary Chrome profile, loopback-only
DevTools and the complete actual Atlas application. Normal and optimised
Python CLI runs, protocol errors, deadlines, search, filters, dialogs, map
invariants and actual CSV/JSON downloads are exercised.

The normal Chrome sandbox is enabled by default. On hosts explicitly
configured for trusted local assets without it, the fixture accepts:

```bash
ATLAS_BROWSER_NO_SANDBOX=1 .venv/bin/python -m pytest tests/test_browser_checks.py
```

Record which mode ran. The option changes the browser launch only; it does
not relax checks or substitute assets. Manual page selection and endpoint
requirements are documented in the
[presentation README](04_interactive_presentation/README.md#full-data-browser-checks).

## Current focused checkpoint: 2 October 2026

These measurements belong to the specified complete owning source scopes and
their pinned inputs. They do not constitute an aggregate repository coverage
measurement or a fresh run of every earlier check.

| Owning source | Native evidence | Statements | Branches |
| --- | --- | --- | --- |
| FFDB namespace package: framing, selection, reader, catalogue, producer and integration | 129 cases on each of Python 3.12.14 and 3.14.7 | 411/411 | 120/120 |
| Main dataset integrator, including complete historical selection | 233 focused cases, 12 status cases and actual historical CLI replay | 355/355 | 150/150 |
| Browser checker | 48 native Chrome cases in explicit local no-sandbox mode | 211/211 | 50/50 |
| Historical frozen-input selection and binding | 24 owning cases on each pinned Python version | 70/70 | 20/20 |
| Historical first-pass enrichment validator | Current focused validator cases | 132/132 | 76/76 |
| Historical second-pass gap generator and validator | Focused cases and actual frozen CLI with external report output | 227/227 | 88/88 |
| Historical third-pass gap generator and validator | Focused cases and actual frozen CLI with external report output | 213/213 | 84/84 |
| Historical live-acquisition refusal | 11 public CLI cases on each pinned Python version | 14/14 | 2/2 |

The seven current historical consumer modules collectively cover all 997
statements and 418 branches on both pinned Python versions, with no missing or
excluded paths. The 233-case focused cohort passed but initially measured
98.30 % coverage; that result remains separate from the completed measurement.
Twelve existing status-vocabulary cases and four additional actual CLI cases
exercise the complete original-nine-input route, missing-bundle refusal and
both frozen validators with external report destinations. The native original
bundle remains in separate custody; no source data was fabricated or relicensed
for these checks. Existing outputs remain intact on missing-bundle refusal.
The original four historical products and all four original gap tables reproduce
byte-for-byte. The default FFDB selection reproduces the five current
facility/company products. Neither mode silently falls back to the other.

The source selection retains every visible FFDB raw/display cell without
redistributing the full viewer renderer. Strict mypy, Ruff, formatting and
docstring checks passed for the relevant source and tests. Node 24.21.0 ran
85 map cases and 125 citation/export/serializer cases; the three owning
citation modules retain 100 % line, branch and function coverage. Native
18-product offline reproduction passes without fresh acquisition.

The complete 93-module production Python scan reports zero annotated Bandit
findings. With annotations ignored, it retains 24 low-severity B404/B603
subprocess reports, with no medium/high findings or scan errors. The removed
historical URL-opening sink is replaced by a public acquisition refusal.

Independent review accepted the original refusal and all 12 subprocess sites.
Ten sites remain byte-identical in the current source. The two historical
validator sites changed for the frozen-bundle selection; their successor
review accepted the actual source and affected seven-module qualification
on both pinned Python versions. The accepted boundary assumes trusted operators,
native-tool lookup and local sibling scripts, with finite per-process
deadlines. It does not establish descendant-process containment, source
permissions or whole release approval.

## Historical whole-suite checkpoint

The earlier bootstrap measurement covered 60 Python files in 31 directories:
31.79 % statements, 30.23 % branches and 31.32 % combined coverage. That
dated checkpoint failed the 100 % gate. It is neither a current aggregate
measurement nor replaced by later focused successes.

Other historical results included 505 Python tests, 85 map tests and
13,017 facility records with 12,813 mapped. Those counts belong to the earlier
inputs. The earlier source security audit found 13 medium and 89 low findings;
the current unsuppressed result is stated separately above.

## Acceptance boundaries

`make test` enumerates standalone source directories because measuring only
the two central generators, or relying on `--cov=.` alone, omits executable
surfaces. No CLI entry-point guard is excluded. The 100 % statement/branch
floor remains in force; current whole-candidate acceptance is still open.

The full FFDB viewer response and permission-page HTML are preserved privately
and omitted from the public source tree. The 37,968-byte visible-data selection
retains all typed dictionary members and complete Table/Main indices, with a
labelled authored header and distinct original-response linkage. A direct
comparison against the retained original proves every raw/display cell equal.
The two authored acquisition manifests retain exact ownership sidecars.
Selected data, TSV and cell provenance use the IAEA source-specific permission
reference instead of broad software annotations. The preceding complete source
selection passed native REUSE for all 600 applicable files, with zero missing
licences, invalid expressions or read errors. Temporary bytecode and tool
caches remain outside that measured source tree.

REUSE syntax does not establish a publisher grant. The
[component rights map](04_interactive_presentation/data/source_rights.json)
binds 12 facility components, four company components, five research overlays,
five company overlays and 40 exact default input pins. Original editorial
contributions retain their own licence; source-specific terms apply to the
respective data contributions. The FFDB permission and the historical
146-identity six-field compilation permission have bounded accepted scopes.
Independent review also qualified the mixed-source attribution map, ordered
field origins and bounded PPPL terms corrections. These dispositions retain
their described source and field scopes; they do not approve the whole first
candidate or grant rights over foreign expression. Linked works are not
relicensed by citation or checksum.

Complete scientific-entry review and current maturity/evidence classifications
remain pending. Source locators, software tests and custody receipts do not
certify reactor performance or commercial readiness.

The shared Tier-0 structural auditor also currently rejects the unchanged
GitHub API array fixture as though every JSON document must be an object.
That shared-tool contract must be corrected while retaining the original
source bytes and duplicate-key rejection; it is not a dataset corruption.
Atlas is outside the device family map, as documented in ADR 0001.

Every JSON path in the complete first candidate requires an exact adjacent
ownership sidecar with both standard owner SPDX records. Source fixtures
retain their publisher licence expressions and copyrights; owner records
describe concepts, code and provenance packaging only. JSON schemas, source
cells, frozen input hashes and generated products remain unchanged.

The shared commit wrapper currently rejects genuine additional foreign
copyright records despite the required owner records being present. That
compatibility defect needs its canonical correction before the first commit.
Removing foreign notices or changing their licences is not an admissible fix.

Correctness CI has no path filter. A workflow that did not exercise a changed
surface at its exact revision supplies no acceptance evidence.
