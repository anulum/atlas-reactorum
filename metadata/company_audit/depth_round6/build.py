#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/depth_round6/build.py
"""Build deterministic depth-round-6 overlays for ten exact-name targets."""

from __future__ import annotations

import argparse
import csv
from collections.abc import Mapping, Sequence
from pathlib import Path

HERE = Path(__file__).resolve().parent
R4 = HERE.parent / "depth_round4" / "gap_matrix.tsv"
DATE = "2026-09-28"
MATRIX_FIELDS = [
    "record_id",
    "source_catalog",
    "source_row",
    "organization",
    "country",
    "identity_class",
    "normalized_status",
    "approach_configuration",
    "named_devices_projects",
    "fuel_cycle",
    "highest_independently_supported_milestone",
    "unsupported_or_ambiguous_claims",
    "official_url",
    "independent_sources",
    "source_dates",
    "confidence",
    "evidence_tier",
    "status_completeness",
    "identity_completeness",
    "approach_completeness",
    "device_completeness",
    "fuel_cycle_completeness",
    "milestone_completeness",
    "unsupported_claims_completeness",
    "official_url_completeness",
    "independent_source_completeness",
    "source_date_completeness",
    "country_completeness",
    "confidence_completeness",
    "gap_count",
    "priority_score",
    "priority_band",
    "gap_fields",
]

