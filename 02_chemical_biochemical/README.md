<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 02_chemical_biochemical/README.md
-->

# Chemical and biochemical reactor library

Curated 2026-09-26. This collection covers reactor fundamentals, ideal and non-ideal flow, heterogeneous and multiphase reactors, intensified and energy-conversion reactors, bioreactors, and process safety. It favors material that is legally public, technically reputable, and useful for engineering study. It is **not** a collection of hazardous synthesis recipes.

## Start here

1. [Chemical Reaction Engineering: From First Principles to AI-Assisted Practice](https://research.chalmers.se/publication/551551) — modern open textbook (303 pages); batch, semi-batch, CSTR, PFR/tubular, non-ideal flow, catalysis, stability, and risk analysis.
2. [MIT 10.37 reference guide](01_ideal_flow_batch_cstr_pfr/README.md) — chemical and biological reaction engineering, CSTR/PFR/batch, RTD, heat effects, catalysis, packed beds, mass transfer, and fermenters. The guide links to the original lecture notes and their historical file identities; course PDFs are held outside this repository.
3. [Membrane and Membrane Reactors Operations in Chemical Engineering](https://mdpi-res.com/bookfiles/book/1347/Membrane_and_Membrane_Reactors_Operations_in_Chemical_Engineering.pdf) — open 156-page membrane-reactor volume.
4. [Fuel Cell Handbook, Seventh Edition](https://netl.doe.gov/sites/default/files/netl-file/FCHandbook7.pdf) — DOE/NETL public handbook (427 pages).
5. `10_biochemical_fermentation_digesters/` — two EPA AgSTAR handbooks covering anaerobic-digester selection, operation, monitoring, gas handling, maintenance, and safety.
6. [Scale-Up Reaction Safety](https://drs.illinois.edu/Page/SafetyLibrary/ScaleUpReactionSafety) — public scale-up and runaway-prevention guidance.

## Folder map

- `00_fundamentals` — broad reaction-engineering texts and indexes.
- `01_ideal_flow_batch_cstr_pfr` — batch/semi-batch, CSTR, PFR/tubular, RTD, heat effects, chemostats, catalysis and packed-bed notes.
- `02_multiphase_packed_fluidized_trickle_slurry` — cataloged fixed/packed, fluidized, trickle-bed and slurry resources.
- `03_membrane_microflow` — membrane reactors, microreactors and flow chemistry.
- `04_catalysis` — catalytic-reaction references; core downloadable treatment is also in the MIT set and Andersson text.
- `05_electrochemical_fuel_cells` — electrochemical reactors, electrolyzers and fuel cells.
- `06_photo_plasma` — photochemical, photocatalytic and plasma reactors.
- `07_polymerization` — polymerization-reactor modelling, control and runaway literature.
- `08_combustion_gasification_pyrolysis` — combustion, gasification and pyrolysis references.
- `09_hydrothermal` — hydrothermal and supercritical-water reactor engineering.
- `10_biochemical_fermentation_digesters` — fermenters, fed-batch/chemostat material and anaerobic digestion.
- `11_safety_scaleup` — reaction hazard assessment, thermal runaway, scale-up, management of change and accident lessons.
- `12_catalog_paywalled` — intentionally empty; paywalled books and papers are represented as metadata-only rows in `sources.tsv`.

## Catalog conventions

`sources.tsv` is the authoritative catalog. `downloaded` means a local file was retrieved and validated by file signature. `online-only` means the source is legally readable at the URL but was not mirrored (dynamic site, access control, or to avoid duplicating large media). `paywalled-metadata` means no full text was downloaded. A local HTML file is a snapshot/landing page, not necessarily a self-contained offline website.

Commercial reactor design must be performed by qualified engineers using current codes, material-compatibility data, relief-system design, calorimetry, HAZOP/LOPA, and site-specific review. Educational equations and review papers are not construction approval.



## Document custody

Third-party research copies are retained separately in owner-controlled local
custody. This repository distributes the catalogue and checksums in
[the custody manifest](../metadata/document_custody.json), not the downloaded
works. Follow each original source URL and its publisher terms for access.
