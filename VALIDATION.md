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
| Taxonomy citations | `make validate` | Complete 135-entry input, 599 statements, exact principle/strength/challenge bindings, real export and detail serializer; 100 % lines, branches and functions for the four owning modules |
| Presentation | `04_interactive_presentation/validate.sh` | Actual assets, JSON schemas, interface language and native map/citation tests |
| Learning contract | `04_interactive_presentation/validate.sh` | Six source-bound paths, original answer claims, identical evidence in both depths and dual-hash links; 100 % native lines, branches and functions for the authored catalogue and learning model |
| Learning browser | `.venv/bin/python -m pytest tests/test_learning_paths_browser.py` | Real navigation, source-linked answers, version refusal, keyboard/mobile controls and actual file downloads; original CDP controller source/range/function evidence |
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
tree, omitting all 22 expected offline release products. It runs the native
Node taxonomy exporter, retained-history builder, Python dataset integrator, Python coverage report and
shell inventory builder, in that order. Every output must be created and
match its accepted bytes; staged inputs must remain intact, and undeclared
outputs fail. The accepted candidate is never deleted or overwritten.
A builder that does nothing cannot pass.

The reproducibility runner supplies its own Python interpreter to the Node
taxonomy validator. `make build` supplies the configured `VENV` interpreter.
An explicit `ATLAS_PYTHON` setting retains its selector semantics; an unavailable
interpreter fails without replacing accepted products. Dedicated real-environment
regressions put a dependency-free Python on PATH and exercise both public
entry points with the selected complete development environment.

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

History changes run the four dedicated native contract suites through
`validate.sh`: original journal, source-bound corrections, escaped timeline/
exact links and actual import/build/curator CLI. Their four owning modules
require 100 per cent native line, branch and function coverage. Actual Chrome
cases in `tests/test_evidence_history_browser.py` preserve the served controller
source/hash and original UTF-16 native regions/functions, with a complete
module teardown gate. They exercise real import successors, exact revision
reload/Back, source absence/return, local pending-proposal custody, concurrent
results, mobile keyboard/disclosure and actual downloads. The trusted-local
host may require the existing explicit `ATLAS_BROWSER_NO_SANDBOX=1` test mode.

The retained journal input is validated against the current complete profile
export before either presentation output is built. Reproduction retains that
input exactly; it never generates a new observation from the reproducibility
epoch. Missing or changed accepted history products and source/journal mismatch
are detected by the actual release tests. Proposal review records decisions
without applying accepted source edits or establishing authenticated authorship.

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

Learning-browser evidence preserves native Chrome ranges and function identities
against the exact original controller source. At module teardown every native
source interval and function must have an execution count. These records are
distinct from Node's line/branch/function report for the catalogue and model;
native CDP regions are not relabelled as AST branches. The six machine answer
checks verify agreement with their cited statement. They do not measure human
learning outcomes, scientific acceptance or operating-device performance.

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
Before evidence profiles were added, the native 18-product offline
reproduction passed without fresh acquisition.

The preceding 93-module production Python scan reports zero annotated Bandit
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

## Evidence profile qualification (2026-10-03)

The complete 135-entry profile migration retains 599 citations, 148 sources and
all 21 original taxonomy fields per entry. Forty-one dedicated public API/CLI cases
passed on each of Python 3.12.14 and 3.14.7. The owning validator covers all 175
statements and 74 branch exits, with no exclusions. Actual subprocess measurement
includes the native entry point and optimized refusal; duplicate JSON members,
nonfinite values, unknown sources and invalid last records refuse. A real owned
concurrent source edit is refused before a mixed snapshot can be returned.
An unknown last-record parent is refused by the public migration and reader,
including the optimized CLI, even when input hashes match the changed source.
The original reproduction accepted that parent in migration while the exporter
refused it; this mismatch is corrected without altering any catalogue value.