FIELDS = [
    "organization",
    "match_rule",
    "source_record_id",
    "fields_enriched",
    "enriched_status",
    "enriched_approach_configuration",
    "enriched_named_devices_projects",
    "enriched_fuel_cycle",
    "enriched_highest_independently_supported_milestone",
    "enriched_unsupported_or_ambiguous_claims",
    "enriched_official_url",
    "enriched_independent_urls",
    "source_ids",
    "source_dates",
    "audit_date",
    "confidence",
    "overlay_note",
]
COMMON = "normalized_status;approach_configuration;named_devices_projects;fuel_cycle;highest_independently_supported_milestone;unsupported_or_ambiguous_claims;official_url;independent_urls;source_dates"
ROWS = [
    [
        "Helion Energy",
        "exact normalized organization name",
        "AUD-003",
        COMMON,
        "active; Polaris operating and Orion site work announced",
        "pulsed magneto-inertial fusion; colliding field-reversed configurations; direct electrical energy recovery",
        "Trenta (sixth prototype); Polaris (seventh prototype, operating); Orion (commercial plant project/site work)",
        "Polaris test programme: D-D, D-T and D-He3; long-term commercial cycle: D-He3 with He3 intended to be produced from D-D products and tritium decay",
        "Independent literature supports operation of multiple pulsed FRC prototypes through Trenta. Current Polaris operation and 2026 D-T/temperature results are company-reported and expert-commented, not an independently published diagnostic dataset; no independent net-electricity result is public.",
        "Polaris D-T yield and 150 million C, electricity recovery, closed fuel-cycle sufficiency, Orion schedule and commercial output remain company claims or prospective; expert quotations in a company release are not independent replication.",
        "https://www.helionenergy.com/",
        "https://www.frontiersin.org/articles/10.3389/fenrg.2023.1157394/full; https://iea.blob.core.windows.net/assets/d24ccc77-ef68-491c-848d-b9c0ec0c484b/TheStateofEnergyInnovation2026.pdf",
        "H01;H02;H03",
        "Polaris page accessed 2026-09-28; Helion result release 2026-02-13; Frontiers review 2023-05-03",
        "2026-09-28",
        "high for status/fuel; medium for current performance",
        "Fuel stages are not conflated: D-T testing does not make D-T the stated commercial cycle, and D-He3 commercial viability is unproven.",
    ],
    [
        "General Fusion",
        "exact normalized organization name",
        "AUD-004",
        COMMON,
        "active public company; LM26 operating demonstration programme",
        "magnetized-target fusion; mechanically compressed magnetized plasma with liquid-lithium liner",
        "LM26 / Lawson Machine 26 operating since 2025; earlier Pi3 plasma injector; future Fusion Island plant concept",
        "LM26 milestone tests use hydrogen plasma as an engineering proxy; commercial plant design is D-T with tritium breeding in a lithium-bearing liquid-metal wall",
        "A 2026 SEC filing records LM26 construction, operation and plasma compressions and reports approximately 0.72 keV electron temperature. This is regulated public-company disclosure, not independent metrology; earlier subsystem physics is peer reviewed. No Lawson criterion or net energy is established.",
        "LM26 1 keV/10 keV/Lawson targets, company temperature analysis, commercial D-T breeding sufficiency, repetition rate, electricity and 2030s schedule remain disclosed goals or company results unless separately peer reviewed.",
        "https://generalfusion.com/",
        "https://www.sec.gov/Archives/edgar/data/2074850/000110465926106033/gfuz-20260630xf1.htm; https://www.ukaea.org/news/ukaea-supports-diverse-paths-to-fusion-energy/",
        "G01;G02;G03",
        "SEC F-1 period ended 2026-06-30 / filed 2026-09; company research library accessed 2026-09-28; UKAEA 2025-01-16",
        "2026-09-28",
        "high for device/status/fuel; medium for reported performance",
        "SEC disclosure is primary issuer evidence with legal accountability, not an independent experiment.",
    ],
    [
        "Tokamak Energy",
        "exact normalized organization name",
        "AUD-005",
        COMMON,
        "active; ST40 operating and under 2026 upgrade; Demo4 testing continuing",
        "high-field spherical tokamak with HTS magnets",
        "ST40 operating research tokamak; Demo4 HTS magnet system; ST-E1 pre-concept power plant; participation in FAST is separate partner project",
        "ST40 presently uses hydrogen/deuterium plasmas; ST-E1 and the company's commercial plant route are D-T with tritium breeding required",
        "DOE/national-laboratory reporting and a peer-reviewed paper support ST40 deuterium-plasma ion temperatures around 100 million C in short pulses. UK government reporting supports continuing ST40 upgrades and Demo4 magnet tests. This is not D-T operation or gain.",
        "ST-E1 performance and timing, D-T operation, breeding, net power, and company descriptions of later ST40/Demo4 records remain prospective or not independently metrologically detailed in the cited public sources.",
        "https://tokamakenergy.com/",
        "https://www.energy.gov/science/fes/articles/small-fusion-experiment-hits-temperatures-hotter-suns-core; https://www.gov.uk/government/publications/uk-fusion-strategy-2026/a-new-energy-revolution-the-uks-plan-for-delivering-fusion-energy-accessible-webpage",
        "T01;T02;T03",
        "official ST40 update 2026-07-29; DOE 2023-05-12; UK strategy 2026-03",
        "2026-09-28",
        "high",
        "Explicitly separates ST40 deuterium experiments from the D-T commercial design.",
    ],
    [
        "Zap Energy",
        "exact normalized organization name",
        "AUD-006",
        COMMON,
        "active; FuZE-Q physics and Century engineering platforms operating",
        "sheared-flow-stabilized Z pinch; pulsed magnetic confinement",
        "FuZE and FuZE-Q fusion-physics devices; Century repetitive power-handling platform; later Millennium/Demo/Pilot roadmap entries",
        "FuZE/FuZE-Q experiments use deuterium for D-D neutron studies; Century uses non-fusing protium or helium; intended power-plant cycle is D-T",
        "Peer-reviewed FuZE work supports thermonuclear-neutron interpretation, while DOE-reviewed Century operation supports 1,080 shots over three hours in a flowing-liquid-metal environment. Century intentionally did not use fusion fuel and is not a fusion-yield milestone.",
        "Company-reported later FuZE-Q neutron yields, breakeven trajectory, future D-T performance, gain and plant economics are not independently validated here. Century repetition must not be described as repetitive fusion.",
        "https://www.zapenergy.com/",
        "https://arpa-e.energy.gov/news-and-events/news-and-insights/arpa-e-investor-update-vol-23-zap-energys-fusion-power-plant-demo; https://doi.org/10.1080/15361055.2025.2532331",
        "Z01;Z02;Z03",
        "Century DOE-certification release 2025-02-25; ARPA-E 2024-06-13; peer-reviewed Century paper 2025",
        "2026-09-28",
        "high",
        "Device-specific fuels prevent the non-fusing Century platform from being mistaken for a D-T reactor demonstration.",
    ],
    [
        "Type One Energy",
        "exact normalized organization name",
        "AUD-007",
        COMMON,
        "active; Infinity One in procurement/development, not yet commissioned",
        "optimized stellarator with non-planar HTS magnets",
        "Infinity One engineering verification/workforce platform planned at TVA Bull Run; Infinity Two D-T pilot-plant design; no operating company stellarator",
        "Infinity Two is explicitly a D-T burning-plasma design with breeder blanket; Infinity One's operating fuel is not stated clearly enough in current public material to assign",
        "TVA independently confirms the Infinity One project and site partnership. A 2025 peer-reviewed special issue provides a self-consistent physics and tritium-cycle design basis for Infinity Two. These are project and design milestones; no Type One plasma device is operating.",
        "Infinity One 2029 startup, unspecified test fuel, Infinity Two 800 MW fusion/400 MWe, D-T burn, tritium self-sufficiency and 2034 grid schedule remain prospective design claims.",
        "https://typeoneenergy.com/",
        "https://www.tva.com/energy/fusion; https://doi.org/10.1017/S0022377825000297",
        "O01;O02;O03",
        "official technology page accessed 2026-09-28; TVA page accessed 2026-09-28; Journal of Plasma Physics special issue 2025-03-24",
        "2026-09-28",
        "high for project/design; medium for schedule",
        "Negative finding retained: no exact public operating fuel for Infinity One was found, so Infinity Two's D-T cycle is not transferred to it.",
    ],
    [
        "Thea Energy",
        "exact normalized organization name",
        "AUD-008",
        COMMON,
        "active; Eos remains a designed/future integrated device; Canis coil-array hardware tested",
        "software-controlled planar-coil quasi-axisymmetric stellarator",
        "Canis 3x3 HTS planar-coil array tested; Eos D-D neutron-source stellarator planned; Helios D-T pilot-plant concept",
        "Eos is explicitly D-D; Helios/power-plant route is explicitly D-T",
        "Peer-reviewed/technical publications document nine-coil Canis operation at 20 K with closed-loop field control and published Eos physics design. DOE selection supports the milestone programme. No integrated Eos plasma device is publicly evidenced as operating.",
        "Eos construction, D-D neutron and tritium-production rates, Helios confinement/gain, D-T operation and power remain modeled or prospective; coil tests are not a fusion milestone.",
        "https://thea.energy/",
        "https://www.energy.gov/articles/us-department-energy-announces-selectees-107-million-fusion-innovation-research-engine; https://doi.org/10.1088/1741-4326/ada56a",
        "A01;A02;A03",
        "Eos page accessed 2026-09-28; DOE selectees 2025-01-16; Nuclear Fusion publication 2025-01-28",
        "2026-09-28",
        "high for fuel/design; medium-high for hardware state",
        "Eos and Helios fuels are recorded separately; no operating Eos is inferred from completed coil hardware.",
    ],
    [
        "Realta Fusion",
        "exact normalized organization name",
        "AUD-009",
        COMMON,
        "active; WHAM public-private experiments ongoing; Anvil is future company demonstration system",
        "high-field axisymmetric magnetic mirror with HTS magnets; direct-energy-conversion research",
        "WHAM (UW-Madison-owned public-private platform); Anvil future demonstration system; Hammir-DD/Hammir-DT roadmap concepts",
        "WHAM current experiments use deuterium; first-generation power plant is D-T; advanced fuels are only a longer-term possibility",
        "UW-Madison independently confirms WHAM operation as a university/Realta public-private platform. A 2026 company demonstration converted a portion of exhaust/input plasma power to electricity on WHAM and explicitly did not show net electricity or fusion-born power conversion.",
        "The 2026 direct-conversion result is company-reported; Anvil construction, D-T gain, net electricity, advanced-fuel use and commercial schedules remain prospective. WHAM is not solely a Realta-owned device.",
        "https://realtafusion.com/",
        "https://www.physics.wisc.edu/newsletter/newsletter-2024.pdf; https://www.energy.gov/documents/fusion-science-and-technology-roadmap",
        "R01;R02;R03",
        "Realta demonstration 2026-06-30; UW report 2024; DOE roadmap 2026-06",
        "2026-09-28",
        "high for current fuel/platform; medium for company demonstration",
        "Ownership and energy origin are bounded: the converted energy was mostly injected heating power, not demonstrated fusion electricity.",
    ],
    [
        "Pacific Fusion",
        "exact normalized organization name",
        "AUD-010",
        COMMON,
        "active; Sirius pulsed-power prototype exceeded 3,000 shots; New Mexico fusion facility construction announced",
        "pulsed magnetic inertial fusion using impedance-matched Marx-generator pulsed power",
        "Sirius four-stage pulser at LLNL; planned Demonstration System / net-facility-gain machine in New Mexico",
        "planned fusion system is D-T according to company technical material; Sirius fires into a resistive load and has no fusion fuel",
        "LLNL independently reports more than 3,000 Sirius shots and identifies the 60 GW, 100 ns pulsed-power prototype partnership. This validates repetitive driver hardware, not target implosion, fusion yield or gain.",
        "Demonstration System construction schedule, D-T target performance, net facility gain, economics and power-plant scalability remain prospective. Sirius electrical efficiency into a resistive load is not fusion efficiency.",
        "https://www.pacificfusion.com/",
        "https://lift.llnl.gov/llnl-pacific-fusion-partnership-advances-next-generation-pulsed-power-technology; https://www.energy.gov/documents/fusion-science-and-technology-roadmap",
        "P01;P02;P03",
        "company/LLNL Sirius releases 2026-07-16; DOE roadmap 2026-06",
        "2026-09-28",
        "high",
        "Negative finding: no Pacific Fusion target implosion or fusion shot is established by the current driver milestone.",
    ],
    [
        "Xcimer Energy",
        "exact normalized organization name",
        "AUD-011",
        COMMON,
        "active; Phoenix laser prototype began operations in June 2026",
        "laser inertial fusion using electron-beam-pumped KrF excimer lasers and SBS pulse compression",
        "Phoenix operating laser prototype; Anvil planned beamline; Vulcan planned high-yield facility; Athena planned power plant",
        "future fusion stages use D-T capsules with a tritium-breeding plant cycle; Phoenix is a laser/optics platform and uses no fusion fuel",
        "Current company evidence establishes end-to-end Phoenix laser operation above 1 kJ. DOE documents independently establish funded excimer-driver development and list Phoenix in the national roadmap. Phoenix has not driven a fusion capsule; no company fusion yield is established.",
        "Phoenix superlatives and detailed performance are company-reported; Anvil/Vulcan/Athena energy, D-T gain, tritium self-sufficiency, wall-plug gain, electricity and dates are prospective.",
        "https://xcimer.energy/",
        "https://stage.energy.gov/nepa/articles/cx-270844-xcimer-energy-inc-hybrid-pumped-excimer-laser-hyper-laser; https://www.energy.gov/documents/fusion-science-and-technology-roadmap",
        "X01;X02;X03",
        "Phoenix start-of-operations 2026-06-03; DOE NEPA 2025-09-19; DOE roadmap 2026-06",
        "2026-09-28",
        "high for laser state; medium for company performance",
        "Fuel applies to future capsule stages, not Phoenix. NIF ignition cannot be attributed to Xcimer.",
    ],
    [
        "Focused Energy",
        "exact normalized organization name",
        "AUD-012",
        COMMON,
        "active; target, laser and proton-fast-ignition development; no integrated fusion device operating",
        "direct-drive laser inertial fusion with proton fast ignition; current branding also describes LightHouse architecture and Pearl targets",
        "Pearl D-T fuel capsule; LightHouse modular laser-fusion architecture; sub-scale test facilities and pilot plant remain planned",
        "explicit D-T fuel capsules; proposed tritium supply/breeding details are not sufficiently public to claim a closed cycle",
        "DOE documentation independently confirms the proton-fast-ignition pilot-plant programme, target design and subscale facility work; peer-reviewed literature documents the design approach. Company milestones include proton-focusing experiments, not an integrated D-T implosion or company ignition.",
        "NIF ignition/gain belongs to LLNL, not Focused Energy. Pearl 30x output, integrated ignition, target gain above 100, pilot-plant performance, tritium cycle and electricity remain modeled or prospective.",
        "https://www.focused-energy.co/",
        "https://www.energy.gov/nepa/articles/cx-030451-inertial-fusion-energy-high-gain-proton-fast-ignition; https://doi.org/10.1007/s10894-023-00363-x",
        "F01;F02;F03",
        "official technology page accessed 2026-09-28; DOE NEPA 2024-04-12; Journal of Fusion Energy 2023-07-03",
        "2026-09-28",
        "high for fuel/approach; medium-high for milestone",
        "Current official domain is focused-energy.co, replacing the stale focused-energy.world catalog URL.",
    ],
]

