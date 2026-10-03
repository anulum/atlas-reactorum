#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/depth_round7/build.py
"""Build deterministic depth-round-7 exact-name overlays."""

from __future__ import annotations

import argparse
import csv
from collections.abc import Mapping, Sequence
from pathlib import Path

H = Path(__file__).resolve().parent
R4 = H.parent / "depth_round4" / "gap_matrix.tsv"
DATE = "2026-09-28"
F = [
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
BASE = "normalized_status;approach_configuration;named_devices_projects;fuel_cycle;highest_independently_supported_milestone;unsupported_or_ambiguous_claims;official_url;independent_urls;source_dates"
ROWS = [
    [
        "EMC2 Fusion Development Corporation",
        "exact normalized organization name",
        "AUD-048",
        BASE,
        "active as a small simulation-led Polywell developer; hardware programme shifted to design/simulation and neutron-source proposals",
        "Polywell magnetic-cusp confinement with electrostatic ion acceleration",
        "historical WB-8 and WB-X experimental devices; next device called WB-11 is proposed; current high-flux neutron-source and PIC-modeling programmes",
        "near-term neutron-source/power route: D-T; company survey lists later D-He3 and p-B11 stages; no current fueled WB-11 experiment",
        "The official site and 2025 FIA survey establish current organizational activity, simulation work and neutron-source proposals. Peer-reviewed historical work supports high-beta cusp experiments on prior WB hardware. No new operating device or current neutron yield is independently documented.",
        "The 1,000x neutron-flux, WB-11, reactor performance, D-T gain and advanced-fuel stages are designs/company claims; active web and survey presence do not establish hardware operation.",
        "https://www.emc2fusion.com/",
        "https://www.fusionindustryassociation.org/wp-content/uploads/2025/07/2025-Global-Fusion-Industry-Report.pdf; https://doi.org/10.1103/PhysRevX.5.021024",
        "E01;E02;E03",
        "official site accessed 2026-09-28; FIA report 2025-07; Physical Review X 2015-06-11",
        "2026-09-28",
        "high for current identity/status; medium for programme; low for performance",
        "Corrects dormant classification but does not treat a simulation/proposal programme as an operating reactor.",
    ],
    [
        "Lockheed Martin Compact Fusion Reactor program",
        "exact normalized organization name",
        "AUD-049",
        BASE,
        "cancelled; Skunk Works halted the CFR effort before 2021, publicly confirmed in 2023",
        "high-beta magnetic cusp/mirror compact-reactor concept",
        "T4/T4B experiment; T5 was announced under construction in 2019 but completion/result is not public; later T6-T8/TX were roadmap concepts",
        "historical development roadmap: T7 deuterium plasma and eventual T8/TX D-T reactor; public evidence does not establish fueled T5 operation",
        "Lockheed official archival material and patents establish the CFR concept and experimental programme. Aviation Week independently reports executive confirmation that the effort was cancelled before 2021. No public T5 result, D-T operation or integrated reactor milestone was found.",
        "T5 completion, plasma parameters, T6-TX construction, 100 MW output, compact sizing and D-T reactor performance were never publicly demonstrated. An active patent is not evidence of an active programme.",
        "https://www.lockheedmartin.com/en-us/who-we-are/business-areas/aeronautics/skunkworks/insideskunkworks.html",
        "https://aviationweek.com/defense/aircraft-propulsion/skunk-works-halted-nuclear-fusion-effort-2021; https://patents.google.com/patent/US9934876B2/en",
        "L01;L02;L03",
        "official archival page accessed 2026-09-28; cancellation report 2023-08-29; patent granted 2018-04-03 / maintenance 2025-11-03",
        "2026-09-28",
        "high for cancellation; medium for historical hardware; low for performance",
        "Official URL is archival programme content, not a current product page.",
    ],
    [
        "Marvel Fusion",
        "exact normalized organization name",
        "AUD-013",
        BASE,
        "active; laser, target, neutron-source and demonstrator development; no integrated fusion device operating",
        "laser-driven inertial fusion; hollow-shell fast ignition using nanostructured conversion targets",
        "Colorado laser/target demonstrator under development; staged industrial lasers and neutron source precede target-gain demonstrator",
        "near-term non-cryogenic D-T targets with liquid blanket for heat capture/tritium breeding; later tritium-lean fuel is unspecified",
        "Current official sources establish a funded laser/target development programme and named facility partnerships. Independent government/academic ecosystem sources corroborate the demonstrator project. No Marvel-driven ignition, target gain or reactor-scale fusion result is public.",
        "NIF ignition belongs to LLNL, not Marvel. Target gain, non-cryogenic D-T performance, tritium-lean cycle, blanket self-sufficiency and power-plant performance remain prospective.",
        "https://www.marvelfusion.com/",
        "https://www.ukaea.org/wp-content/uploads/2026/04/ukaea-global-fusion-guide-smes.pdf; https://www.energy.gov/documents/fusion-science-and-technology-roadmap",
        "M01;M02;M03",
        "technology page accessed 2026-09-28; UKAEA guide 2026-04; DOE roadmap 2026-06",
        "2026-09-28",
        "high for status/fuel; medium for facility state",
        "Fuel is bounded to the current roadmap; the later tritium-lean chemistry is not guessed.",
    ],
    [
        "Renaissance Fusion",
        "exact normalized organization name",
        "AUD-014",
        BASE,
        "active; enabling-hardware and industrial-partnership phase; integrated stellarator remains prospective",
        "simplified high-field stellarator using directly deposited HTS coils and thick flowing liquid-metal wall",
        "Nicola100 HTS magnet/700 C liquid-metal combined test; engraved-copper stellarator-field demonstration; future high-field stellarator demonstrator",
        "D-T reactor cycle; lithium-based liquid wall intended to breed/extract tritium; current magnet/liquid-metal tests are unfueled",
        "Company publications and a peer-reviewed blanket paper support component tests and modeled D-T breeding/shielding. A September 2026 DIFFER/VDL agreement supports active industrialization work. No integrated plasma device or fusion result is established.",
        "10 T net-energy stellarator, tritium-breeding sufficiency, Li-tritide extraction at plant scale, electricity and schedule remain designs or company projections.",
        "https://renfusion.eu/",
        "https://doi.org/10.1016/j.jnucmat.2024.155239; https://iea.blob.core.windows.net/assets/23af92ae-0cd4-4e6c-a06b-957b0688f0ed/TheStateofEnergyInnovation2026.pdf",
        "R01;R02;R03",
        "official milestone page accessed 2026-09-28; Journal of Nuclear Materials 2024; IEA report 2026",
        "2026-09-28",
        "high for status/fuel/components; medium for integration",
        "Component validation is not represented as a fusion-device milestone.",
    ],
    [
        "Proxima Fusion",
        "exact normalized organization name",
        "AUD-015",
        BASE,
        "active; Stellarator Model Coil manufacturing; Alpha preparation conditional on additional public funding",
        "quasi-isodynamic high-field stellarator with HTS magnets",
        "Stellarator Model Coil planned for 2027 test; Alpha D-T net-gain demonstrator planned near IPP Garching; Stellaris power-plant concept at Gundremmingen",
        "Alpha and Stellaris are D-T; Stellaris includes a modeled water-cooled lead-lithium breeding blanket; Alpha needs tritium inventory but is not intended to breed its own",
        "IPP independently confirms the 2026 Alpha partnership, financing status and that federal funding remains uncommitted. Peer-reviewed Stellaris work supports an integrated design basis. No company plasma device is operating.",
        "SMC 2027 test, Alpha construction/early-2030s Q>1, Stellaris grid date, blanket TBR above one and electricity are prospective; financing and an MOU are not technical validation.",
        "https://www.proximafusion.com/",
        "https://www.ipp.mpg.de/2026-proxima-411mio; https://doi.org/10.1016/j.fusengdes.2024.114161",
        "P01;P02;P03",
        "official pages 2026-02-26 and accessed 2026-09-28; IPP 2026-07-08; Stellaris paper 2024",
        "2026-09-28",
        "high for status/fuel/project; medium for design",
        "Alpha and Stellaris are separated; no construction or gain is inferred from financing.",
    ],
    [
        "Gauss Fusion",
        "exact normalized organization name",
        "AUD-016",
        BASE,
        "active; conceptual design review complete and engineering phase begun; no company fusion device",
        "integrated gigawatt-class stellarator power-plant engineering",
        "GIGA conceptual power-plant design; subsystem/magnet prototypes planned; no integrated experimental device",
        "D-T power-plant cycle with tritium breeding blanket/fuel-cycle systems; current design work is unfueled",
        "IPP hosted the March 2026 conceptual-design review and the IAEA World Fusion Outlook lists GIGA as a private plant concept. This supports an active, reviewed design programme, not an operating machine.",
        "1 GWe/3 GW fusion output, 2040s operation, magnet performance, D-T burn, tritium self-sufficiency and plant economics remain design targets.",
        "https://gauss-fusion.com/",
        "https://www.ipp.mpg.de/events/44906/5018228; https://www-pub.iaea.org/MTCD/Publications/PDF/p15777-24-02766E_WFO_web.pdf",
        "G01;G02;G03",
        "official site accessed 2026-09-28; IPP review 2026-03-13; IAEA World Fusion Outlook 2024 (printed p. 21)",
        "2026-09-28",
        "high for status/design/fuel; low for performance",
        "Identity is power-plant architect/integrator; no plasma milestone is claimed.",
    ],
    [
        "First Light Fusion",
        "exact normalized organization name",
        "AUD-017",
        BASE,
        "active; pivoted to FLARE fuel-system/IP and partnership-led reactor architecture; corporate registry active",
        "two-stage inertial fusion: low-power compression plus fast ignition using FLARE amplified targets",
        "historical Machine 3 and deuterium gas-gun target campaign; FLARE target/fuel-system design; future partner-built demonstrator/reactor",
        "historical validation shots used D-D targets; FLARE commercial target uses D-T with natural-lithium breeding blanket proposed",
        "An independent 2022 review found limited evidence consistent with D-D neutrons in historical impact shots. UK government and Companies House sources confirm current FLARE activity and active company status. No FLARE ignition, D-T shot or gain is public.",
        "Government strategy performance language is a company-provided case study. FLARE target gain up to 1,000, TBR 1.8, reactor economics, D-T burn and net electricity remain modeled/company claims.",
        "https://firstlightfusion.com/",
        "https://www.gov.uk/government/publications/uk-fusion-strategy-2026/a-new-energy-revolution-the-uks-plan-for-delivering-fusion-energy-accessible-webpage; https://find-and-update.company-information.service.gov.uk/company/07555858",
        "F01;F02;F03",
        "technology page accessed 2026-09-28; UK strategy 2026-03; Companies House statement 2026-03-08",
        "2026-09-28",
        "high for status/fuel; medium for historical neutron evidence",
        "Historical D-D experiments are not conflated with the untested D-T FLARE power cycle.",
    ],
    [
        "OpenStar Technologies",
        "exact normalized organization name",
        "AUD-019",
        BASE,
        "active; Junior commissioned/first plasma; Tahi facility in preparation with New Zealand government loan support",
        "levitated-dipole magnetic confinement",
        "Junior prototype commissioned with first plasma; Tahi next device/facility in requirements/site phase; later Maui/power-plant studies",
        "Junior working gas/fuel is not explicitly established in cited public records; published commercial levitated-dipole plant design is D-T",
        "New Zealand government records independently confirm Junior first plasma and preparatory work for Tahi while labeling the pathway high risk. Company technical resources show peer-reviewed Junior design/results and a 2026 D-T plant study. No fusion reaction from Junior is documented.",
        "First plasma is not fusion. Junior fuel, temperature/confinement claims, Tahi construction, D-T plant performance, gain and electricity remain undisclosed or prospective.",
        "https://www.openstar.tech/",
        "https://www.mbie.govt.nz/dmsdocument/31872-regional-infrastructure-fund-investing-in-the-openstar-fusion-energy-research-and-development-project-proactiverelease-pdf; https://www.beehive.govt.nz/release/government-backs-fusion-energy-research",
        "O01;O02;O03",
        "official technical resources accessed 2026-09-28; MBIE paper 2026-01-07; ministerial release 2026-02-04",
        "2026-09-28",
        "high for status/device; medium for plant fuel; low for Junior fuel",
        "Explicit negative finding: no project-bounded Junior fuel was located, so D-T is assigned only to the published power-plant design.",
    ],
    [
        "Avalanche Energy",
        "exact normalized organization name",
        "AUD-020",
        BASE,
        "active as Avalanche Fusion; Orbitron experimental and beam-development work continues",
        "crossed-field electrostatic ion confinement with magnetron electron confinement; beam-target/ion-ion fusion",
        "Orbitron experimental devices and neutron-source work; first energy-extraction system remains prospective",
        "current neutron experiments use deuterium/D-D; first proposed energy-extraction system is D-T with thermal conversion; other fuel claims are not treated as demonstrated",
        "APS conference records and a 2024 peer-reviewed device paper support deuterium-ion confinement and neutron-producing Orbitron experiments. These do not establish bulk thermonuclear plasma, gain or electricity.",
        "5-100 kW cells, commercial D-T operation, beam-target versus embedded-target neutron fractions, gain, direct conversion and compact shielding remain unresolved or prospective.",
        "https://www.avalanchefusion.com/",
        "https://meetings-archive.aps.org/dpp/2024/gp12/114; https://doi.org/10.1063/5.0201470",
        "A01;A02;A03",
        "official Orbitron page accessed 2026-09-28; APS contribution 2024-10-09; AIP Advances paper 2024-08-20",
        "2026-09-28",
        "high for current experiment/fuel; medium for neutron interpretation",
        "Corrects official domain and separates present D-D experiments from the proposed D-T power stage.",
    ],
    [
        "Princeton Fusion Systems",
        "exact normalized organization name",
        "AUD-022",
        BASE,
        "active as Princeton Satellite Systems doing business as Princeton Fusion Systems; current work includes RF amplifiers while PFRC-2 remains a PPPL research device",
        "odd-parity rotating-magnetic-field-heated field-reversed configuration",
        "PFRC-2 at PPPL; proposed PFRC-3; PFRC-4 reactor/Direct Fusion Drive concepts",
        "PFRC-2 training/development material specifies hydrogen fuel; proposed PFRC reactor/drive cycle is D-He3; PFRC-3 fuel is not clearly fixed publicly",
        "PPPL confirms the PFRC research device and a 2025 peer-reviewed company paper confirms continuing fusion RF-control work. Peer-reviewed reactor papers support the D-He3 concept. No PFRC fusion-power experiment is public.",
        "PFRC-3 funding/construction, ion-temperature scaling, PFRC-4 100 kW, D-He3 supply, gain, propulsion and commercial deployment remain proposed. PFRC-2 is PPPL hardware, not solely company owned.",
        "https://www.princetonfusionsystems.com/",
        "https://www.pppl.gov/Princeton-Field-Reversed-Configuration; https://doi.org/10.1080/15361055.2025.2540212",
        "Q01;Q02;Q03",
        "official material accessed 2026-09-28; PPPL page accessed 2026-09-28; Fusion Science and Technology 2025-10-02",
        "2026-09-28",
        "medium-high",
        "Fuel is device-bounded: present hydrogen research is not represented as D-He3 fusion operation.",
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
S = [
    [
        "E01",
        "EMC2 Fusion Development Corporation",
        "Home / technology / history",
        "EMC2 Fusion",
        "company primary",
        "accessed 2026-09-28",
        "https://www.emc2fusion.com/",
        "Current activity and roadmap; self-reported.",
    ],
    [
        "E02",
        "EMC2 Fusion Development Corporation",
        "Global Fusion Industry Report 2025",
        "Fusion Industry Association",
        "participant survey",
        "2025-07",
        "https://www.fusionindustryassociation.org/wp-content/uploads/2025/07/2025-Global-Fusion-Industry-Report.pdf",
        "Current identity/fuel response; not performance validation.",
    ],
    [
        "E03",
        "EMC2 Fusion Development Corporation",
        "High-energy electron confinement in magnetic cusp configuration",
        "Physical Review X",
        "peer-reviewed experiment",
        "2015-06-11",
        "https://doi.org/10.1103/PhysRevX.5.021024",
        "Historical cusp experiment; does not establish current hardware or gain.",
    ],
    [
        "L01",
        "Lockheed Martin Compact Fusion Reactor program",
        "Inside Skunk Works compact fusion archive",
        "Lockheed Martin",
        "official historical archive",
        "accessed 2026-09-28",
        "https://www.lockheedmartin.com/en-us/who-we-are/business-areas/aeronautics/skunkworks/insideskunkworks.html",
        "Official historical programme statements; not current status.",
    ],
    [
        "L02",
        "Lockheed Martin Compact Fusion Reactor program",
        "Skunk Works halted nuclear fusion effort before 2021",
        "Aviation Week",
        "independent trade reporting",
        "2023-08-29",
        "https://aviationweek.com/defense/aircraft-propulsion/skunk-works-halted-nuclear-fusion-effort-2021",
        "Executive-confirmed cancellation; article may require subscription.",
    ],
    [
        "L03",
        "Lockheed Martin Compact Fusion Reactor program",
        "US9934876B2 magnetic field plasma confinement",
        "Google Patents / USPTO data",
        "patent registry",
        "granted 2018-04-03; maintained 2025-11-03",
        "https://patents.google.com/patent/US9934876B2/en",
        "Concept ownership/legal history; patent status is not programme activity.",
    ],
    [
        "M01",
        "Marvel Fusion",
        "Technology",
        "Marvel Fusion",
        "company primary",
        "accessed 2026-09-28",
        "https://www.marvelfusion.com/technology",
        "Current fuel/roadmap claims; no independent performance.",
    ],
    [
        "M02",
        "Marvel Fusion",
        "Global Fusion Guide for SMEs",
        "UKAEA",
        "government ecosystem guide",
        "2026-04",
        "https://www.ukaea.org/wp-content/uploads/2026/04/ukaea-global-fusion-guide-smes.pdf",
        "Independent company/programme context; not technical validation.",
    ],
    [
        "M03",
        "Marvel Fusion",
        "Fusion Science and Technology Roadmap",
        "U.S. DOE",
        "government roadmap",
        "2026-06",
        "https://www.energy.gov/documents/fusion-science-and-technology-roadmap",
        "Programme infrastructure context; participant timelines.",
    ],
    [
        "R01",
        "Renaissance Fusion",
        "Technology and milestones",
        "Renaissance Fusion",
        "company primary",
        "accessed 2026-09-28",
        "https://renfusion.eu/technology",
        "Component milestones/fuel claims; self-reported.",
    ],
    [
        "R02",
        "Renaissance Fusion",
        "Compact fusion blanket using liquid Li-LiH walls",
        "Journal of Nuclear Materials",
        "peer-reviewed design",
        "2024",
        "https://doi.org/10.1016/j.jnucmat.2024.155239",
        "Modeled blanket; no integrated device.",
    ],
    [
        "R03",
        "Renaissance Fusion",
        "The State of Energy Innovation 2026",
        "International Energy Agency",
        "independent intergovernmental report",
        "2026",
        "https://www.iea.org/reports/the-state-of-energy-innovation-2026",
        "Company/funding context; no performance validation.",
    ],
    [
        "P01",
        "Proxima Fusion",
        "About / Alpha and Stellaris roadmap",
        "Proxima Fusion",
        "company primary",
        "accessed 2026-09-28",
        "https://www.proximafusion.com/about",
        "Current project state and claims.",
    ],
    [
        "P02",
        "Proxima Fusion",
        "Proxima raises EUR411m",
        "Max Planck IPP",
        "independent research partner",
        "2026-07-08",
        "https://www.ipp.mpg.de/2026-proxima-411mio",
        "Confirms partnership/financing dependencies; not construction.",
    ],
    [
        "P03",
        "Proxima Fusion",
        "Stellaris design point",
        "Fusion Engineering and Design",
        "peer-reviewed design",
        "2024",
        "https://doi.org/10.1016/j.fusengdes.2024.114161",
        "Design basis; no operating device.",
    ],
    [
        "G01",
        "Gauss Fusion",
        "GIGA and fuel-cycle overview",
        "Gauss Fusion",
        "company primary",
        "accessed 2026-09-28",
        "https://gauss-fusion.com/",
        "Current design/fuel statements; company claims.",
    ],
    [
        "G02",
        "Gauss Fusion",
        "Overview of conceptual design review",
        "Max Planck IPP",
        "independent institutional event",
        "2026-03-13",
        "https://www.ipp.mpg.de/events/44906/5018228",
        "Confirms completed design-review phase; not hardware performance.",
    ],
    [
        "G03",
        "Gauss Fusion",
        "World Fusion Outlook 2024",
        "IAEA",
        "intergovernmental report",
        "2024",
        "https://www-pub.iaea.org/MTCD/Publications/PDF/p15777-24-02766E_WFO_web.pdf",
        "Printed p. 21 describes Gauss GIGA as a prospective plant; underlying plans remain developer supplied. Edition independently checked on 2026-09-30.",
    ],
    [
        "F01",
        "First Light Fusion",
        "Technology: FLARE",
        "First Light Fusion",
        "company primary",
        "accessed 2026-09-28",
        "https://firstlightfusion.com/technology/",
        "Explicit FLARE D-T fuel and architecture; prospective.",
    ],
    [
        "F02",
        "First Light Fusion",
        "UK Fusion Strategy 2026",
        "UK Government",
        "government strategy / company case study",
        "2026-03",
        "https://www.gov.uk/government/publications/uk-fusion-strategy-2026/a-new-energy-revolution-the-uks-plan-for-delivering-fusion-energy-accessible-webpage",
        "Confirms current programme; performance language supplied by company.",
    ],
    [
        "F03",
        "First Light Fusion",
        "Company overview",
        "UK Companies House",
        "government registry",
        "statement 2026-03-08",
        "https://find-and-update.company-information.service.gov.uk/company/07555858",
        "Active legal status only.",
    ],
    [
        "O01",
        "OpenStar Technologies",
        "Technical resources and Junior status",
        "OpenStar Technologies",
        "company primary / papers index",
        "accessed 2026-09-28",
        "https://www.openstar.tech/technical-resources",
        "Current publications/device claims; Junior fuel not explicit.",
    ],
    [
        "O02",
        "OpenStar Technologies",
        "RIF investment paper",
        "New Zealand MBIE",
        "government due-diligence record",
        "2026-01-07",
        "https://www.mbie.govt.nz/dmsdocument/31872-regional-infrastructure-fund-investing-in-the-openstar-fusion-energy-research-and-development-project-proactiverelease-pdf",
        "Confirms Junior/Tahi status and risk; redactions limit detail.",
    ],
    [
        "O03",
        "OpenStar Technologies",
        "Government backs fusion research",
        "New Zealand Government",
        "ministerial release",
        "2026-02-04",
        "https://www.beehive.govt.nz/release/government-backs-fusion-energy-research",
        "Confirms loan/facility support; not performance validation.",
    ],
    [
        "A01",
        "Avalanche Energy",
        "Orbitron",
        "Avalanche Fusion",
        "company primary",
        "accessed 2026-09-28",
        "https://www.avalanchefusion.com/orbitron",
        "Current D-T power-stage description; claims prospective.",
    ],
    [
        "A02",
        "Avalanche Energy",
        "Neutron camera on Orbitron",
        "APS DPP archive",
        "company-authored conference abstract",
        "2024-10-09",
        "https://meetings-archive.aps.org/dpp/2024/gp12/114",
        "Documents deuterium neutron experiments; not independent replication.",
    ],
    [
        "A03",
        "Avalanche Energy",
        "The Orbitron: A crossed-field device for co-confinement of high energy ions and electrons",
        "AIP Advances",
        "peer-reviewed experiment",
        "2024-08-20",
        "https://doi.org/10.1063/5.0201470",
        "Device/ion confinement evidence; no gain/electricity.",
    ],
    [
        "Q01",
        "Princeton Fusion Systems",
        "PFRC white paper",
        "Princeton Fusion Systems",
        "company primary",
        "2022 / accessed 2026-09-28",
        "https://www.princetonfusionsystems.com/wp-content/uploads/2022/05/PFRCWhitePaperJan2022.pdf",
        "D-He3 reactor roadmap; prospective.",
    ],
    [
        "Q02",
        "Princeton Fusion Systems",
        "PFRC",
        "Princeton Plasma Physics Laboratory",
        "government laboratory",
        "accessed 2026-09-28",
        "https://www.pppl.gov/Princeton-Field-Reversed-Configuration",
        "Confirms PPPL device/research, not company power milestone.",
    ],
    [
        "Q03",
        "Princeton Fusion Systems",
        "Wide-bandgap semiconductor amplifiers for fusion plasma heating",
        "Fusion Science and Technology",
        "peer-reviewed engineering paper",
        "2025-10-02",
        "https://doi.org/10.1080/15361055.2025.2540212",
        "Confirms current company engineering work; not fusion performance.",
    ],
]


CLOSURE_FIELDS = [
    "organization",
    "source_record_id",
    "round4_gap_fields",
    "gap_instances_before",
    "fields_closed_or_resolved",
    "gap_instances_resolved",
    "remaining_explicit_negative_findings",
    "audit_date",
]

GAP_FIELDS = [
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

GAP_MAPPING = {
    "status": "normalized_status",
    "source_date": "source_dates",
    "milestone": "highest_independently_supported_milestone",
}

HISTORY_FIELDS = {
    "depth_round4": [
        "organization",
        "match_rule",
        "source_record_id",
        "fields_enriched",
        "enriched_identity_class",
        "enriched_status",
        "enriched_country",
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
    ],
    "depth_round5": [
        "organization",
        "match_rule",
        "source_record_id",
        "fields_enriched",
        "enriched_identity_class",
        "enriched_status",
        "enriched_country",
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
    ],
    "depth_round6": [
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
    ],
}


def read(path: Path, fields: list[str]) -> list[dict[str, str]]:
    """Read a persisted table with its exact producer schema.

    Parameters
    ----------
    path : pathlib.Path
        Overlay, source, closure or previous gap-matrix TSV.
    fields : list of str
        Ordered schema of the selected producer table.

    Returns
    -------
    list of dict
        Original nonempty rows without changing their claim or evidence text.

    Raises
    ------
    ValueError
        If the header, row shape or record count is structurally invalid.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != fields:
            raise ValueError(f"{path.name}: unexpected header")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path.name}: empty table")
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"{path.name}: malformed row")
    return rows


def read_matrix(path: Path) -> dict[str, dict[str, str]]:
    """Read original matrix identities without collapsing duplicate rows.

    Parameters
    ----------
    path : pathlib.Path
        Previous depth4 matrix with its original producer schema.

    Returns
    -------
    dict of dict
        Complete matrix keyed by exact organization identity.

    Raises
    ------
    ValueError
        If an organization is duplicated or blank.
    """
    rows = read(path, GAP_FIELDS)
    old = {row["organization"]: row for row in rows}
    if len(old) != len(rows) or any(not name.strip() for name in old):
        raise ValueError("previous matrix duplicate or blank identities")
    return old


def read_history(directory: Path) -> set[str]:
    """Read distinct prior overlay identities with each layer's own schema.

    Parameters
    ----------
    directory : pathlib.Path
        Company audit directory containing depth4, depth5 and depth6 outputs.

    Returns
    -------
    set of str
        Exact identities already enriched by the three previous layers.

    Raises
    ------
    ValueError
        If prior identities are blank, duplicate or overlap across layers.
    """
    excluded: set[str] = set()
    for name, fields in HISTORY_FIELDS.items():
        rows = read(directory / name / "enrichment_overlays.tsv", fields)
        names = [row["organization"] for row in rows]
        if len(set(names)) != len(names) or any(not value.strip() for value in names):
            raise ValueError("historical overlays contain duplicate or blank identities")
        if excluded.intersection(names):
            raise ValueError("historical overlay identities overlap across layers")
        excluded.update(names)
    return excluded


def build_closures(
    overlays: Sequence[Sequence[str]],
    old: Mapping[str, Mapping[str, str]],
    excluded: set[str],
) -> list[list[str]]:
    """Derive bounded closures only for the original deterministic selection.

    Parameters
    ----------
    overlays : sequence of sequences of str
        Complete reviewed ten-row overlay in F order.
    old : mapping of str to mappings
        Complete previous matrix keyed by exact organization name.
    excluded : set of str
        Exact identities from the three previous overlay layers.

    Returns
    -------
    list of list of str
        Closure rows in CLOSURE_FIELDS order, retaining negative findings.

    Raises
    ------
    ValueError
        If shape, ranking, selected identities or bounded closure is invalid.
    """
    if any(len(row) != len(F) for row in overlays):
        raise ValueError("overlay row shape mismatch")
    names = [row[0] for row in overlays]
    if len(names) != 10 or len(set(names)) != 10:
        raise ValueError("expected ten unique overlay targets")
    if any(name not in old for name in names):
        raise ValueError("previous matrix missing overlay target")
    if any(old[row[0]]["record_id"] != row[2] for row in overlays):
        raise ValueError("previous record identity mismatch")
    if any(int(row["priority_score"]) < 0 or int(row["source_row"]) < 1 for row in old.values()):
        raise ValueError("invalid previous matrix ranking")
    eligible = [
        row
        for row in old.values()
        if row["organization"] not in excluded
        and {"fuel_cycle", "status"} & set(row["gap_fields"].split(";"))
    ]
    eligible.sort(key=lambda row: (-int(row["priority_score"]), int(row["source_row"])))
    if names != [row["organization"] for row in eligible[:10]]:
        raise ValueError("overlay order/selection does not match deterministic rule")
    closures: list[list[str]] = []
    for row in overlays:
        before = old[row[0]]["gap_fields"].split(";")
        enriched = set(row[3].split(";"))
        closed = [field for field in before if GAP_MAPPING.get(field, field) in enriched]
        if len(closed) != len(before):
            raise ValueError("incomplete bounded closure")
        closures.append(
            [
                row[0],
                row[2],
                ";".join(before),
                str(len(before)),
                ";".join(closed),
                str(len(closed)),
                row[16],
                DATE,
            ]
        )
    return closures


def write(path: Path, fields: list[str], rows: Sequence[Sequence[str]]) -> None:
    """Serialize original curated or derived rows in deterministic TSV order.

    Parameters
    ----------
    path : pathlib.Path
        Output table in the selected directory.
    fields : list of str
        Ordered producer column names.
    rows : sequence of sequences of str
        Complete curated or derived rows without changing claims.
    """
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(fields)
        writer.writerows(rows)


def main() -> None:
    """Validate previous identities, exclusions and selection before output writes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap-matrix", type=Path, default=R4)
    parser.add_argument("--history-directory", type=Path, default=H.parent)
    parser.add_argument("--output-directory", type=Path, default=H)
    args = parser.parse_args()
    inputs = [
        args.gap_matrix,
        *[args.history_directory / name / "enrichment_overlays.tsv" for name in HISTORY_FIELDS],
    ]
    outputs = [
        args.output_directory / name
        for name in ("enrichment_overlays.tsv", "source_registry.tsv", "gap_closure.tsv")
    ]
    if {path.resolve() for path in inputs} & {path.resolve() for path in outputs}:
        print("BUILD FAILED: output would replace a source input")
        raise SystemExit(1)
    try:
        closures = build_closures(
            ROWS, read_matrix(args.gap_matrix), read_history(args.history_directory)
        )
        args.output_directory.mkdir(parents=True, exist_ok=True)
        write(outputs[0], F, ROWS)
        write(outputs[1], SF, [[*row, DATE] for row in S])
        write(outputs[2], CLOSURE_FIELDS, closures)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"BUILD FAILED: {error}")
        raise SystemExit(1) from None
    print(
        f"wrote {len(ROWS)} overlays, {len(S)} sources, {len(closures)} closure rows; resolved {sum(int(row[5]) for row in closures)} gap instances"
    )


if __name__ == "__main__":
    main()
