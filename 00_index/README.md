<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — catalogue index
-->

# Reactor Research Library

Counts below describe the current retained catalogue tables and integrated bundles. Source acquisition and review dates remain per record; these counts do not establish current facility operation or document availability.

## Snapshot results

- **249** bibliographic records in the three primary source catalogues: 108 nuclear, 100 chemical/biochemical and 41 hybrid/emerging. The separate taxonomy citation registry contains 148 sources.
- The [document manifest](../metadata/document_custody.json) records **113 historical document identities**: 108 PDFs and five other captures. The repository carries names, source references and checksums; the manifest alone does not prove present document availability or redistribution rights.
- A discovery audit with **68** additional bibliographic/data candidates, **43** speculative-technology records and a fusion-company landscape expanded from **51 to 98 audited candidates**.
- An integrated map dataset with **1,823 unit-level nuclear-power records** across 62 countries/areas, a separate historical **195-plant** WRI layer, **172 research reactors**, **174 dated IAEA FFDB catalogue records**, and **11,086** explicitly scoped industrial facility/site or process-project records.
- An English-first interactive atlas with **135** indexed architectures, subtypes, operating modes and integration concepts: 29 fission, 32 fusion, 52 chemical/biochemical and 22 hybrid/emerging entries. Categories overlap; the total is not a count of mutually exclusive physical principles.
- After merging one exact supplemental duplicate, the interactive views load **13,459 records**, of which **13,357 have coordinates**, plus **98 audited company/programme records**. FFDB records remain separate from supplemental context. Record types overlap: a power plant can coexist with its individual units, and most industrial-site or planning-project records do not identify individual reactor vessels.
- A dated GitHub metadata catalog now exposes **30 public ANULUM reactor-ecosystem repositories**: 22 device-family architectures, two shared physics/kernel repositories, four control/integration repositories and two supporting hardware/compute repositories.
- A [coverage ledger](COVERAGE_LEDGER.md) tracks research requirements; hosted publication remains separately reviewed.

Start with the [interactive presentation](../04_interactive_presentation/index.html), browse the [merged source catalog](../metadata/all_sources.tsv), or inspect the [validation report](../metadata/validation_report.txt).

This library is a broad, evidence-oriented collection covering three families of reactors:

1. **Nuclear reactors** — fission, fusion, research, advanced, small and accelerator-assisted systems.
2. **Chemical and biochemical reactors** — ideal and industrial reactor classes, catalytic, electrochemical, photochemical, plasma, flow and biological systems.
3. **Hybrid and emerging reactors** — coupled energy systems, fusion-fission hybrids, solid-state fusion, LENR/cold-fusion claims and related experimental concepts.

## Directory map

- `01_nuclear/` — nuclear fission and mainstream fusion technologies.
- `02_chemical_biochemical/` — chemical, electrochemical and biological reactor engineering.
- `03_hybrid_emerging/` — hybrid systems and emerging or contested concepts.
- `04_interactive_presentation/` — an English-first, offline-capable interactive presentation.
- `05_global_reactor_map/` — schema, provenance registry and map-ready facility/project data.
- `metadata/` — merged machine-readable catalogs and validation summaries.
  This includes the company evidence audit and the refreshable ANULUM GitHub repository catalog.

The three research-library sections contain their own `README.md`, `sources.tsv`, source-reference catalogues and `SHA256SUMS`; document bodies stay in separate local custody. The presentation and map directories document their own data and deployment formats.

## Completeness boundary

This is a curated research snapshot, not a claim to contain every publication or every physical reactor in existence. The discovery audit records search methods, unresolved gaps and additional bibliographic candidates. Coverage is strongest where authoritative public registries exist. The new EEA/EPA industrial layer is a geographically and regulatorily bounded site inventory, not a global equipment census; industrial chemical and biochemical installations remain heavily undercounted.

The global map keeps three objects separate: physical facilities, reactor types, and proposals or claims. A GitHub repository, company announcement, patent or catalog entry establishes that a project or claim exists; it does not by itself validate scientific performance or commercial readiness.

The generated field-level backlog is in `../metadata/coverage_audit/COVERAGE.md`, with machine-readable country, dataset and record-kind breakdowns in `coverage.json`. Missing fields are research targets and are never filled by inference.

## Access policy

Only legally public or open-access full texts are stored. Paywalled or otherwise unavailable publications are represented by metadata, DOI and an official landing-page URL. Inclusion in the catalog does not imply scientific endorsement.

## Evidence labels

- **Established:** independently reproduced and consistent with accepted science.
- **Active research:** credible research with unresolved engineering or scientific questions.
- **Contested:** published claims without adequate independent replication.
- **Null/critical:** replication, review or assessment reporting negative results or methodological problems.
- **Speculative:** proposal or model without convincing experimental validation.

## Safety

The collection is for research and education. Reactor construction, operation, pressure systems, radiation sources, fissile materials, reactive chemistry and biological cultivation require appropriate facilities, licensing, hazard analysis and qualified personnel.