SF = [
    "source_id",
    "organization",
    "title",
    "publisher",
    "source_type",
    "source_date",
    "url",
    "scope_and_limitations",
    "accessed_on",
]
SOURCES = [
    [
        "H01",
        "Helion Energy",
        "Polaris",
        "Helion Energy",
        "company primary",
        "accessed 2026-09-28",
        "https://www.helionenergy.com/polaris",
        "Device, test fuels and commercial D-He3 cycle; all performance is company-described.",
    ],
    [
        "H02",
        "Helion Energy",
        "2026 fusion milestones",
        "Helion Energy",
        "company primary",
        "2026-02-13",
        "https://www.helionenergy.com/newsroom/helion-achieves-new-fusion-energy-milestones",
        "Current Polaris D-T and temperature claims; no public independent diagnostic paper.",
    ],
    [
        "H03",
        "Helion Energy",
        "Progress toward fusion energy breakeven and gain",
        "Frontiers in Energy Research",
        "scholarly review",
        "2023-05-03",
        "https://www.frontiersin.org/articles/10.3389/fenrg.2023.1157394/full",
        "Independent context through Trenta; predates Polaris results.",
    ],
    [
        "G01",
        "General Fusion",
        "General Fusion Group F-1",
        "U.S. SEC EDGAR",
        "regulated issuer filing",
        "2026-09",
        "https://www.sec.gov/Archives/edgar/data/2074850/000110465926106033/gfuz-20260630xf1.htm",
        "LM26 state, hydrogen test fuel and D-T commercial design; issuer statements are not independent metrology.",
    ],
    [
        "G02",
        "General Fusion",
        "Research library",
        "General Fusion",
        "company primary",
        "accessed 2026-09-28",
        "https://generalfusion.com/research-library/",
        "Public technical papers and LM26 materials; company-curated.",
    ],
    [
        "G03",
        "General Fusion",
        "UKAEA supports diverse paths to fusion energy",
        "UKAEA",
        "government partner",
        "2025-01-16",
        "https://www.ukaea.org/news/ukaea-supports-diverse-paths-to-fusion-energy/",
        "Programme recognition; not current LM26 performance validation.",
    ],
    [
        "T01",
        "Tokamak Energy",
        "ST40 heating-system site tests",
        "Tokamak Energy",
        "company primary",
        "2026-07-29",
        "https://tokamakenergy.com/2026/07/29/power-plant-heating-system-passes-tokamak-energy-site-testing/",
        "Current ST40 upgrade state; gyrotron test is not plasma performance.",
    ],
    [
        "T02",
        "Tokamak Energy",
        "Small fusion experiment hits temperatures hotter than Sun core",
        "U.S. DOE",
        "government research summary",
        "2023-05-12",
        "https://www.energy.gov/science/fes/articles/small-fusion-experiment-hits-temperatures-hotter-suns-core",
        "National-lab-supported peer-reviewed ST40 deuterium result; short non-gain pulses.",
    ],
    [
        "T03",
        "Tokamak Energy",
        "UK Fusion Strategy 2026",
        "UK Government",
        "government strategy",
        "2026-03",
        "https://www.gov.uk/government/publications/uk-fusion-strategy-2026/a-new-energy-revolution-the-uks-plan-for-delivering-fusion-energy-accessible-webpage",
        "Current ST40 and Demo4 programme state; promotional case study partly company supplied.",
    ],
    [
        "Z01",
        "Zap Energy",
        "DOE certifies Zap technical milestone",
        "Zap Energy",
        "company primary reporting DOE review",
        "2025-02-25",
        "https://www.zapenergy.com/updates/2025/02/doe-certifies-zap-energy-fusion-technology-milestone",
        "Century endurance and non-fusing fuel; company release about DOE review.",
    ],
    [
        "Z02",
        "Zap Energy",
        "ARPA-E investor update: Zap demo",
        "ARPA-E",
        "government programme report",
        "2024-06-13",
        "https://arpa-e.energy.gov/news-and-events/news-and-insights/arpa-e-investor-update-vol-23-zap-energys-fusion-power-plant-demo",
        "Independent programme context for Century/FuZE; no gain validation.",
    ],
    [
        "Z03",
        "Zap Energy",
        "Century repetitive SFS Z-pinch system",
        "Fusion Science and Technology",
        "peer-reviewed journal",
        "2025",
        "https://doi.org/10.1080/15361055.2025.2532331",
        "Century design and commissioning; explicitly nonreacting hydrogen, not fusion.",
    ],
    [
        "O01",
        "Type One Energy",
        "Our technology",
        "Type One Energy",
        "company primary",
        "accessed 2026-09-28",
        "https://typeoneenergy.com/our-technology/",
        "Infinity One/Two state and D-T design; schedules and outputs prospective.",
    ],
    [
        "O02",
        "Type One Energy",
        "Fusion",
        "Tennessee Valley Authority",
        "independent utility partner",
        "accessed 2026-09-28",
        "https://www.tva.com/energy/fusion",
        "Confirms Bull Run Infinity One partnership; not construction or performance validation.",
    ],
    [
        "O03",
        "Type One Energy",
        "Infinity Two physics basis",
        "Journal of Plasma Physics",
        "peer-reviewed design series",
        "2025-03-24",
        "https://doi.org/10.1017/S0022377825000297",
        "Peer-reviewed plant design basis; no operating device.",
    ],
    [
        "A01",
        "Thea Energy",
        "Eos",
        "Thea Energy",
        "company primary",
        "accessed 2026-09-28",
        "https://thea.energy/eos/",
        "Explicit Eos D-D and D-T plant context; device remains planned.",
    ],
    [
        "A02",
        "Thea Energy",
        "DOE FIRE milestone selectees",
        "U.S. DOE",
        "government programme",
        "2025-01-16",
        "https://www.energy.gov/articles/us-department-energy-announces-selectees-107-million-fusion-innovation-research-engine",
        "Independent milestone-programme selection/review; not Eos operation.",
    ],
    [
        "A03",
        "Thea Energy",
        "Eos stellarator design",
        "Nuclear Fusion",
        "peer-reviewed design paper",
        "2025-01-28",
        "https://doi.org/10.1088/1741-4326/ada56a",
        "Peer-reviewed modeled design; no integrated plasma result.",
    ],
    [
        "R01",
        "Realta Fusion",
        "Direct energy conversion demonstration",
        "Realta Fusion",
        "company primary",
        "2026-06-30",
        "https://realtafusion.com/fusion-first-realta-demos-direct-energy-conversion/",
        "Explicitly bounds result as mostly input-power recovery, not net fusion electricity.",
    ],
    [
        "R02",
        "Realta Fusion",
        "UW Physics research highlights",
        "University of Wisconsin-Madison",
        "university source",
        "2024",
        "https://www.physics.wisc.edu/newsletter/newsletter-2024.pdf",
        "Confirms WHAM public-private operation; university-owned platform context.",
    ],
    [
        "R03",
        "Realta Fusion",
        "Fusion Science and Technology Roadmap",
        "U.S. DOE",
        "government roadmap",
        "2026-06",
        "https://www.energy.gov/documents/fusion-science-and-technology-roadmap",
        "Device roadmap and names; participant-submitted timelines are not validation.",
    ],
    [
        "P01",
        "Pacific Fusion",
        "Sirius 3,000-shot campaign",
        "Pacific Fusion",
        "company primary",
        "2026-07-16",
        "https://www.pacificfusion.com/resources/lawrence-livermore-pacific-fusion-collaboration-breaks-new-record-to-advance-america-s-high-gain-fusion-capability",
        "Driver milestone; resistive-load shots, no fusion.",
    ],
    [
        "P02",
        "Pacific Fusion",
        "LLNL-Pacific Fusion partnership",
        "Lawrence Livermore National Laboratory LIFT",
        "national laboratory",
        "2026-07-16",
        "https://lift.llnl.gov/llnl-pacific-fusion-partnership-advances-next-generation-pulsed-power-technology",
        "Independent confirmation of Sirius campaign; no fusion target result.",
    ],
    [
        "P03",
        "Pacific Fusion",
        "Fusion Science and Technology Roadmap",
        "U.S. DOE",
        "government roadmap",
        "2026-06",
        "https://www.energy.gov/documents/fusion-science-and-technology-roadmap",
        "Confirms programme placement; company-submitted timeline.",
    ],
    [
        "X01",
        "Xcimer Energy",
        "Phoenix starts operations",
        "Xcimer Energy",
        "company primary",
        "2026-06-03",
        "https://xcimer.energy/news/xcimer-energy-announces-the-start-of-operations-for-phoenix-a-prototype-system-for-industrial-scale-laser-fusion-architecture/",
        "Phoenix laser claims; no capsule or fusion shot.",
    ],
    [
        "X02",
        "Xcimer Energy",
        "HYPER-LASER NEPA determination",
        "U.S. DOE",
        "government project record",
        "2025-09-19",
        "https://stage.energy.gov/nepa/articles/cx-270844-xcimer-energy-inc-hybrid-pumped-excimer-laser-hyper-laser",
        "Independent funded driver-development scope; not Phoenix performance.",
    ],
    [
        "X03",
        "Xcimer Energy",
        "Fusion Science and Technology Roadmap",
        "U.S. DOE",
        "government roadmap",
        "2026-06",
        "https://www.energy.gov/documents/fusion-science-and-technology-roadmap",
        "Phoenix-to-Athena roadmap; participant timelines are not validation.",
    ],
    [
        "F01",
        "Focused Energy",
        "Technology",
        "Focused Energy",
        "company primary",
        "accessed 2026-09-28",
        "https://www.focused-energy.co/technology",
        "Current LightHouse/Pearl naming and D-T fuel; output claims prospective.",
    ],
    [
        "F02",
        "Focused Energy",
        "CX-030451 proton fast ignition",
        "U.S. DOE",
        "government project record",
        "2024-04-12",
        "https://www.energy.gov/nepa/articles/cx-030451-inertial-fusion-energy-high-gain-proton-fast-ignition",
        "Independent programme scope, target and facility design; not ignition result.",
    ],
    [
        "F03",
        "Focused Energy",
        "Focused Energy: a new approach toward inertial fusion energy",
        "Journal of Fusion Energy",
        "peer-reviewed design paper",
        "2023-07-03",
        "https://doi.org/10.1007/s10894-023-00363-x",
        "Scholarly design roadmap; no integrated company fusion device.",
    ],
]


