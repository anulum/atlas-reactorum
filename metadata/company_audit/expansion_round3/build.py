#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/expansion_round3/build.py
"""Deterministically build the round-3 fusion-organization audit tables."""

from __future__ import annotations

import argparse
import csv
from collections.abc import Mapping, Sequence
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATE = "2026-09-28"

FIELDS = [
    "candidate_id",
    "organization",
    "aliases",
    "identity_class",
    "country",
    "founded",
    "normalized_status",
    "approach_family",
    "public_devices_projects",
    "company_claim_summary",
    "evidence_tier",
    "highest_independently_supported_milestone",
    "unsupported_or_ambiguous_claims",
    "primary_url",
    "independent_urls",
    "source_ids",
    "source_dates",
    "audit_date",
    "confidence",
    "inclusion_rationale",
]

# title, publisher, source_type, source_date, url, scope_and_limitations
SOURCES = {
    "R3S001": (
        "CNEN visit to ETE and National Fusion Programme planning",
        "Brazilian National Nuclear Energy Commission (CNEN)",
        "government primary",
        "2022-02-04",
        "https://www.gov.br/cnen/pt-br/assunto/ultimas-noticias/presidente-da-cnen-e-diretor-da-dpd-visitam-o-experimento-tokamak-esferico-ete-no-inpe-1",
        "Confirms ETE, provisional LFN and submitted PNFN; it does not establish completion of the proposed Ipero laboratory.",
    ),
    "R3S002": (
        "World Fusion Outlook 2024",
        "International Atomic Energy Agency",
        "intergovernmental independent synthesis",
        "2024",
        "https://www-pub.iaea.org/MTCD/Publications/PDF/p15777-24-02766E_WFO_web.pdf",
        "Authoritative regional overview; country summaries are not device-performance audits.",
    ),
    "R3S003": (
        "Controlled nuclear fusion activity programme",
        "Argentine National Atomic Energy Commission (CNEA)",
        "government primary",
        "2013-12",
        "https://nuclea.cnea.gob.ar/items/75717225-7583-4b0a-af74-a3bd4c708a65",
        "Institutional proposal and activity record; not evidence of a power-reactor programme.",
    ),
    "R3S004": (
        "Overview of nuclear fusion activities in Argentina",
        "IAEA Fusion Energy Conference",
        "intergovernmental conference record",
        "2025",
        "https://conferences.iaea.org/event/392/contributions/35641/attachments/19715/36105/Gervasoni-OV.pdf",
        "Independent venue confirms current CNEA-CONICET research context; author is a programme participant.",
    ),
    "R3S005": (
        "Balseiro inspection report on Huemul Island",
        "CNEA repository",
        "government technical primary",
        "1952 report; 1988 edition",
        "https://nuclea.cnea.gob.ar/entities/publication/5aedabc4-3322-4543-b11d-269deadd1365/full",
        "Contemporaneous technical rejection of the claimed result and record of programme termination.",
    ),
    "R3S006": (
        "Engineering and development in Argentina's nuclear sector",
        "Argentina National Institute of Public Administration",
        "government historical analysis",
        "2023",
        "https://nuclea.cnea.gob.ar/server/api/core/bitstreams/9cc4fe70-4ec9-4f7e-8c48-235b9b16c9eb/content",
        "Independent institutional history describes the finding as a sham and November 1952 dismantlement.",
    ),
    "R3S007": (
        "Plasma Physics and Controlled Nuclear Fusion programme",
        "National Autonomous University of Mexico (UNAM)",
        "university primary",
        "2023",
        "https://www.siass.unam.mx/consulta/1860565",
        "Confirms a conceptual spherical-tokamak design programme, not construction or plasma operation.",
    ),
    "R3S008": (
        "First Inter-American Conference on Fusion Science and Technology agenda",
        "FusionLatam / CCHEN / CLAF / IAEA",
        "multi-institution programme record",
        "2025",
        "https://www.fusionlatam.cl/documents/Agenda%20CICT-FN%202025%20English.pdf",
        "Confirms named Mexican and regional research participation; conference agenda is not performance validation.",
    ),
    "R3S009": (
        "Thermonuclear plasma research",
        "Chilean Nuclear Energy Commission (CCHEN)",
        "government primary",
        "accessed 2026-09-28",
        "https://www.cchen.cl/?page_id=1716",
        "Describes CCHEN plasma-focus, z-pinch and pulsed-power research; no electricity programme.",
    ),
    "R3S010": (
        "Chilean and Latin American fusion workforce perspective",
        "IAEA Technical Meeting on Developing the Fusion Workforce",
        "intergovernmental conference record",
        "2026-04-27",
        "https://conferences.iaea.org/event/449/contributions/40739/",
        "Corroborates active small-device research and regional training; contribution is authored by CCHEN staff.",
    ),
    "R3S011": (
        "Laboratory for Plasma for Fusion Energy and Applications",
        "Tecnologico de Costa Rica",
        "university primary",
        "accessed 2026-09-28",
        "https://www.tec.ac.cr/laboratorio-plasmas-energia-fusion-aplicaciones",
        "Documents SCR-1, MEDUSA-CR and laboratory history; device results remain research-scale.",
    ),
    "R3S012": (
        "World Survey of Fusion Devices 2022",
        "International Atomic Energy Agency",
        "intergovernmental technical survey",
        "2022; web edition current 2026",
        "https://www-pub.iaea.org/MTCD/publications/PDF/CRCP-FUS-001webRev.pdf",
        "IAEA-reviewed device survey independently corroborates SCR-1, EGYPTOR and DAMAVAND facility identities/status at publication.",
    ),
    "R3S013": (
        "Latin American Center for Physics institutional profile",
        "CLAF",
        "intergovernmental primary",
        "accessed 2026-09-28",
        "https://claffisica.org.br/page/el-claf",
        "Confirms CLAF mandate and member-state network; page does not itself enumerate Fusion Unit outputs.",
    ),
    "R3S014": (
        "Nuclear Fusion Unit regional coordination synopsis",
        "IAEA Fusion Energy Conference",
        "intergovernmental conference record",
        "2025",
        "https://conferences.iaea.org/event/392/contributions/35871/attachments/19844/33898/Synopses%20L%20Soto%20et%20al%20FEC%202025%20v2.pdf",
        "States NFU-CLAF was established in October 2024 across eight countries; no hardware is attributed to the network.",
    ),
    "R3S015": (
        "Arab Fusion Energy Initiative",
        "American University of Beirut",
        "university primary",
        "accessed 2026-09-28",
        "https://www.aub.edu/fas/AFEI_Initiative/Pages/default.aspx",
        "States regional-programme and medium-tokamak intentions; funding, host and construction are not established.",
    ),
    "R3S016": (
        "Building fusion workforce capacity in Jordan and the Arab world",
        "IAEA Technical Meeting on Developing the Fusion Workforce",
        "intergovernmental conference record",
        "2026-04",
        "https://conferences.iaea.org/event/449/contributions/40767/attachments/22491/39054/Building%20Fusion%20Workforce%20Capacity%20in%20Jordan%20and%20the%20Arab%20World%20-%20Final.pdf",
        "Corroborates AFEI/Arab Fusion Energy Program formation and proposed regional centre; not construction evidence.",
    ),
    "R3S017": (
        "Indimaj services and MENA mission",
        "Indimaj Group",
        "company primary",
        "accessed 2026-09-28",
        "https://www.indimajgroup.com/services",
        "Self-described advisory and supply-chain-entry services; no disclosed reactor development or client-delivery evidence.",
    ),
    "R3S018": (
        "INDIMAJ GROUP LTD company overview",
        "UK Companies House",
        "government registry",
        "2025-12-05",
        "https://find-and-update.company-information.service.gov.uk/company/16892813",
        "Independently confirms active legal identity and incorporation only, not fusion expertise or contracts.",
    ),
    "R3S019": (
        "Damavand control-system contribution",
        "IAEA Technical Meeting",
        "intergovernmental conference record / researcher primary",
        "2024-07",
        "https://conferences.iaea.org/event/377/contributions/31627/",
        "Recent AEOI/NSTRI-affiliated experimental work supports active use; author-reported technical results.",
    ),
    "R3S020": (
        "Egyptian Atomic Energy Authority",
        "Egyptian Atomic Energy Authority",
        "government primary",
        "accessed 2026-09-28",
        "https://eaea.org.eg/",
        "Confirms EAEA and its plasma research remit; the landing page gives limited EGYPTOR detail.",
    ),
    "R3S021": (
        "Laboratory for Plasmas and Nuclear Fusion / EGYPTOR",
        "Egyptian Atomic Energy Authority",
        "government research programme",
        "accessed 2026-09-28",
        "https://eaea.org.eg/",
        "Primary institutional anchor for EGYPTOR; current operating parameters require independent survey support.",
    ),
    "R3S022": (
        "Current African fusion outlook",
        "International Atomic Energy Agency",
        "intergovernmental independent synthesis",
        "2024",
        "https://www-pub.iaea.org/MTCD/Publications/PDF/p15777-24-02766E_WFO_web.pdf",
        "States fusion-specific African R&D is limited and identifies Egyptian and Libyan tokamaks; does not imply power development.",
    ),
    "R3S023": (
        "Yan Fusion company and programme",
        "Yan Fusion",
        "company primary",
        "accessed 2026-09-28",
        "https://www.yanfusion.com/about",
        "Company-described stellarator, coil-production and schedule claims; no independent device result.",
    ),
    "R3S024": (
        "The 46 companies scrambling to commercialize fusion",
        "Nature",
        "independent scientific journalism",
        "2026-08",
        "https://www.nature.com/immersive/d41586-026-02513-5/index.html",
        "Independently corroborates Yan Fusion identity, approach and reported funding; not technical validation.",
    ),
    "R3S025": (
        "Firefly Fusion",
        "Firefly Fusion",
        "company primary",
        "accessed 2026-09-28",
        "https://fireflyfusion.energy/",
        "Official approach and team claims; no prototype result.",
    ),
    "R3S026": (
        "Firefly Fusion collaboration profile",
        "DIII-D National Fusion Facility",
        "independent national-facility partner",
        "accessed 2026-09-28",
        "https://d3dfusion.org/fireflyfusion/",
        "Corroborates LUCIOLE concept and DIII-D collaboration, not construction or projected Q.",
    ),
    "R3S027": (
        "Kronos Fusion Energy",
        "Kronos Fusion Energy",
        "company primary",
        "accessed 2026-09-28",
        "https://www.kronosfusionenergy.com/",
        "Company presents HYPERION and advanced-fuel concepts and explicitly indicates machines are not built.",
    ),
    "R3S028": (
        "Kronos Fusion Energy company profile",
        "FusionXInvest",
        "independent specialist directory",
        "accessed 2026-09-28",
        "https://fusionxinvest.com/company-profile/4394/kronos-fusion-energy/",
        "Corroborates company identity and conceptual programme; directory evidence is not physics validation.",
    ),
}