Node 24.21.0 passed 147 citation, export and profile-rendering cases with 100 %
line, branch and function coverage in the four owning modules. The existing 85
map cases passed. Three native Chrome cases exercised every one of the 135
dialogs, all 599 citations, keyboard disclosures, mobile width, reload and an
actual single-profile JSON download. Ordinary final-product I/O errors roll
back replaced products; this does not promise atomic multi-file reads or
power-loss durability.

The earlier forty owning reconstruction cases passed with the 20-product release contract.
Ruff, NumPy docstrings, format, strict mypy and the new validator's source-security
scan passed; documented paths, ownership headers and credential-content checks
also passed. These are scoped software checks, not a new whole Atlas suite,
hosted CI result, scientific verdict or publisher licence grant. Independent
whole-entry classification remains open, and no complete-entry flag is promoted.

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

Historical pre-commit finding, resolved on 2026-10-03: the shared Tier-0
structural auditor rejected the unchanged GitHub API array fixture as though
every JSON document had to be an object. The corrected generic JSON contract
accepts arrays and scalars while retaining object-only governance profiles,
duplicate-key rejection and original source bytes.
Atlas is outside the device family map, as documented in ADR 0001.

Every JSON path in the complete first candidate requires an exact adjacent
ownership sidecar with both standard owner SPDX records. Source fixtures
retain their publisher licence expressions and copyrights; owner records
describe concepts, code and provenance packaging only. JSON schemas, source
cells, frozen input hashes and generated products remain unchanged.

Historical pre-commit finding, resolved on 2026-10-03: the shared commit wrapper
rejected genuine additional foreign copyright records. The corrected staged
sidecar contract requires both owner records exactly once and retains distinct
publisher records. Publisher notices and licence expressions remain intact.

The corrected shared contracts passed the same 184 dedicated public CLI and
native Git cases on Python 3.12.14 and 3.14.7. These are 184 unique cases, not a
whole Atlas suite. Native subprocess measurement covers all 61 changed lines
and 18 changed branch exits; the structural auditor is fully covered. The
whole commit wrapper remains partially covered (282 of 290 statements and
120 of 128 branch exits in the author's measurement). Independent review
qualified the shared compatibility repairs and preservation of all 739 first
commit blobs within that scope. It requested this documentation correction;
it did not grant whole-programme, scientific or release acceptance. The local
first commit exists; no push, hosted CI, deployment or release follows from
these checks.

Correctness CI has no path filter. A workflow that did not exercise a changed
surface at its exact revision supplies no acceptance evidence.

## Reproducible comparison contract

The comparison contract uses the complete real profile document for snapshot
identity, rather than only the inherited taxonomy hash. Its dedicated public
Node API checks cover all 135 actual entries, source-preserving exports,
ordered stable-ID URL restoration, unavailable versions, missing parameters,
zero values and incompatible declared units/conditions/boundaries/conversions.
No parameter is numerically merged and no scientific review flag is promoted.

`validate.sh` includes the dedicated comparison contract at the existing
100 per cent line/branch/function floor. Run the actual browser boundary with
`python -m pytest tests/test_taxonomy_comparison_browser.py`; the maintained
fixture selects the exact observed URL of its one owned native page and
retains source-bound CDP execution records. The normal Chrome sandbox is the
default; the documented trusted-local host override remains explicit.
Browser tests do not replace a human comprehension study or deployment review.

## Research comparison restoration

`tests/test_research_comparison.py` exercises the real public API and CLI against
the complete source catalogue, changed originals, unavailable snapshots and
an actual Chrome-downloaded comparison. Measure the entire owning
`tools.research_comparison` module at the unchanged 100 % statement/branch floor.
`validate.sh` enforces 100 % native line/branch/function coverage for the dedicated
research reader; all 135 original identities round-trip. The Jupyter notebook
must execute its real cells against the accepted snapshot and reproduce the
same result on a second execution. Keep actual executed notebooks and failures
privately; the public notebook contains input cells without claimed outputs.
See [the research contract](examples/research/README.md) for expected hashes,
canonical input, original rights and interpretation boundaries.