CLOSURE_FIELDS = [
    "organization",
    "source_record_id",
    "round4_priority_score",
    "round4_gap_fields",
    "fields_closed",
    "remaining_negative_findings",
    "round6_disposition",
    "audit_date",
]


def read_matrix(path: Path) -> dict[str, dict[str, str]]:
    """Read an intact previous matrix without collapsing duplicate identities.

    Parameters
    ----------
    path : pathlib.Path
        Previous depth4 matrix with its original producer schema.

    Returns
    -------
    dict of dict
        Matrix rows indexed by exact original organization name.

    Raises
    ------
    ValueError
        If schema, row shape, presence or identity uniqueness is invalid.
    """
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != MATRIX_FIELDS:
            raise ValueError("previous matrix header mismatch")
        rows = list(reader)
    if not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError("previous matrix empty or malformed")
    old = {row["organization"]: row for row in rows}
    if len(old) != len(rows) or any(not name.strip() for name in old):
        raise ValueError("previous matrix duplicate or blank identities")
    return old


def build_closures(
    overlays: Sequence[Sequence[str]], old: Mapping[str, Mapping[str, str]]
) -> list[list[str]]:
    """Derive ten documented fuel/date closures from their previous identities.

    Parameters
    ----------
    overlays : sequence of sequences of str
        Complete reviewed rows in FIELDS order.
    old : mapping of str to mappings
        Previous depth4 matrix indexed by exact organization name.

    Returns
    -------
    list of list of str
        Closure rows in CLOSURE_FIELDS order, preserving negative findings.

    Raises
    ------
    ValueError
        If row shape, targets, previous identities or declared gaps differ.
    """
    if any(len(row) != len(FIELDS) for row in overlays):
        raise ValueError("overlay row shape mismatch")
    names = [row[0] for row in overlays]
    if len(names) != 10 or len(set(names)) != 10:
        raise ValueError("expected ten unique overlay targets")
    if any(name not in old for name in names):
        raise ValueError("previous matrix missing overlay target")
    if any(
        old[row[0]]["record_id"] != row[2]
        or old[row[0]]["priority_score"] != "5"
        or old[row[0]]["gap_fields"] != "fuel_cycle;source_date"
        for row in overlays
    ):
        raise ValueError("previous target identity, score5 or fuel/date gaps mismatch")
    if any(not {"fuel_cycle", "source_dates"} <= set(row[3].split(";")) for row in overlays):
        raise ValueError("overlay must document both fuel_cycle and source_dates")
    return [
        [
            row[0],
            row[2],
            old[row[0]]["priority_score"],
            old[row[0]]["gap_fields"],
            "fuel_cycle;source_date",
            row[16],
            "closed with bounded evidence and retained claim limits",
            DATE,
        ]
        for row in overlays
    ]


