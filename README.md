<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
ATLAS REACTORUM — public documentation
-->

# Atlas Reactorum

An English-first, source-aware atlas and research library of reactor
technology: nuclear fission, plasma and alternative fusion, chemical and
biochemical reactors, hybrid systems, and explicitly labelled speculative
technologies.

The atlas separates three things that are commonly conflated — the physical
principle, the maturity of the technology, and the strength of the evidence
behind a claim. Coverage is deliberately broad, but completeness is never
fabricated: a large record count is not a count of unique reactor vessels.

## Open the atlas

Open [`04_interactive_presentation/index.html`](04_interactive_presentation/index.html)
in a modern browser. It is fully static, carries no runtime dependencies, and
works from `file://` with no build server.

Current integrated snapshot:

- 135 indexed architectures, subtypes, operating modes and integration concepts;
- 13,459 facility and project records, of which 13,357 carry coordinates;
- 98 evidence-screened fusion companies, programmes and adjacent organisations;
- 30 public ANULUM reactor-related repositories;
- domain, layer, source-dataset, country, status and text filters over the full
  dataset, with filtered CSV and JSON export.

The default fusion input is the pinned
[IAEA FFDB catalogue](05_global_reactor_map/imports/fusion/ffdb/README.md):
174 source records, including 137 publisher map points. The builder validates
the complete capture, manifest, source table and field provenance before
writing outputs. Missing coordinates and operation dates remain absent;
historical overlays do not fill them.

These are overlapping discovery records, not a deduplicated asset register. An
industrial-site record usually establishes a regulated facility or activity,
not the number or design of reactors inside it. Company and speculative-
technology records document claims and evidence boundaries; inclusion is not
technical validation.

## The map

The facility layer is a canvas map engine with no runtime dependencies. It
draws on the Equal Earth projection, which is equal-area, so visual density on
the map is honest density on the globe. Points are indexed in a quadtree and
aggregated into screen-space groups: a group is filled by its majority domain
and ringed by its rarest, so a single fusion device among four hundred chemical
sites is still visible.

Pan by dragging or with the arrow keys, zoom with the wheel or `+` and `-`,
reset with `0`, and select a group to zoom into it. Every mapped record is also
reachable by keyboard and assistive technology. See
[`04_interactive_presentation/map/README.md`](04_interactive_presentation/map/README.md).

Canonical Reactor project citations, including local expansion proposals,
are available in [the versioned portfolio snapshot](metadata/reactor_portfolio/README.md).
These citations preserve producer revisions and do not certify their claims.

## Repository guide

- [`00_index/README.md`](00_index/README.md) — scope, coverage and evidence rules
- [`01_nuclear/`](01_nuclear/) — fission and fusion literature
- [`02_chemical_biochemical/`](02_chemical_biochemical/) — chemical and biochemical literature
- [`03_hybrid_emerging/`](03_hybrid_emerging/) — hybrid and speculative concepts
- [`04_interactive_presentation/README.md`](04_interactive_presentation/README.md) — atlas use, rebuild and validation
- [`05_global_reactor_map/README.md`](05_global_reactor_map/README.md) — facility-map schema, imports and limitations
- [`metadata/`](metadata/) — inventories, audits, provenance and checksums
- [`metadata/coverage_audit/COVERAGE.md`](metadata/coverage_audit/COVERAGE.md) — generated field-level research backlog
- [`CHANGELOG.md`](CHANGELOG.md) — released and unreleased changes

## Rebuild and validate

```bash
node 04_interactive_presentation/scripts/export_taxonomy.cjs
python3 04_interactive_presentation/scripts/build_datasets.py
python3 metadata/coverage_audit/build_coverage.py
(cd 04_interactive_presentation && ./validate.sh)
./metadata/build_inventory.sh
```

`validate.sh` verifies that its required tools are present before running any
check, and runs the map engine's and taxonomy citation/export tests, so a checker that cannot execute
is reported as a failure rather than as a check that passed.

The taxonomy detail view retains 599 source-inspected statements for 135 entries,
including 480 statements bound to complete physical fields, with exact
locators and support boundaries. Unknown original retrieval dates remain
explicit. Full entry review remains pending.
Research configurations distinguish pool/tank geometry, dissolved aqueous fuel,
critical versus source-driven subcritical operation, and pulsing as a mode.
Homogeneous composition does not imply uniform gas or neutron distributions.
EPFL and Mainz provide named teaching/control and pulse examples; facility
limits, licensing and pulse capability are not universal.
Electrolysers and fuel cells have separate reaction directions and ionic carriers.
The dated DOE/NETL/PNNL sources support material, heat-integration and durability
limits; cost/life targets, universal fuel tolerance and current fleet performance
are not inferred. AEM precious-metal reduction remains potential.
Batch and semi-batch entries distinguish exothermic heat release from other
campaigns; stopping feed need not stop reaction of accumulated material. CSTR
and plug-flow entries identify ideal model assumptions. Cascade feed and
temperature options retain process-specific benefits and coupled-stage limits.
The [citation contract](metadata/taxonomy_audit/README.md) documents the authored
metadata, catalogue-only source custody and schema 1.3.0 audit exports.

`python3 tools/preflight.py --check reproducibility` rebuilds the 18 offline
release products in a fresh external temporary tree and requires identical
bytes, including both JSON and JavaScript exports and the inventory receipts.
It preserves accepted files. Use `--workspace /absolute/external/workspace`
to select an existing temporary parent. This checks the release build from
frozen local inputs; it does not perform fresh source acquisition or rights
verification. See [Validation](VALIDATION.md) for the contract and limitations.

The map engine's tests can also be run directly:

```bash
(cd 04_interactive_presentation/map && node --test tests/*.test.js)
```

The browser integration check is documented in the presentation README.
Dataset-specific import directories carry their own builders, source
registries, rights notes and validators.

Third-party document bodies are retained in separate owner-controlled local
custody. [The document manifest](metadata/document_custody.json) preserves
checksums and source references; source access does not establish redistribution
rights.

## Rights and attribution

The repository's own code and documentation are licensed under the GNU Affero
General Public License, version 3 or later; see [`LICENSE`](LICENSE) and
[`COMMERCIAL-LICENCE.md`](COMMERCIAL-LICENCE.md).

The material it catalogues is not covered by that licence. This repository
aggregates sources with differing licences and rights conditions — do not
assume a single blanket licence applies. Follow each catalogue row, source
registry, local attribution file and dataset README. The generated datasets'
[component rights map](04_interactive_presentation/data/source_rights.json)
binds each source layer and overlay to its attribution and input digest.
Copyright-retained
sources are used only for bounded factual assertions and are never
redistributed as full works; a catalogue-only record is a valid record where
access or redistribution is restricted.

Published facility fields retain 1,631 verbatim source assertions: 1,092 end-use
labels and 539 feedstocks or fuel classifications. They supply purpose/use
for 1,342 records and fuel/feed classifications for 533 records. Six secondary
WRI categories remain classifications of whole plants. Per-field provenance
records the original cell, source identifier, capture date, licence and hash;
unknown reactor composition and current physical operation remain unknown.
The facility dataset uses schema 1.1.0. Search, facility details and filtered
CSV/JSON retain these fields, and CSV carries the assertion array as JSON.