def row(
    i: int,
    org: str,
    aliases: str,
    cls: str,
    country: str,
    founded: int | str,
    status: str,
    approach: str,
    projects: str,
    claim: str,
    tier: str,
    milestone: str,
    gaps: str,
    primary: str,
    independent: str,
    ids: str,
    dates: str,
    confidence: str,
    rationale: str,
) -> dict[str, str]:
    """Serialize one reviewed discovery record while preserving claim limits.

    Parameters
    ----------
    i : int
        Local sequential FC3 candidate number.
    org : str
        Declared organization identity.
    aliases : str
        Recorded alternative names separated by semicolons.
    cls : str
        Conservative organization classification.
    country : str
        Recorded geographic label.
    founded : int or str
        Founding year or qualified date text.
    status : str
        Bounded activity status.
    approach : str
        Recorded approach family.
    projects : str
        Named devices or proposed programmes.
    claim : str
        Organization-supplied claim, separated from independent findings.
    tier : str
        Evidence classification with qualification.
    milestone : str
        Highest independently supported bounded milestone.
    gaps : str
        Unsupported or ambiguous assertions retained explicitly.
    primary : str
        Recorded primary source link.
    independent : str
        Recorded independent source links.
    ids : str
        Referenced source registry identifiers.
    dates : str
        Record-specific source dates.
    confidence : str
        Curated confidence level.
    rationale : str
        Discovery inclusion rationale.

    Returns
    -------
    dict of str
        Original candidate schema with a stable local FC3 identifier.
    """
    values = [
        f"FC3-{i:03d}",
        org,
        aliases,
        cls,
        country,
        str(founded),
        status,
        approach,
        projects,
        claim,
        tier,
        milestone,
        gaps,
        primary,
        independent,
        ids,
        dates,
        DATE,
        confidence,
        rationale,
    ]
    return dict(zip(FIELDS, values, strict=True))


