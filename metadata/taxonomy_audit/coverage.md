<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/taxonomy_audit/coverage.md
-->

# Reactor taxonomy audit

Audit date: 26 September 2026. Scope: the 123 entries preserved in `input-taxonomy-snapshot.tsv`, not any subsequently corrected version of the application. No taxonomy files were changed by this audit.

## Result

The taxonomy is a useful discovery index, but it is not a verified catalogue of 123 distinct reactor architectures. It contains 22 fission, 31 fusion, 48 chemical and 22 hybrid entries. Its own kinds comprise 90 architectures, 12 subtypes and 21 operating modes, ignition schemes, process classes, configurations or application/integration concepts. Even the 90 architecture labels require scientific editorial review.

Three confirmed misassigned references affect **24 entries**, because sources were attached to whole groups. These should be corrected before citing the atlas as an evidence-backed reference. A fourth source URL returns HTTP 404. None of the rows receives a blanket scientific approval in `audit.tsv`; `plausible-provisional` means no specific classification error was found in this bounded review, not that all its claims were established.

## Citation corrections

| Assigned source | Verified problem | Recommended source/action |
|---|---|---|
| IAEA `Pub1854_web.pdf` | Actual title: *Decommissioning of Particle Accelerators*. It is not a general fusion physics text. | Replace with [IAEA Fusion Physics, STI/PUB/1562](https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1562_web.pdf), then map exact chapters to entries. The replacement PDF was downloaded in memory and its opening pages inspected. |
| DOI `10.1063/1.873677` | Crossref title concerns long-time tails, self-organized criticality and transport. It does not support Z-pinch-driven ICF. | [Sandia Z-pinch/ICF hohlraum study](https://www.sandia.gov/research/publications/details/dynamics-of-a-z-pinch-x-ray-source-for-heating-icf-relevant-hohlraums-to-12-2000-07-10/) directly describes the relevant experimental configuration. Do not apply it indiscriminately to MagLIF. |
| DOI `10.1088/0741-3335/36/7/001` | Crossref identifies a paper on particle pinch velocity in the compact helical system CHS, not spheromaks. | Remove from FRC/spheromak group. [LLNL's December 1999 research magazine](https://str.llnl.gov/sites/str/files/2024-04/1999.12.pdf) contains SSPX/spheromak coverage; FRC needs its own reference. |
| DOE `/eere/fuelcells/technical-targets-water-electrolysis` | HTTP 404 during this audit. | Use the [DOE technology assessment](https://www.energy.gov/sites/default/files/2024-12/hydrogen-shot-water-electrolysis-technology-assessment.pdf) and [current electrolysis overview](https://www.energy.gov/cmei/fuels/hydrogen-production-electrolysis). Scope each electrolyser separately. |

DOI registration establishes article identity, not the truth of its findings. Publisher access challenges occurred even with HTTP 200. HTTP failures are reported as observations during this check, not proof that a work is permanently unavailable.

## Maturity and classification findings

- Pebble-bed HTGR is understated as demonstration-only: [Tsinghua's HTR-PM report](https://www.inet.tsinghua.edu.cn/ineten/info/1024/1698.htm) documents commercial operation beginning in December 2023. This supports deployment of that architecture, without establishing a large commercial fleet or every new design.
- Sodium fast reactors also have deployment evidence: the [IAEA 2024 Nuclear Technology Review](https://www.iaea.org/sites/default/files/gc/gc68-inf-4.pdf) reports operating SFRs. A family-level deployment label should coexist with design-specific research statuses.
- Historical commercial use needs a separate facet. Magnox, prismatic HTGR and heavy-water pressure-vessel histories cannot be expressed cleanly by a single present-day maturity label.
- VHTR, optimization, process operating modes, polymerisation chemistry and propulsion applications overlap underlying architectures. Parent-child links must not imply mutually exclusive types.
- Segmented flow is not limited to microchannels; the current parent relationship is too restrictive. Ideal plug flow and tubular geometry are also different concepts.
- Solid-core nuclear thermal rockets and fission-fragment propulsion have fission as their primary physics. Direct fusion drive and pyroelectric fusion belong primarily to fusion, with propulsion or beam-source application facets. “Hybrid” should identify actual coupled processes, not simply all unusual technologies.
- The dense-plasma-focus reference is developer-authored progress reporting. It supports research context, not independently verified commercial p–11B reactor performance. Polywell's cusp-confinement result similarly supports a subsystem, not net-energy operation.
- The NETL gasifier source is specifically an entrained-flow project, so fixed/moving-bed and fluidised-bed entries need their own sources. The plasma-chemistry review explicitly concerns non-thermal plasma and cannot alone establish thermal-arc deployment.
- LENR entries correctly carry contested labels, but their kind should clearly identify claim classes. A null replication source is evidence about a claim, not evidence of an operating reactor.

## Meaningful missing coverage

Add entries only where a distinct reactor architecture or explicitly labelled mode is useful. None of the following is a reason to create one card per vendor, fuel isotope, output size or device name.

| Priority | Missing coverage | Evidence / treatment |
|---|---|---|
| High | Research-reactor geometries: pool, tank, tank-in-pool, homogeneous; critical/subcritical assemblies and pulsed operation | [IAEA research-reactor construction coverage](https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1596_web.pdf) and [IAEA working-group scope](https://www.iaea.org/topics/research-reactors/technical-working-group-on-research-reactors-twg-rr). Geometry, criticality and pulse mode must be separate facets rather than blindly additive entries. |
| High | Aqueous homogeneous fission reactors | Distinct fuel-bearing liquid architecture missing from the salt-focused liquid-fuel coverage; use IAEA homogeneous research-reactor references before adding details. |
| High | Sequencing-batch biological treatment reactor | [EPA fact sheet](https://www.epa.gov/system/files/documents/2022-10/sequencing-batch-reactors-factsheet.pdf) directly defines the alternating fill/react/settle/draw process. Label it as an operating configuration, not an entirely independent physical principle. |
| High | Upflow anaerobic sludge blanket and fixed-film anaerobic reactors | [EPA definition](https://www3.epa.gov/ghgreporting/help/tool2014/definitions/industrial-wastewater.html) explicitly identifies these architectures; farm digesters alone do not cover wastewater reactor diversity. |
| High | Chemical-looping reactors | [NETL chemical-looping description](https://www.netl.doe.gov/node/7478) supports coupled solids/reactor loops. Cross-link to fluidised/moving-bed geometry instead of duplicating all combinations. |
| Medium | Oscillatory baffled, spinning-disc/rotating packed-bed reactive systems, monolith reactors, reactive extrusion | Candidate gaps requiring architecture-specific primary studies before insertion; no full evidence audit completed here. Distinguish reactive apparatus from nonreactive separators. |
| Medium | Reactive distillation, sorption-enhanced reaction, catalytic plate/heat-exchanger reactors | Candidate coupled reaction/separation or heat-transfer architectures; require sources and application-specific maturity. |
| Medium | Photobioreactor geometries, immobilised-cell/packed-bed culture, hollow-fibre bioreactors | Biological process catalogue currently emphasizes stirred vessels and modes. Require geometry-specific support, without making one type per organism. |
| Medium | Combustors and hydrothermal liquefaction/oxidation | Broad chemically reactive systems explicitly within the user's scope but absent from this version. Scope boundaries and architecture criteria need agreement within the catalogue, not arbitrary enumeration. |
| Review | Historical fusion configurations and alternate beam-target neutron sources | First audit whether they are genuinely new confinement/drive mechanisms or aliases/subtypes of existing mirror, cusp, pinch, FRC and electrostatic branches. The current count alone is not a completeness measure. |

## Method and limits

`audit.tsv` has one row per entry, with classification triage, source directness, access observations, issues and recommended action. `verified_source_url` contains a verified work identity or authoritative replacement identified during this audit; it does not claim that every detail of the row was verified in that source. Empty values mean no replacement was positively identified.

`sources.tsv` and `url_checks.json` cover all 56 unique original URLs plus the supplementary/replacement sources in `additional_sources.json`. The checker uses bounded GET requests, follows redirects, extracts the first five PDF pages where possible and requests Crossref titles for DOIs. It caps each response at 8 MB; a large PDF may therefore be correctly served but not text-extractable in this pass. `pdf-response-text-unavailable` is not evidence of a corrupt source. Four initial requests failed transiently; the final machine-readable files contain the latest check. Most HTML was identity/access checked, not reviewed in full.

Two DOI titles that were missed in the first automated attempt were retrieved directly from Crossref on retry: the CHS paper above and the fermentation scale-up paper at `10.1016/j.cjche.2020.12.004`. The latter is relevant background but is not a specific reference for every chemostat/perfusion/fed-batch claim.

This is an editorial/source audit, not exhaustive literature review or expert validation of 123 scientific dossiers. Remaining work: entry-level citations with exact pages/sections; named facility demonstrations for maturity; separate domains, physical configurations, operating modes and applications; then incorporate verified missing architectures. `build_audit.py` accepts the saved schema `1.0.0` URL-check envelope and the historical bare array. Reproduce the original 123-entry editorial rules without network requests:

```bash
python metadata/taxonomy_audit/build_audit.py --output-directory /tmp/atlas-taxonomy-reproduction
```

The output directory is required. The maintained `audit.tsv` now includes 135 entries, incorporating twelve later reviews; historical reproduction must not overwrite it. The producer refuses its maintained directory, output aliases to maintained files and paths that would replace either input. `--input` and `--checks` allow complete copied snapshots and observations to be reviewed separately. Malformed rows, duplicate identities, incompatible check envelopes, count mismatches and missing URL observations fail before outputs are opened. I/O failures are reported without a traceback; a failure writing the second output can leave the first output, so this pair is not an atomic transaction.

The fixed `audit_date` remains `2026-09-26`: it identifies this historical rule set and does not imply a fresh scientific review. A new `check_sources.py` run is separate network work and refreshes access observations, not scientific approval. Importing the producer performs no file reads or writes. The public `read_snapshot`, `read_checks` and `build_audit` functions are also used by the CLI.


## Producing separate access observations

The source checker now reads the schema `1.0.0` supplementary envelope and its historical bare-array form. Together with the complete original taxonomy snapshot, the recorded supplementary list produces 68 unique references; envelope keys are never treated as URLs. Importing the checker performs no input reads, executable discovery, network requests or writes.

A fresh observation run is separate from the historical editorial reproduction:

```bash
python metadata/taxonomy_audit/check_sources.py --output-directory /tmp/atlas-source-observations
python metadata/taxonomy_audit/build_audit.py --checks /tmp/atlas-source-observations/url_checks.json --output-directory /tmp/atlas-source-review
```

Both destinations are explicit and separate from maintained files. The checker protects its historical JSON/TSV observations and source inputs, including resolved output symlinks. `--input` and `--additional` select intact copied inputs; `--no-additional` checks only the original snapshot references. The output remains a schema `1.0.0` JSON envelope and a ten-column TSV, sorted by unique original reference. Failed individual transfers are recorded rather than converted into source approval. A later output I/O failure can leave the earlier output; the pair is not atomic.

Every initial reference and redirect must use anonymous HTTPS. TLS verification remains enabled; `--ca-certificate` supplies an additional trusted certificate bundle. At most six responses are followed before a redirect-limit failure. `--timeout` is the connection and per-read inactivity timeout, not a total transfer deadline. `--max-bytes` limits retained decoded response bytes (default 8,000,000); an oversized body receives `response-body-limit-exceeded` and no extracted title.

When available, the CLI resolves the real `pdftotext` executable from the trusted PATH, passes PDF bytes on standard input without a shell, restricts extraction to the first five pages and applies `--pdf-timeout` (default five seconds). Native return status and nonblank text are required for `pdf-extracted`. Missing tools, disabled extraction (`--no-pdf-text`), empty/invalid PDF text or native failures receive `pdf-response-text-unavailable`, preserving the observed HTTP status. This limits extraction scope and process duration; it does not impose a separate native-parser memory quota. The title is a 700-character excerpt, not a review of the document.

DOI references are identified by the configured resolver authority and path prefix, with case-insensitive host matching and decoded DOI paths. A DOI string embedded in an unrelated URL is not a resolver identity. `--doi-origin` and `--crossref-base` support institutional HTTPS mirrors and must be query/fragment-free prefixes. Registration requires a complete HTTP 200 JSON message identifying the same DOI and carrying nonempty text titles. DOI registration establishes work identity, not the truth of findings.

New observations use the current UTC date; `--checked-on` accepts an explicit calendar date in `YYYY-MM-DD`. The editorial producer still records its historical rule-set date, so a new access check does not silently refresh scientific review. Dedicated transport tests require native OpenSSL and pdftotext. They serve all copied recorded references over an actual local TLS socket, serialize a real five-page PDF of all 123 snapshot identities, exercise the native parser and feed generated checks into the actual editorial producer. No external source is fetched by these tests.