def write(path: Path, fields: list[str], rows: list[list[str]]) -> None:
    """Serialize deterministic curated rows without altering their claim limits.

    Parameters
    ----------
    path : pathlib.Path
        Output TSV in the selected directory.
    fields : list of str
        Ordered producer schema.
    rows : list of lists of str
        Reviewed or derived rows in producer order.
    """
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(fields)
        writer.writerows(rows)


def main() -> None:
    """Validate previous evidence and derive all closures before writing outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap-matrix", type=Path, default=R4)
    parser.add_argument("--output-directory", type=Path, default=HERE)
    args = parser.parse_args()
    if args.gap_matrix.resolve() in {
        (args.output_directory / name).resolve()
        for name in ("enrichment_overlays.tsv", "source_registry.tsv", "gap_closure.tsv")
    }:
        print("BUILD FAILED: output would replace previous matrix")
        raise SystemExit(1)
    try:
        closures = build_closures(ROWS, read_matrix(args.gap_matrix))
        args.output_directory.mkdir(parents=True, exist_ok=True)
        write(args.output_directory / "enrichment_overlays.tsv", FIELDS, ROWS)
        write(args.output_directory / "source_registry.tsv", SF, [[*row, DATE] for row in SOURCES])
        write(args.output_directory / "gap_closure.tsv", CLOSURE_FIELDS, closures)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"BUILD FAILED: {error}")
        raise SystemExit(1) from None
    print(f"wrote {len(ROWS)} overlays, {len(SOURCES)} sources and {len(closures)} closure rows")


if __name__ == "__main__":
    main()