CANDIDATES = [
    row(
        1,
        "Brazilian National Fusion Programme and National Fusion Laboratory",
        "PNFN; Programa Nacional de Fusao Nuclear; LFN; Laboratorio de Fusao Nuclear",
        "national public fusion research programme; not a company",
        "Brazil",
        2021,
        "proposed programme; existing research devices active or being upgraded",
        "magnetic confinement | spherical and conventional tokamak research",
        "LFN at Ipero (proposed); ETE; TCABR; NOVA-UFES",
        "CNEN proposes a coordinated national programme and permanent laboratory around upgrades and transfer of existing Brazilian tokamak capabilities.",
        "B — programme planning and existing-device base corroborated",
        "CNEN documentation and IAEA regional synthesis support an established Brazilian fusion-research base, an ETE facility and formal LFN/PNFN planning.",
        "Permanent Ipero laboratory completion, device transfer, new plasma milestones, fusion gain and electricity generation are not established.",
        SOURCES["R3S001"][4],
        SOURCES["R3S002"][4],
        "R3S001;R3S002",
        "CNEN 2022-02-04; IAEA 2024",
        "high",
        "Major Latin American public programme omitted from the company-centric baseline; retained with non-company classification.",
    ),
    row(
        2,
        "CNEA Controlled Fusion Research Programme",
        "Comision Nacional de Energia Atomica fusion programme; CNEA fusion activities",
        "national laboratory research programme; not a company",
        "Argentina",
        1977,
        "active research programme; no power demonstrator",
        "plasma focus | magnetic confinement theory and materials research",
        "controlled-fusion activity programme; CNEA-CONICET projects",
        "CNEA maintains controlled-fusion research and proposes an integrated national activity portfolio.",
        "B — institutional programme and current research community corroborated",
        "CNEA records and an IAEA conference overview establish a durable Argentine fusion research programme and active CNEA-CONICET community.",
        "No Argentine fusion power reactor, gain result or electricity milestone is supported; programme scope and funding after 2025 remain incompletely public.",
        SOURCES["R3S003"][4],
        SOURCES["R3S004"][4],
        "R3S003;R3S004",
        "CNEA 2013; IAEA FEC 2025",
        "medium",
        "Distinct current public programme, separate from the terminated Huemul claim.",
    ),
    row(
        3,
        "Huemul Project",
        "Proyecto Huemul; Richter Project; Thermotron",
        "historical state-backed speculative fusion claim; terminated",
        "Argentina",
        1948,
        "terminated in 1952 after negative technical review",
        "claimed thermonuclear reactions using shock/acoustic heating; poorly specified",
        "Huemul Island pilot plant; Thermotron",
        "Ronald Richter claimed controlled thermonuclear reactions and prospective cheap fusion energy.",
        "D — historically documented claim refuted by contemporaneous review",
        "Balseiro's inspection found no support for the claimed reactions; the government ended and dismantled the project in 1952.",
        "No validated fusion reaction or usable energy was produced; the original technical claims lacked reproducible evidence.",
        SOURCES["R3S005"][4],
        SOURCES["R3S006"][4],
        "R3S005;R3S006",
        "inspection 1952 / edition 1988; INAP 2023",
        "high",
        "Historically important Latin American speculative claim, explicitly segregated from active developers and validated milestones.",
    ),
    row(
        4,
        "UNAM Controlled Nuclear Fusion and Plasma Physics Programme",
        "Fisica de Plasmas y Fusion Nuclear Controlada; ICN-UNAM plasma department",
        "public academic research programme; not a company",
        "Mexico",
        2023,
        "active conceptual-design and theory programme",
        "magnetic confinement | spherical tokamak theory and engineering",
        "conceptual spherical tokamak design",
        "UNAM describes work on equilibrium, stability, transport, structural loads and plasma control for a conceptual spherical tokamak.",
        "B/C — university programme corroborated; pre-hardware",
        "UNAM pages and the regional conference record support an identifiable controlled-fusion research group and conceptual-design activity.",
        "Construction, first plasma, fusion reactions, gain and power generation are not claimed or demonstrated.",
        SOURCES["R3S007"][4],
        SOURCES["R3S008"][4],
        "R3S007;R3S008",
        "UNAM programme 2023; conference 2025",
        "high",
        "Mexican public programme adds a documented non-English Latin American ecosystem.",
    ),
    row(
        5,
        "CCHEN Plasma Physics and Nuclear Fusion Laboratory",
        "Laboratorio de Fisica de Plasmas y Fusion Nuclear; Thermonuclear Plasma Division",
        "government fusion research laboratory; not a company",
        "Chile",
        1965,
        "active research laboratory",
        "dense plasma focus | z-pinch | pulsed power | fusion-material exposures",
        "miniaturized plasma-focus devices; P2mc projects",
        "CCHEN reports miniaturized devices that produce fusion-neutron pulses and fusion-relevant material exposures.",
        "A/B — operating small research devices and outputs corroborated",
        "CCHEN programme records and IAEA proceedings support operating small-scale pulsed-plasma research, training and peer-reviewed fusion-relevant work.",
        "Research-device neutron production must not be equated with energy gain, sustained confinement or a power-reactor programme.",
        SOURCES["R3S009"][4],
        SOURCES["R3S010"][4],
        "R3S009;R3S010",
        "CCHEN current page; IAEA 2026-04-27",
        "high",
        "Substantive Chilean public programme and regional-capacity anchor absent from the 84 records.",
    ),
    row(
        6,
        "TEC Laboratory for Plasma for Fusion Energy and Applications",
        "Laboratorio de Plasmas para Energia de Fusion y Aplicaciones; PlasmaTEC",
        "public academic fusion laboratory; not a company",
        "Costa Rica",
        2011,
        "active research laboratory",
        "magnetic confinement | modular stellarator and spherical tokamak",
        "SCR-1; MEDUSA-CR",
        "TEC operates education and research devices for plasma confinement and fusion-science training.",
        "A/B — operating research hardware independently catalogued",
        "TEC and the IAEA device survey corroborate SCR-1 operation, MEDUSA-CR possession and a sustained laboratory programme.",
        "Neither device is an energy-producing reactor; fuel-fusion yield, gain and electricity are not demonstrated.",
        SOURCES["R3S011"][4],
        SOURCES["R3S012"][4],
        "R3S011;R3S012",
        "TEC accessed 2026-09-28; IAEA survey 2022/current edition",
        "high",
        "One of Latin America's clearest operating fusion-research infrastructures.",
    ),
    row(
        7,
        "CLAF Nuclear Fusion Unit",
        "NFU-CLAF; Unidad de Fusion Nuclear del Centro Latinoamericano de Fisica",
        "regional fusion coordination network; not a reactor developer",
        "Latin America and Caribbean",
        2024,
        "active coordination and capacity-building network",
        "cross-approach research coordination and workforce development",
        "regional network across Argentina, Bolivia, Brazil, Chile, Costa Rica, Honduras, Mexico and Uruguay",
        "The unit coordinates regional laboratories, training, knowledge sharing and policy/industry dialogue.",
        "B — establishment and participating-country scope corroborated",
        "An IAEA conference synopsis states that NFU-CLAF was established in October 2024 and names its initial eight-country network.",
        "No device, reactor performance, financing pool or construction milestone belongs to the network itself.",
        SOURCES["R3S013"][4],
        SOURCES["R3S014"][4],
        "R3S013;R3S014",
        "CLAF accessed 2026-09-28; IAEA FEC 2025",
        "high",
        "Captures the regional ecosystem layer without misclassifying it as a developer.",
    ),
    row(
        8,
        "Arab Fusion Energy Initiative",
        "AFEI; Arab Fusion Energy Program collaboration",
        "regional public-academic fusion initiative; planned device",
        "Lebanon / Arab region",
        2023,
        "active initiative; fundraising and pre-construction planning",
        "magnetic confinement | proposed medium-sized tokamak",
        "proposed Arab regional fusion centre and medium-sized tokamak",
        "AFEI proposes a regional research hub, workforce programme and tokamak using HTS, liquid-lithium, RF and neutral-beam technologies.",
        "B/C — initiative and proposal corroborated; no build milestone",
        "AUB and an IAEA workforce meeting corroborate the initiative, Arab programme coordination and proposed regional centre/device.",
        "Host country, committed construction budget, final design, procurement, build start and plasma milestones remain unconfirmed.",
        SOURCES["R3S015"][4],
        SOURCES["R3S016"][4],
        "R3S015;R3S016",
        "AUB accessed 2026-09-28; IAEA 2026-04",
        "high",
        "Credible Middle Eastern regional initiative, conservatively retained as planning rather than a reactor project.",
    ),
    row(
        9,
        "Indimaj Group",
        "Indimaj Group Ltd; Indimaj",
        "fusion advisory and ecosystem consultancy; not a reactor developer",
        "United Kingdom / MENA focus",
        2025,
        "active consultancy",
        "fusion policy, investment, programme and supply-chain advisory",
        "MENA fusion advisory services",
        "The company says it helps governments, universities, investors and industry design programmes and enter fusion supply chains.",
        "C — legal identity corroborated; delivery claims not independently demonstrated",
        "UK Companies House confirms the active legal entity and incorporation; the company site establishes its declared fusion-advisory scope.",
        "No independently disclosed clients, contracts, reactor hardware or technical-performance milestone was found; do not count as a developer.",
        SOURCES["R3S017"][4],
        SOURCES["R3S018"][4],
        "R3S017;R3S018",
        "company site accessed 2026-09-28; Companies House incorporated 2025-12-05",
        "medium",
        "Adds a clearly classified MENA-focused ecosystem service provider rather than inventing a regional reactor company.",
    ),
    row(
        10,
        "AEOI Plasma and Nuclear Fusion Research School",
        "NSTRI Plasma Physics and Nuclear Fusion Research School; Damavand programme",
        "national public fusion research programme; not a company",
        "Iran",
        1990,
        "active research programme",
        "magnetic confinement | conventional tokamak",
        "DAMAVAND tokamak",
        "The AEOI/NSTRI school conducts tokamak plasma-control, materials and discharge research using DAMAVAND.",
        "A/B — operating research device and recent experiments corroborated",
        "The IAEA device survey lists DAMAVAND as operating, while 2024 IAEA proceedings document recent control-system experiments by AEOI/NSTRI researchers.",
        "Research-scale operation does not establish fusion gain, D-T power production or a commercial reactor programme.",
        SOURCES["R3S019"][4],
        SOURCES["R3S012"][4],
        "R3S019;R3S012",
        "IAEA meeting 2024-07; IAEA survey 2022/current edition",
        "high",
        "Major Middle Eastern operating tokamak programme missing from the baseline.",
    ),
    row(
        11,
        "Egyptian Atomic Energy Authority Plasma and Nuclear Fusion Programme",
        "EAEA Plasma and Nuclear Fusion Department; EGYPTOR programme",
        "national public fusion research programme; not a company",
        "Egypt",
        1998,
        "research programme; device status reported operating in IAEA 2022 survey",
        "magnetic confinement | conventional tokamak | plasma focus",
        "EGYPTOR tokamak; plasma-focus facilities",
        "EAEA maintains plasma and fusion research infrastructure centred on the EGYPTOR research tokamak and plasma laboratories.",
        "B — institutional identity and research device independently catalogued",
        "EAEA confirms its nuclear/plasma research remit; the IAEA survey documents EGYPTOR as a public research tokamak and the World Fusion Outlook identifies Egypt as one of Africa's tokamak hosts.",
        "Current post-2022 operating cadence, upgraded parameters, fusion reactions, gain and any power programme are not established.",
        SOURCES["R3S020"][4],
        SOURCES["R3S012"][4] + "; " + SOURCES["R3S022"][4],
        "R3S020;R3S012;R3S022",
        "EAEA accessed 2026-09-28; IAEA survey 2022; Outlook 2024",
        "medium",
        "Evidence-backed African public fusion programme; explicitly not a commercial reactor developer.",
    ),
    row(
        12,
        "Yan Fusion",
        "Yan Fusion (Shanghai) Technology Co. Ltd.; YAN FUSION; 岩超聚能",
        "fusion reactor/device developer and magnet supplier",
        "China",
        2025,
        "active; coil production line claimed; device planned",
        "magnetic confinement | superconducting stellarator | AI-assisted design",
        "four proposed LTS/HTS 3D stellarator coils; planned private stellarator",
        "Company claims a modular 3D superconducting-coil line and targets four coil variants followed by a private stellarator.",
        "B/C — company, funding and approach corroborated; hardware results company-led",
        "Nature independently identifies the 2025 Shanghai stellarator company and reported funding; the official site shows a specific manufacturing programme.",
        "Production-line throughput, completed qualified coils, device construction, plasma and energy milestones are not independently validated.",
        SOURCES["R3S023"][4],
        SOURCES["R3S024"][4],
        "R3S023;R3S024",
        "official site accessed 2026-09-28; Nature 2026-08",
        "high",
        "Recent non-English entrant formed after the earlier landscape and independently recognized.",
    ),
    row(
        13,
        "Firefly Fusion",
        "Firefly Fusion SAS; Firefly Fusion SA",
        "fusion reactor/device developer",
        "France / Switzerland",
        2024,
        "active; design and research-collaboration stage",
        "magnetic confinement | compact negative-triangularity copper-magnet tokamak",
        "LUCIOLE",
        "Company proposes an actively cooled copper-magnet tokamak intended to explore negative-triangularity burning-plasma regimes.",
        "B/C — legal identity and national-facility collaboration corroborated; pre-hardware",
        "DIII-D independently confirms Firefly's collaboration, LUCIOLE concept, location and negative-triangularity research programme.",
        "Prototype construction, burning plasma, Q=10 ambitions, costs and commercialization schedule are not demonstrated.",
        SOURCES["R3S025"][4],
        SOURCES["R3S026"][4],
        "R3S025;R3S026",
        "official and DIII-D pages accessed 2026-09-28",
        "high",
        "Recent European entrant with a named concept and credible independent partner evidence.",
    ),
    row(
        14,
        "Kronos Fusion Energy",
        "Kronos Fusion; Kronos Fusion Energy Defense Systems",
        "speculative fusion reactor/device developer; pre-hardware",
        "United States",
        2022,
        "active claims; simulation and design stage",
        "magnetic confinement | tandem mirror / linear device | D-T breeder and D-He3 concepts",
        "HYPERION; advanced-fuel tandem-mirror generator concepts",
        "Company markets simulated reactor designs, fuel breeding and advanced-fuel electricity concepts while stating that machines are not yet built.",
        "D — identity corroborated; technical programme remains claim-led",
        "A specialist directory corroborates the company's identity and declared concept, but no independent physical-device milestone was found.",
        "All plasma, breeding, D-He3, net-energy, weapons-effects and deployment claims remain unvalidated without hardware or independent experiments.",
        SOURCES["R3S027"][4],
        SOURCES["R3S028"][4],
        "R3S027;R3S028",
        "official and directory pages accessed 2026-09-28",
        "low",
        "Explicit speculative-claim inclusion that preserves the distinction between simulations, proposals and validated performance.",
    ),
]


