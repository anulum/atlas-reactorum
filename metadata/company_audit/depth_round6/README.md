<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/company_audit/depth_round6/README.md
-->

# Fusion catalog depth audit — round 6

Audit date: **2026-09-28**

Round 6 enriches the next ten highest-priority active reactor/device developers in the round-4 matrix after excluding all nine identities overlaid in rounds 4–5. All eligible records were tied at priority score 5; the deterministic selection preserves round-4 matrix/source-row order.

## Selection

The exact-name targets are Helion Energy, General Fusion, Tokamak Energy, Zap Energy, Type One Energy, Thea Energy, Realta Fusion, Pacific Fusion, Xcimer Energy and Focused Energy. Their round-4 gaps were `fuel_cycle;source_date`.

## Outputs

- `enrichment_overlays.tsv`: 10 non-destructive exact-name overlays.
- `source_registry.tsv`: 30 primary, government, national-laboratory, utility and scholarly sources, each with limitations.
- `gap_closure.tsv`: deterministic before/after closure report.
- `build.py`, `validate.py`, `validation.json`: reproducible generation and structural validation.

Run `python3 build.py` and then `python3 validate.py` in this directory. The producer accepts `--gap-matrix` and `--output-directory` for isolated data copies. Its public `read_matrix` and `build_closures` interfaces validate the complete previous schema, ten unique targets, matching record IDs, score 5 and exactly the two fuel/date gaps before any output write. Both enriched fields must be documented; retained limitations do not become scientific validation. Output paths cannot replace the selected previous matrix. Validation reads persisted inputs without rebuilding them. It checks the exact round-4 record IDs, score-5 fuel/date gaps, source associations and bounded closures. For data copies, use `python3 validate.py --directory /path/to/round6 --gap-matrix /path/to/round4/gap_matrix.tsv --report /path/to/report.json`; reports cannot overwrite inputs. These checks establish metadata consistency, not scientific validation.

## Evidence rules

Fuel is assigned per device or project, not per company by analogy. A present hydrogen/deuterium engineering experiment is not relabeled D-T because a future plant uses D-T. Conversely, D-T tests do not prove a closed commercial fuel cycle. Host devices (WHAM), partner/national-laboratory hardware (Sirius), and predecessor public results (NIF) are explicitly separated from company-owned achievements.

Company pages and issuer filings establish disclosed status and claims. Government roadmaps, registries and partner pages corroborate programme identity and hardware relationships but not plasma performance. Peer review supports the reported experiment or design; it is not necessarily independent replication. Negative findings are retained where public evidence does not establish fuel, operation, gain or electricity.

## Findings

- Helion distinguishes Polaris D-D/D-T/D-He3 testing from its prospective D-He3 commercial cycle; current Polaris performance remains company-reported.
- General Fusion's filing says LM26 uses hydrogen as a proxy, while its commercial design is D-T with lithium-based breeding.
- ST40 uses hydrogen/deuterium; Tokamak Energy's ST-E1 plant route is D-T.
- Zap's FuZE physics devices use deuterium, while Century deliberately uses non-fusing protium/helium; Century repetition is not repetitive fusion.
- Type One's Infinity Two is D-T; no sufficiently explicit operating fuel was found for the not-yet-operating Infinity One.
- Thea's Eos is D-D and Helios is D-T; Canis coil tests are hardware, not fusion.
- WHAM uses deuterium and is a UW–Realta public-private platform; Realta's planned first plant is D-T.
- Pacific Fusion's Sirius is a resistive-load pulser with no fusion fuel; its planned system is D-T.
- Xcimer's Phoenix is an operating laser platform, not a fuelled fusion device; later capsule systems are D-T.
- Focused Energy's Pearl targets are D-T; NIF ignition cannot be attributed to the company.

## Counts and limitations

This directory contains **10 overlays**, **30 source entries**, and **10 closure rows**. Both original gap labels are closed for all ten records by exact, project-bounded fuel wording and record-specific dates. “Closed” means documented, including explicit negative findings; it does not mean a technical claim is validated. No integrated catalog or presentation code is modified.
