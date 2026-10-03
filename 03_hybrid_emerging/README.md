<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 03_hybrid_emerging/README.md
-->

# Hybrid and emerging reactor research library

Curated 26 September 2026. This directory contains legally public/open material only. A catalog entry is not an endorsement. Paywalled or otherwise unavailable publications are linked in `sources.tsv` but were not copied or bypassed.

## Evidence labels used here

- **CONFIRMED PHYSICS** — independently established reaction or engineering physics. This does not imply useful net power. Examples: accelerator-driven subcritical multiplication, beam–target D–D fusion, muon-catalysed fusion, and pyroelectric ion acceleration.
- **PEER-REVIEWED, EARLY / NEEDS REPLICATION** — credible measurements with limited independent replication or immature scaling. Examples: recent very-low-energy beam–target fusion enhancement in metal hydrides.
- **NULL REPLICATION / NEGATIVE REVIEW** — an explicit failure to reproduce the claimed effect or a review finding the evidence unconvincing.
- **CONTESTED CLAIM** — positive results exist, but reproducibility, controls, interpretation, or independence remain disputed.
- **SPECULATIVE CONCEPT** — a proposal or model without an experimentally demonstrated reactor-scale result.
- **COMMERCIAL CLAIM, NOT INDEPENDENTLY VALIDATED** — vendor claims without public, independent, full-system calorimetry and nuclear-product accounting sufficient to establish net energy.

## Categories and current assessment

1. `01_fusion_fission_hybrids` — fusion neutron sources driving subcritical fission blankets. **Speculative reactor concept with established component physics.** Proposed for power, fissile breeding and waste transmutation; no integrated power plant exists. It inherits fusion-source, fission-fuel-cycle, materials, safeguards and economics challenges.
2. `02_accelerator_driven_subcritical` — accelerator + spallation target + subcritical blanket. **Confirmed component/system physics; pre-commercial.** Research facilities and subcritical experiments exist, but high-power accelerator reliability, target survivability, fuel cycles and economics remain deployment barriers.
3. `03_nuclear_renewable_process_heat` — coordinated nuclear, renewables, storage and industrial loads. **Conventional engineering integration, demonstration stage.** Includes hydrogen, desalination, district heat, synthetic fuels and flexible electricity. It should not be confused with an exotic nuclear reaction.
4. `04_thermochemical_electrochemical` — high-temperature electrolysis and hybrid thermochemical cycles coupled to nuclear/process heat. **Established chemistry; integrated commercial deployment incomplete.** Materials, corrosive intermediates, heat exchange, efficiency and cost dominate.
5. `05_solid_state_lenr_cold_fusion` — Pd–D electrolysis, metal hydrides, lattice-confinement and beam–target fusion. Keep three different claims separate:
   - Classical Fleischmann–Pons anomalous heat: **unconfirmed/contested**. DOE reviews, Google’s programme and Project Callisto did not establish reproducible cold-fusion heat.
   - Beam-, gamma- or neutron-triggered reactions in deuterated solids: **nuclear reactions confirmed in specific driven experiments**, but these are externally driven and far from net energy.
   - 2025 Thunderbird and 2026 sub-keV results: **peer-reviewed early science**. The 2025 apparatus produced about `10^-9 W` fusion-equivalent output from `15 W` input; the 2026 low-energy plateau is an enhancement over an extremely small theoretical baseline, not a power demonstration.
6. `06_muon_catalyzed` — **confirmed fusion mechanism, no energy breakeven.** Muon production cost, 2.2 μs lifetime and alpha sticking limit cycles per muon. Hybrid fission blankets can improve an energy ledger only by adding fission energy and its fuel-cycle burdens.
7. `07_pyroelectric` — **confirmed beam–target fusion/neutron-source technique, not a power reactor.** Thermal cycling of a pyroelectric crystal creates a high voltage that accelerates deuterons into a target; it consumes far more energy than fusion releases.
8. `08_cavitation_bubble` — **contested claim with strong null evidence.** The original acoustic-cavitation claim was not reproduced by a sensitive Oak Ridge test; later authorship/independence findings further weakened the claimed evidence. Do not treat sonochemistry or ordinary sonoluminescence as evidence of fusion.
9. `09_laser_phonon_nanoparticle` — mechanisms and proposed triggers (electron screening, vacancies, phonons, coherent excitation, laser stimulation and nanoparticles). **Mostly exploratory/speculative.** Project Callisto’s laser/terahertz tests found no anomalous heat; known rate-enhancement mechanisms do not by themselves demonstrate net energy.
10. `10_commercial_claims` — claims and independent critiques. **No listed company has a publicly established, independently replicated net-energy reactor.**

## Speculative and architecture-only concepts

These are included for completeness, but must not be read as demonstrated reactors:

