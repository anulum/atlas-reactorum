<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — interactive presentation documentation
-->

# Atlas Reactorum — interactive presentation

An English-first, evidence-bounded presentation covering nuclear fission, plasma fusion, chemical and biochemical reactors, and hybrid or emerging systems. It is a no-build static site: no package manager, framework, remote font or runtime API is required.

This interface is a local research prototype. Repository validation applies to the retained local snapshot. Hosted publication and deployment require their own review.

## Open locally

- Open `index.html` directly (`file://` is supported), or
- run `python3 -m http.server 8080` in this directory and visit `http://localhost:8080/`.

Keyboard: Left/Right or Page Up/Page Down moves between sections; Home/End moves to the first/last section. Filters, selects, cards and dialogs are keyboard accessible. Reduced-motion preferences are respected.

The facility view reports live domain counts and can export the complete current filter result as CSV or JSON. The 250-card display cap affects rendering only; it does not truncate map points, search, counts or exports.

## Evidence boundary

The expanded taxonomy indexes 135 entries: 29 fission, 32 fusion, 52 chemical/biochemical and 22 hybrid/emerging. These include architectures, subtypes and operating modes that can overlap. `data/taxonomy-expanded.sources.tsv` exposes each source mapping. The scientific/editorial audit from `../metadata/taxonomy_audit/` is integrated into `data/taxonomy-audit.*` and the detail dialog for all 135 entries. The first pass covered 123; the 11 later additions were audited on 2026-09-29, and the merged critical/subcritical entry was split into two, so no entry is marked `not-yet-audited`. This is classification and source-scope triage, not full per-claim verification. Rebuild both exports with `node scripts/export_taxonomy.cjs`.

The detail dialog now shows 599 source-inspected statements for 135 entries,
including exact sections, separate printed/PDF pages and each source's support
boundary. Four hundred and eighty statements bind complete physical fields for PWR, BWR,
integral PWR, six HTGR/fast-reactor types, SCWR, VHTR and three salt-based types, two heavy-water types, Magnox, AGR and RBMK, plus seven research configurations, four electrolysers and five fuel-cell types; the integral layout retains the
source's most-or-all qualification. The historical IAEA sources distinguish
high-temperature design targets, fuel testing and coolant properties from
current deployment. Sodium fast-core classification does not imply absence of
every moderating shield, and ALLEGRO start-up fuel differs from its later target.

Five chemical entries cover batch and semi-batch operation, ideal CSTR and
plug-flow models, and cascades of physical CSTRs. Exothermic heat release,
possible multiple steady states and kinetic benefits keep their conditions.
Stopping a semi-batch feed need not stop the accumulated reaction. Staged feed
and temperature options are documented separately; the cited equal-feed Monod
model gives no generic advantage, and the temperature case uses burst transfer.
The GIF SCWR/VHTR pages supply design goals and technical challenges; process
heat and efficiency potential are not measured plant performance.
Salt-based entries distinguish dissolved fuel from solid fuel cooled by fluoride
salt. Fuel circulation and online processing are not universal; fuel-cycle
flexibility remains potential and decay-heat removal needs qualification.
Heavy-water entries distinguish pressure tubes from pressure-vessel internals.
Magnox operation and INSAG-7 feedback/channel analysis are historical. AGR
fuel/cladding and graphite inspections have specific source support; fleet
counts and present-day unit certification are not inferred.
Research configurations distinguish pool/tank geometry, dissolved aqueous fuel,
critical versus source-driven subcritical operation, and pulsing as a mode.
Homogeneous composition does not imply uniform gas or neutron distributions.
EPFL and Mainz provide named teaching/control and pulse examples; facility
limits, licensing and pulse capability are not universal.
Electrolysers and fuel cells have separate reaction directions and ionic carriers.
The dated DOE/NETL/PNNL sources support material, heat-integration and durability
limits; cost/life targets, universal fuel tolerance and current fleet performance
are not inferred. AEM precious-metal reduction remains potential.
Source-copy retrieval dates are shown separately from inspection dates.
Unknown historical retrieval dates remain explicit; an inspection date does
not fill that gap.
Entries without claim citations show pending review. These statements
do not establish complete scientific review for any entry. The
[citation data contract](../metadata/taxonomy_audit/README.md) binds all 135
current catalogue entries before export; source originals remain catalogue-only.

