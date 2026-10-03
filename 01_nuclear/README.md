<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 01_nuclear/README.md
-->

# Nuclear reactor and plasma-fusion research library

Curated on 2026-09-26. This section contains 54 source records: 39 locally downloaded public PDFs (about 412 MiB) and 15 catalogued web/DOI records. The emphasis is authoritative, legal public access and broad technical orientation, not detailed operating or construction instructions.

## How to use the catalogue

`sources.tsv` is the source of truth. Its columns are:

- `category`: reactor family or cross-cutting subject
- `title`, `year`, `authors_or_org`: bibliographic description
- `url`: official or repository source (a DOI is retained for paywalled material)
- `local_file`: relative path when a copy was downloaded
- `access`: `open-fulltext`, `open-web`, `open-article`, or `paywalled-or-record`
- `status`: `downloaded` or `catalogued`
- `notes`: scope and access qualifications

`SHA256SUMS` authenticates every downloaded file plus the catalogue and this README. Verify it from this directory with `sha256sum -c SHA256SUMS`.

## Fission coverage

- `00_overviews`: technology-neutral assessment and comparative plant-design terminology.
- `01_fission_light_water`: PWR/BWR concepts and passive safety.
- `02_fission_heavy_water`: CANDU/PHWR textbook and public training-library links in the catalogue.
- `03_fission_gas_graphite`: GCR/AGR/HTGR context and historical RBMK safety analysis.
- `04_fission_fast`: sodium-, lead/lead-bismuth-, and gas-cooled fast systems and fuel-cycle proceedings.
- `05_fission_molten_salt`: MSR status plus liquid-metal/molten-salt coolant challenges.
- `06_fission_htgr_vhtr`: HTGR/VHTR and coated-particle fuel technology.
- `07_research_reactors`: utilization, safety and international experience.
- `08_smr_microreactors`: current IAEA SMR/microreactor survey and design catalogue.
- `09_generation_iv`: GIF roadmap for GFR, LFR, MSR, SFR, SCWR and VHTR.
- `10_ads`: accelerator-driven subcritical systems, facilities and benchmarks.

## Plasma-fusion coverage

The fusion material is deliberately split by confinement method and by plant-enabling technology.

### Magnetic confinement

- `11_fusion_tokamak`: tokamak power-plant studies and the current ITER engineering basis.
- `12_fusion_stellarator`: stellarator physics, the US research-opportunities report and recent W7-X/European-program records.
- `14_fusion_alternatives`: field-reversed configurations (FRC), spheromaks and associated compact-toroid literature; Z-pinch and magnetized-target references are also catalogued.
- `16_fusion_heating_current_drive`: neutral-beam, ion-cyclotron, electron-cyclotron and radiofrequency heating/current-drive references.
- `17_fusion_diagnostics_control`: PPPL material on spectroscopy, electron-cyclotron emission and pilot-plant diagnostic constraints.

### Inertial confinement

- `13_fusion_inertial`: IAEA inertial-fusion reference material and selected modern ignition/review records. Z-pinch-driven inertial fusion and magnetized-liner concepts are cross-referenced in `sources.tsv`.

### Cross-cutting reactor technology

- `15_fusion_crosscutting`: the 750-page IAEA *Fundamentals of Magnetic Fusion Technology*, DOE long-range planning and broad international status material.
- `18_fusion_materials_plasma_facing`: catalogue entries for UKAEA/EUROfusion reviews of plasma-facing, structural, blanket, diagnostic and magnet materials.
- `19_fusion_tritium_fuel_cycle`: D-T burn fraction, breeding, inventories, processing, self-sufficiency and current technology mapping.
- `20_fusion_readiness_safety`: IAEA technology-readiness criteria for fusion components.

## Evidence and readiness caveat

The library distinguishes three different things that are often blurred together:

1. **Established plasma physics:** plasma production, heating, confinement and diagnostics are experimentally mature fields, although performance varies strongly by configuration and regime.
2. **Burning-plasma experiments:** ITER and inertial-confinement facilities investigate regimes relevant to self-heating and fusion gain; they are not commercial generating stations.
3. **Reactor and power-plant readiness:** plasma-facing materials, neutron damage, maintainability, tritium breeding/self-sufficiency, fuel processing, heat extraction, reliability and economics remain separate engineering challenges. IAEA TECDOC-2047 is included specifically to keep scientific results distinct from component/system TRL.

Conceptual plant papers are useful for assumptions and research priorities, but they are not evidence that a commercially deployable reactor exists. Vendor-supplied entries in the IAEA SMR catalogue are likewise identified as design descriptions rather than independent performance validation.

## Selection and access policy

Priority was given to IAEA, NRC, US DOE/FESAC, ITER, PPPL, UKAEA/EUROfusion, GIF and university or national-laboratory repositories. Open full texts were downloaded only from public publisher/institutional endpoints. No paywall, login, robots control or access restriction was bypassed. When a stable legal full text was not confirmed, only a DOI or official landing page was catalogued.

Historical RBMK material is included for safety and design-history study. This collection intentionally omits sensitive facility-security information and is not a substitute for licensed engineering standards, regulator-approved safety analysis, operator training, or site procedures.

## Validation

At finalization, all 39 local `.pdf` files were identified as PDF documents and passed a structural parse with `pdfinfo`. URLs can change after collection; consult `sources.tsv` and the publisher landing page if a link later moves.


## Document custody

Third-party research copies are retained separately in owner-controlled local
custody. This repository distributes the catalogue and checksums in
[the custody manifest](../metadata/document_custody.json), not the downloaded
works. Follow each original source URL and its publisher terms for access.