SF = [
    "source_id",
    "title",
    "publisher",
    "source_type",
    "source_date",
    "url",
    "scope_and_limitations",
    "accessed_on",
]

AUDIT_FIELDS = [
    "company",
    "aliases",
    "founded",
    "identity_class",
    "normalized_status",
    "country",
    "approach_family",
    "public_devices_projects",
    "company_claim_summary",
    "evidence_tier",
    "highest_independently_supported_milestone",
    "unsupported_or_ambiguous_claims",
    "official_url",
    "independent_urls",
    "source_dates",
    "audit_date",
    "confidence",
]

FIRST_FIELDS = [
    "candidate_id",
    "organization",
    "aliases",
    "identity_class",
    "country",
    "founded",
    "normalized_status",
    "approach_family",
    "public_devices_projects",
    "company_claim_summary",
    "evidence_tier",
    "highest_independently_supported_milestone",
    "unsupported_or_ambiguous_claims",
    "official_url",
    "independent_urls",
    "source_dates",
    "audit_date",
    "confidence",
    "inclusion_rationale",
]


def read(path: Path, fields: list[str]) -> list[dict[str, str]]:
    """Read a nonempty source with its exact ordered producer schema.

    Parameters
    ----------
    path : pathlib.Path
        Candidate, registry or protected audit TSV.
    fields : list of str
        Selected producer's ordered columns.

    Returns
    -------
    list of dict
        Original rows without changing source wording or evidence levels.

    Raises
    ------
    ValueError
        If schema, row shape or table presence is invalid.
    """
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != fields:
            raise ValueError(f"{path.name}: unexpected header")
        rows = list(reader)
    if not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError(f"{path.name}: empty or malformed rows")
    return rows