The atlas is an orientation and research interface, not device design, safety analysis or investment advice. Qualitative comparison scores deliberately avoid fake numerical precision.

- **External sources** support physical and historical claims.
- **Literature catalogues** retain citation URLs and historical document identities. Access and redistribution follow the original publisher's terms.
- **`anulum/scpn-*` repositories** are user-owned research projects. Repository existence, code volume or an architecture document is not independent scientific validation.
- **Speculative/contested entries** are visually segregated. Inclusion means “documented for critical study”, not endorsement.
- **Company claims** are stored separately from independent-evidence notes.

## Data integration seams

The global facility map uses `data/global_reactors.sample.js` for `file://` compatibility. Its 13,459 records comprise 1,823 GEM power-reactor units, 195 historical WRI plant records, 172 research-reactor records, 174 pinned IAEA FFDB catalogue records, 11,086 industrial facility/site or process-project records and nine separate supplemental context records. Fifty-four research-reactor records receive official-source overlays. The default FFDB selection validates the complete 2026-10-02 visible capture and both cached products before exporting; 137 FFDB records have publisher map locations. The explicit `--fusion-source historical` option uses the attributed six-field FusionBenchmark compilation selection and separate overlays. Complete original inputs require `--fusion-source historical-full --historical-bundle /path/to/complete-inputs`, with all nine declared hashes and schemas verified before export. See the [historical input contract](../05_global_reactor_map/imports/fusion/README.md). They do not fill FFDB fields or select themselves when a new-source input is missing. See the [new source contract](../05_global_reactor_map/imports/fusion/ffdb/README.md) and [source-specific permission](../05_global_reactor_map/imports/fusion/ffdb/RIGHTS.md). These layers overlap and do not count unique physical reactors. The corresponding JSON is validated by `data/global_reactors.schema.json`; domain, layer, source-dataset, country, status and text filters plus CSV/JSON exports operate on the full set, while the visible card list is capped at 250 matching records for browser performance.

The company landscape follows the same pattern with `data/fusion_companies.sample.*` and contains 98 audited company/programme records: the original 51-record audit plus 18 first-round, 15 Asian/European second-round and 14 Latin American/MENA/other third-round candidates. A 98-row depth audit exposes field gaps; five depth passes apply 39 exact-name current-source overlays without overwriting the source catalogs. The [latest ten-profile review](../metadata/company_audit/depth_round8/README.md) records 33 citations and their field associations, including unresolved prototype fuel and source-access limits. The UI separates company claims, the highest independently supported bounded milestone, unsupported/ambiguous claims, identity class, evidence tier and audit confidence. This screening audit is not technical certification or investment advice.

The ecosystem panel is generated from a dated GitHub API snapshot and displays 30 public ANULUM reactor-related repositories across device-family, shared-kernel, control/integration and supporting-hardware categories. Refresh logic and the canonical metadata snapshot live in `../metadata/anulum_github/`. Repository activity and software tests are not physical-reactor validation.

Run `python3 scripts/build_datasets.py` to regenerate JSON and offline JS bundles from the catalogs. See `data/README.md` for provenance and `../00_index/COVERAGE_LEDGER.md` for the outstanding coverage criteria.

## Publication boundary

Open the presentation locally. Hosted publication is a separate reviewed
operation after repository and artifact-custody checks. The historical deployment prototype remains in local handover custody and is
not an approved workflow. Internal asset paths are
relative, and the presentation expects its sibling source catalogues.

## Files