| Concept | What is established | What remains speculative or unshown | Critical comparator in this library |
|---|---|---|---|
| Fusion-driven fission breeder / waste burner | Fusion and fission neutron physics; subcritical multiplication | An economical, maintainable integrated plant and closed fuel cycle | DOE hybrid research-needs report |
| Accelerator-driven actinide burner / energy amplifier | Accelerators, spallation and subcritical assemblies | Utility-scale availability, target life, fuel cycle and favorable economics | IAEA ADS status report |
| Muon-fusion–fission hybrid | Muon-catalysed D–T fusion and fission multiplication | A favorable full-system energy/cost ledger | NASA/CERN muon reviews and limitations in this README |
| Metal-hydride “cold-fusion” heat reactor | Hydrogen/deuterium loading chemistry | Reproducible nuclear heat without an energetic trigger | DOE, Google and Callisto null record |
| Beam–target metal-hydride reactor | D–D fusion under ion bombardment | Net energy or a scalable rate; present output is many orders below input | 2025 Nature OA text and 2026 preprint |
| Gamma/neutron-triggered lattice confinement | Triggered reactions in deuterated metals | Efficient multiplication and useful power | NASA LCF papers; their own scaling caveats |
| Phonon/coherent-excitation fusion | Lattice modes and coherent driving exist physically | Fusion-rate amplification sufficient for power | Mechanism roadmap plus Callisto terahertz/laser null tests |
| Laser-stimulated hydrides / nanoparticle targets | Laser–matter interaction and high hydrogen surface area | Reproducible anomalous nuclear heat at low input | Callisto full reports; ARPA-E programme is a test, not validation |
| Pyroelectric fusion power source | Compact high-voltage ion acceleration and fusion neutrons | Positive energy balance; explicitly excluded by the original authors | 2005 author copy and README assessment |
| Cavitation/bubble fusion reactor | Acoustic cavitation and sonoluminescence | Credible independently replicated fusion signal, much less net power | Oak Ridge null replication and critical comments |
| Nuclear-renewable “energy park” with hydrogen/synfuels | Each conventional subsystem and control concept | Optimal commercial configuration at a particular market/site | IAEA/NREL studies; scenario results are not universal |

The mechanistic review catalogs electron screening, high fuel loading, vacancies, lattice dynamics, phonons, photons, lasers and coherent excitation as research hypotheses. Large enhancement factors relative to a vanishingly small bare-nucleus rate can still leave an unusably small absolute rate. Project Callisto is the most direct critical comparator here: its thermal, laser, terahertz, electrical, pressure and electrochemical campaigns found no anomalous heat in the tested spaces.

## Cold-fusion/LENR anchor record

The two full Project Callisto reports are included, not merely the web summary. They cover more than 500 samples, over 200,000 sample-hours of calorimetry, more than 40 formal or modified Fleischmann–Pons replications, and pressures up to roughly 600 ksi. They report no anomalous heat and identify conventional explanations for most apparent anomalies. A few non-repeating unresolved observations were explicitly not treated as LENR evidence.

DOE’s 1989 review found no convincing evidence for a useful energy source and did not recommend a dedicated programme, while allowing ordinary peer-reviewed proposals. DOE’s 2004 review again found the evidence insufficient for a special programme; the public-domain scan is stored as DJVU. Google’s 2015–2019 multi-institution effort also found no cold-fusion effect. ARPA-E and DARPA materials in `programs/` document hypothesis-testing research, not confirmation of commercial LENR.

## Commercial claims: critical reading guide

- **Leonardo/E-Cat (Andrea Rossi):** published demonstrations were not independent black-box validations. The included critique identifies calorimetry and assumed-material-property problems. No public, independently replicated nuclear-product and energy balance establishes the claim.
- **Brillouin Energy:** company reports describe hydrogen/nickel systems and claimed controlled heat. Public evidence remains dependent on company-selected apparatus/data and has not established an independently replicated reactor.
- **Clean Planet:** patents, collaborations and investment demonstrate organized R&D, not proof of claimed heat-to-energy performance. Demand independent preregistered tests, raw data, controls and complete mass/nuclear-product balances.
- **ENG8 and HYLENR:** press releases, certificates or short demonstrations are not equivalent to peer-reviewed, independent replication. Treat power claims as unvalidated unless test ownership, calibration, hidden inputs, steady-state duration and isotopic/radiation products are independently audited.
- **Astral Systems:** NASA lattice-confinement work supports externally triggered nuclear reactions in deuterated metals. It does not validate commercial net power; licensing a government patent is not a performance demonstration.
- **Acceleron Fusion:** muon-catalysed fusion is real physics, but a commercial system still has to overcome muon-production energy/cost, sticking, decay and tritium-handling constraints.

## How to use the catalog

`sources.tsv` is the inventory and includes downloaded and catalog-only items. The `status` and `notes` columns carry the evidence label and explain access limitations. `SHA256SUMS` covers every local research file other than the checksum file itself. Open XML can be read in a browser or transformed locally; it was retained when a legally open publisher PDF was not directly available.

This is a research library, not design or operating guidance. Nuclear, pressure, radiation, tritium, pyrophoric-hydride and high-voltage experiments require licensed facilities and specialist safety review.


## Document custody

Third-party research copies are retained separately in owner-controlled local
custody. This repository distributes the catalogue and checksums in
[the custody manifest](../metadata/document_custody.json), not the downloaded
works. Follow each original source URL and its publisher terms for access.