def norm(value: str) -> str:
    """Normalize a declared identity solely for duplicate comparisons.

    Parameters
    ----------
    value : str
        Organization name or alias from an audited table.

    Returns
    -------
    str
        Case-folded alphanumeric comparison key, never a replacement identity.
    """
    return "".join(char for char in value.casefold() if char.isalnum())


def read_protected(directory: Path) -> set[str]:
    """Read required earlier catalog identities before any candidate output.

    Parameters
    ----------
    directory : pathlib.Path
        Company audit root with all three earlier persisted catalogs.

    Returns
    -------
    set of str
        Normalized primary names and nonblank declared aliases.

    Raises
    ------
    ValueError
        If a previous count is wrong, primary identities duplicate or names are invalid.
    """
    protected: set[str] = set()
    for name, fields, key, count in (
        ("audited_companies.tsv", AUDIT_FIELDS, "company", 51),
        ("expansion_candidates.tsv", FIRST_FIELDS, "organization", 18),
        ("expansion_round2/candidates.tsv", FIELDS, "organization", 15),
    ):
        rows = read(directory / name, fields)
        if len(rows) != count:
            raise ValueError("expected baseline file counts 51/18/15 totaling84")
        primary = [norm(row[key]) for row in rows]
        if any(not value for value in primary) or len(set(primary)) != len(primary):
            raise ValueError("protected catalog has blank or duplicate primary identities")
        for row in rows:
            for value in [row[key], *row["aliases"].split(";")]:
                if value.strip():
                    normalized = norm(value)
                    if not normalized:
                        raise ValueError("protected catalog has invalid alias")
                    protected.add(normalized)
    return protected


