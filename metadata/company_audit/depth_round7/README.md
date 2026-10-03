<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/company_audit/depth_round7/README.md
-->

# Fusion catalog depth audit — round 7

Audit date: **2026-09-28**

Round 7 selects the next ten unenriched records from the round-4 matrix that lack an explicit project-bounded fuel cycle or have stale/ambiguous status. Selection sorts by descending round-4 priority score, then preserves matrix order. It excludes all 19 names enriched in rounds 4–6.

## Coverage

The exact-name targets are EMC2 Fusion Development Corporation, Lockheed Martin Compact Fusion Reactor program, Marvel Fusion, Renaissance Fusion, Proxima Fusion, Gauss Fusion, First Light Fusion, OpenStar Technologies, Avalanche Energy and Princeton Fusion Systems.

Before enrichment they contained **24 gap instances**: fuel and source-date gaps for all ten, plus status and official-URL gaps for EMC2 and Lockheed. The overlays resolve/document all **24/24** instances. Project-bounded fuel wording improves from **0/10 to 10/10**, record-specific source dates from **0/10 to 10/10**, explicit status from **8/10 to 10/10**, and usable official/official-archive URLs from **8/10 to 10/10**. Resolution includes explicit negative findings and does not imply technical validation.

## Outputs

- `enrichment_overlays.tsv`: ten exact-name overlays.
- `source_registry.tsv`: thirty sources with scope/limitations.
- `gap_closure.tsv`: row-level coverage accounting.
- `build.py`, `validate.py`, `validation.json`: deterministic build and validation.

Run `python3 build.py` and then `python3 validate.py` in this directory. The producer also accepts `--gap-matrix`, `--history-directory` and `--output-directory` for isolated data copies. Its public matrix, history and closure interfaces check exact schemas, distinct identities, previous record IDs, ranking and the original ten-target selection before output writes. An incomplete bounded closure is refused; output paths cannot replace any selected source input. Validation reads persisted tables without rebuilding them. It recomputes the original deterministic selection from the round-4 matrix and round-4–6 overlays, then checks row-level closure accounting and source ownership. For data copies, use `python3 validate.py --directory /path/to/round7 --gap-matrix /path/to/round4/gap_matrix.tsv --history-directory /path/to/company_audit --report /path/to/report.json`. The report cannot replace an input; invalid inputs cannot claim verified fuel/date coverage. Metadata consistency does not establish scientific validation.

## Material findings

- EMC2 is currently active as a small simulation-led Polywell/neutron-source developer, correcting the stale dormant label. No new operating device is public.
- Lockheed Skunk Works cancelled CFR before 2021. T5 completion and results were never made public; patents do not establish continued activity.
- Marvel's near-term targets are non-cryogenic D-T; later tritium-lean chemistry is unspecified.
- Renaissance is testing HTS/liquid-metal components for a D-T stellarator but has no integrated plasma device.
- Proxima's Alpha and Stellaris are D-T projects; Alpha financing remains conditional and no company plasma device operates.
- Gauss GIGA is an integrated D-T stellarator plant design, not a reactor experiment.
- First Light's historical shots used D-D; the untested FLARE commercial cycle is D-T.
- OpenStar's published power-plant design is D-T, but Junior's gas/fuel is not explicit in the audited sources; Junior first plasma is not fusion.
- Avalanche's present Orbitron neutron experiments are D-D, while its first proposed energy system is D-T.
- PFRC-2 uses hydrogen for current research; the proposed Princeton Fusion Systems reactor/drive is D-He3.

## Evidence policy and limitations

Company claims, official archives, regulated registries, government/partner sources and scholarly publications are separately characterized. Peer review supports the reported design or experiment but is not automatically independent replication. Fuel is assigned to a named project stage, never inferred from the company family. First plasma, component testing, financing, patents and design reviews are not fusion gain. Dead or historical programmes retain archival official URLs with that limitation stated.

The Gauss GIGA citation was corrected on 2026-09-30 against the original IAEA PDF: the linked work is *World Fusion Outlook 2024*, second edition, printed p. 21. The original audit date remains 2026-09-28; this later bibliographic correction does not establish present operation or performance. The integrated company exports carry the corrected source date.

Web pages may change and the registry is not a permanent archive.