- `index.html`, `styles.css`, `app.js` — application;
- `data/` — generated JSON and offline JavaScript datasets, with JSON Schemas;
- `SOURCES.tsv` — claim/source map;
- `ATTRIBUTION.md` — source and licensing boundary;
- `.nojekyll` — serve static files unchanged;

## Checks

Run `./validate.sh` to check JSON, JavaScript syntax, required files and accidental
non-English UI residue. It runs the map tests and dedicated citation/export tests,
requiring 100 per cent line, branch and function coverage for the citation
validator, native exporter and detail serializer. Browser rendering should still
be inspected after substantive visual edits.


### Full-data browser checks

`browser-check.py` connects to one explicitly selected local Chrome page; importing it makes no browser or network connection. Serve the complete repository locally, then open its presentation in a separate headless Chrome profile with the normal browser sandbox enabled:

```bash
python3 -m http.server 8080 --bind 127.0.0.1
# In another terminal; google-chrome or chromium must be installed:
google-chrome --headless --remote-debugging-address=127.0.0.1 --remote-debugging-port=9223 --remote-allow-origins=http://127.0.0.1:9223 --user-data-dir=/tmp/atlas-browser-check http://127.0.0.1:8080/04_interactive_presentation/index.html
python3 04_interactive_presentation/browser-check.py --endpoint http://127.0.0.1:9223 --page-url http://127.0.0.1:8080/04_interactive_presentation/index.html
```

Use an unused port and a dedicated profile; do not point this probe at a shared browser. The endpoint must be an anonymous loopback HTTP origin. Page selection uses the exact URL and refuses absent or duplicate matches; the WebSocket debugger must belong to the same origin. `--timeout` is a positive finite connection/command/readiness limit. Each command matches its own sequence identifier and ignores intervening native events, with a deadline across those events.

The probe reloads the selected page, waits for full dataset and map initialization and checks the complete snapshot: 135 taxonomy entries, 13,459 facility/site records, 98 companies and the dated 30-public-repository catalogue. The 13,357 mapped/indexed records, equal-area canvas projection, keyboard reachability, cluster conservation, card cap, search/filter/dialog and source-scope labels are included. The public catalogue count is separate from the current research-group repository registry.

All checks remain active under `python -O`; a failed predicate, protocol/JavaScript error, missing full dataset or unavailable browser returns a failed report and exit status one. Argument errors use exit two. A passing report is generated only after every check passes. Connections close on success and failure; the probe does not close the browser itself. `BrowserSession`, `select_page`, `response_result`, `evaluation_value`, `parse_counts` and `run_checks` expose the same typed connection, protocol decoding and validation boundaries used by the CLI.

The dedicated Python tests require native Chrome or Chromium and use isolated temporary profiles with the browser sandbox enabled. They load all actual application assets and datasets, exercise real DevTools/WebSocket events, errors, deadlines and normal/optimized CLI runs, and deliberately change only the served index language to verify failure. Public decoders are also tested with explicit corruptions of target lists and replies captured from that actual browser; these are validation tests, not fabricated WebSocket servers or substituted browser clients. The checks verify software behavior and recorded-data presentation, not scientific approval or device control authority.

For hosts configured to run trusted local Atlas assets without the Chrome
sandbox, set `ATLAS_BROWSER_NO_SANDBOX=1` when running
`pytest tests/test_browser_checks.py`. The native fixture still uses a separate
temporary profile, loopback-only DevTools and the complete actual application.

Published facility fields retain 1,631 verbatim source assertions: 1,092 end-use
labels and 539 feedstocks or fuel classifications. They supply purpose/use
for 1,342 records and fuel/feed classifications for 533 records. Six secondary
WRI categories remain classifications of whole plants. Per-field provenance
records the original cell, source identifier, capture date, licence and hash;
unknown reactor composition and current physical operation remain unknown.
The facility dataset uses schema 1.1.0. Search, facility details and filtered
CSV/JSON retain these fields, and CSV carries the assertion array as JSON.