def check_identities(candidates: Sequence[Mapping[str, str]], protected: set[str]) -> None:
    """Refuse candidate IDs, names or aliases that lose discovery separation.

    Parameters
    ----------
    candidates : sequence of mappings of str to str
        Complete reviewed candidate rows with the original FIELDS schema.
    protected : set of str
        Normalized names and aliases from required earlier catalogs.

    Raises
    ------
    ValueError
        If schema or candidate identities are invalid, duplicated or collide.
    """
    if not candidates or any(set(row) != set(FIELDS) for row in candidates):
        raise ValueError("candidate table empty or row schema mismatch")
    ids = [row["candidate_id"] for row in candidates]
    if any(not value.strip() for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("duplicate or blank candidate_id")
    seen: set[str] = set()
    for row in candidates:
        values = [row["organization"], *[a.strip() for a in row["aliases"].split(";") if a.strip()]]
        identities = {norm(value) for value in values}
        if "" in identities:
            raise ValueError("invalid normalized candidate identity")
        if identities & protected:
            raise ValueError("protected identity collision")
        if identities & seen:
            raise ValueError("duplicate candidate name or alias")
        seen.update(identities)


def write(path: Path, fields: list[str], rows: Sequence[Mapping[str, str]]) -> None:
    """Write original reviewed records in deterministic field and row order.

    Parameters
    ----------
    path : pathlib.Path
        Candidate or source registry output.
    fields : list of str
        Original ordered producer schema.
    rows : sequence of mappings of str to str
        Reviewed record values without changing evidence wording.
    """
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Read protected evidence and check candidate identities before output writes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-root", type=Path, default=ROOT)
    parser.add_argument("--output-directory", type=Path, default=HERE)
    args = parser.parse_args()
    inputs = {
        (args.audit_root / name).resolve()
        for name in (
            "audited_companies.tsv",
            "expansion_candidates.tsv",
            "expansion_round2/candidates.tsv",
        )
    }
    outputs = [args.output_directory / name for name in ("candidates.tsv", "source_registry.tsv")]
    if inputs & {path.resolve() for path in outputs}:
        print("BUILD FAILED: output would replace a protected input")
        raise SystemExit(1)
    try:
        protected = read_protected(args.audit_root)
        check_identities(CANDIDATES, protected)
        sources = [
            dict(zip(SF, [sid, *values, DATE], strict=True))
            for sid, values in sorted(SOURCES.items())
        ]
        args.output_directory.mkdir(parents=True, exist_ok=True)
        write(outputs[0], FIELDS, CANDIDATES)
        write(outputs[1], SF, sources)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"BUILD FAILED: {error}")
        raise SystemExit(1) from None
    print(f"wrote {len(CANDIDATES)} candidates and {len(SOURCES)} source records")


if __name__ == "__main__":
    main()
