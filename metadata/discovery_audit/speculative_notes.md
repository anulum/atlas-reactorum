<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/discovery_audit/speculative_notes.md
-->

# Speculative and emerging reactor discovery notes

Audit date: 2026-09-26

This sweep complements the main reactor library. It is a discovery map, not a list of endorsed technologies and not a claim that every item is likely to become an energy-producing reactor. The catalogue intentionally puts credible negative and null results beside positive component demonstrations.

## Result

`speculative_candidates.tsv` contains 43 unique candidate/source records across:

- unconventional magnetic, electrostatic, pulsed and magneto-inertial fusion;
- aneutronic fuels and non-equilibrium plasma concepts;
- muon- and antimatter-catalysed nuclear concepts;
- contested condensed-matter and cavitation fusion claims;
- thorium, molten-salt, breed-and-burn and accelerator/fusion-driven subcritical fission systems;
- fusion-fission and nuclear-renewable hybrids;
- space-fission and fusion-propulsion concepts;
- plasma-chemical, photocatalytic, solar-thermochemical, sonochemical and bioelectrochemical reactors.

URLs and DOIs were deduplicated exactly. No large files were downloaded.

## Status vocabulary

- `theoretical`: physics or system calculations without a corresponding integrated experiment.
- `proposed`: a concept or design has been developed, but the defining integrated reactor has not been demonstrated.
- `component-demonstrated`: one or more relevant physical effects or subsystems have been observed; this must not be read as reactor feasibility.
- `system-demonstrated`: an integrated non-commercial system operated at some scale. It does not imply economic viability or, for propulsion, flight readiness.
- `theoretical-negative`: a credible analysis identifies fundamental or severe limits in the studied regime.
- `falsified-or-null`: a targeted replication or search did not confirm the reactor-relevant claim. It does not prove that every imaginable variant is impossible.

The `reactor_readiness` column separately identifies what was actually built or analysed. This prevents a detected nuclear reaction, neutron source, stable plasma, catalyst response, or individual component from being mistaken for net power, a closed fuel cycle, or a deployable plant.

## Main critical findings

### Fusion and plasma

IEC fusors are real and useful neutron sources, but this is not evidence that their electrode losses can be overcome for electricity production. Polywell experiments provide evidence for improved high-beta cusp electron confinement, while reactor-relevant ion confinement, fusion gain and recirculating power remain unverified.

Dense plasma focus, plasma oscillatory confinement, laser and other devices can produce p-B11 reactions. The reaction itself is not the disputed part. The unresolved issue is an energy-producing system after bremsstrahlung, ion-electron equilibration, driver losses, repetition, heat rejection and conversion are counted. Rider-type constraints and the newer p-B11 bremsstrahlung analyses are included precisely to balance positive reaction-yield papers.

Magnetic mirrors, FRCs, spheromaks, levitated dipoles, MagLIF and magnetized-target variants all have genuine experimental plasma programmes. Their entries are marked component-level unless an integrated energy system exists. No entry in the fusion subset is evidence of commercial reactor readiness.

### Catalysed and low-energy nuclear claims

Muon-catalysed fusion is experimentally established nuclear physics, but making muons consumes too much energy and muon sticking/decay limits catalytic cycles. Antiproton-catalysed microfission/fusion remains a propulsion concept dominated by antimatter production and storage barriers.

The 2019 multi-laboratory cold-fusion programme found no Fleischmann-Pons effect. The 2025 palladium result is categorised separately because an external ion beam caused the fusion and electrochemical loading modestly enhanced its rate; it is not spontaneous room-temperature fusion and did not produce net energy.

For sonofusion, the catalogue uses the direct Oak Ridge replication that found no correlated fusion-neutron signal and constrained any possible emission far below the original interpretation. This avoids amplifying later promotional summaries without reproducible evidence.

### Fission and hybrids

Thorium is a fuel-cycle option, not a reactor type or automatic solution to waste, proliferation, materials and economics. Molten-salt operation has historical experimental precedent, but a modern thorium breeder with online processing and a qualified commercial materials/safeguards system has not operated.

Accelerator-driven and fusion-driven subcritical systems rest on known neutron physics and demonstrated components. Their central challenges are integrated availability, target and materials lifetime, remote fuel handling, separations, licensing and cost. Fusion-fission hybrids inherit substantial requirements from both parent technologies.

Traveling-wave/breed-and-burn systems have serious neutronic and engineering design work behind them but no operating representative power reactor. Nuclear-renewable hybrids are less speculative scientifically: their uncertainty is mainly system integration and economics.

### Chemical, photonic and biological reactors

These are included because “reactor” spans energy-conversion systems beyond nuclear devices. Their status should not be compared directly with fusion gain:

- The 100 m2 photocatalytic water-splitting array is a real scale demonstration, but its reported peak solar-to-hydrogen efficiency was 0.76% and the whole system was energy-negative.
- Solar-thermochemical ceria reactors and a solar-tower kerosene chain have operated; durability, heat recovery, efficiency and cost remain scale-up questions.
- Plasma CO2 conversion and plasma-catalytic ammonia synthesis are experimentally established, but published performance can be distorted by inconsistent mass balances and energy-efficiency definitions.
- Sonochemical hydrogen production is measurable yet far less energy-efficient than electrolysis in the cited controlled study.
- Microbial fuel/electrolysis cells can recover energy or products during treatment, but power density, electrode cost, fouling and adverse scaling limit bulk energy use.

## Search and selection method

Searches emphasized English-language primary experiments, government/national-laboratory reports, DOI records and peer-reviewed critical assessments. Sources from APS, AIP, Nature, IAEA-adjacent literature, NASA NTRS, OSTI, INL, ORNL and established journals were preferred. A review was used when it was the clearest authoritative status source or when a concept spans many small experiments.

Candidate inclusion required both reactor relevance and at least one citable technical source. A company press release, patent, crowdfunding page, unsourced performance claim or news story alone was not enough. Commercial authorship is flagged implicitly in the assessment where it materially affects interpretation.

## Limitations

- The sweep is broad but not exhaustive. English-first searching underrepresents Russian, Chinese, Japanese and other national programmes.
- Search indexing is uneven for old conference proceedings, technical reports, discontinued programmes and papers behind paywalls.
- Private fusion and advanced-reactor companies often publish selectively; absence of public evidence is not proof of no internal progress, but it cannot support a positive readiness rating.
- Preprints are labelled and should not be treated as peer-reviewed confirmation.
- Publication dates returned by modernized archives can reflect page migration rather than the original report date; the table uses the underlying work's stated year where identifiable.
- The audit does not cover every patent, vendor design, isotope-production device, conventional electrolysis reactor or ordinary chemical reactor.
- Status labels summarise the cited evidence as of the audit date and may change with independent replication or new integrated demonstrations.
- No attempt was made to collect operating parameters, sensitive nuclear design details or instructions for constructing radiation-producing apparatus.

## Recommended interpretation

For any candidate, ask four separate questions:

1. Was the underlying physical or chemical effect observed independently?
2. Was the defining confinement, catalyst, target, core or conversion component demonstrated at relevant conditions?
3. Was a complete energy and material balance measured, including driver and recirculating power?
4. Was an integrated system operated with credible lifetime, maintainability, safety and economics?

Most misleading “reactor breakthrough” claims answer only the first question and imply all four.
