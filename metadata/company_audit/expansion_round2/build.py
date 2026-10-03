#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/expansion_round2/build.py
"""Build the round 2 company and programme expansion.

Emits reviewed discovery candidates, their source registry and the evidence fields
each claim rests on.
"""

from __future__ import annotations

import argparse
import csv
from collections.abc import Mapping, Sequence
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATE = "2026-09-27"
SOURCES = {
    "S001": (
        "Dongsheng Fusion financing and company background",
        "Qiming Venture Partners",
        "investor primary",
        "2026-08",
        "https://www.qimingvc.com/en/node/7639",
        "Company formation, route and financing; investor-authored, not performance validation.",
    ),
    "S002": (
        "Shanghai Dongsheng Fusion financing report",
        "Sina Finance",
        "independent media",
        "2026-06-11",
        "https://finance.sina.com.cn/stock/csjzbj/2026-06-11/doc-iniazyek2244561.shtml",
        "Independent identity/funding coverage; technical detail remains company-derived.",
    ),
    "S003": (
        "Xeonova official site",
        "Hefei Xeonova Technology",
        "official",
        "2026",
        "https://xeonova.cn/",
        "Official technical description and news; self-reported performance.",
    ),
    "S004": (
        "China fusion commercialization landscape",
        "OCN Industry Research",
        "independent industry analysis",
        "2026-09",
        "https://www.ocn.com.cn/industry/latest/202609/tjrja2092030.shtml",
        "Broad market synthesis; some financing data explicitly described as unconfirmed.",
    ),
    "S005": (
        "HHMAX-901 project progress",
        "HHMAX-Energy",
        "official",
        "2025-2026",
        "https://www.hhmax-energy.com/xiangmujinzhan.html",
        "Official device chronology; first-plasma claim not independently instrument-verified.",
    ),
    "S006": (
        "Hanhai Fusion profile",
        "Energy Startups",
        "independent directory",
        "2026-09-11",
        "https://www.energystartups.org/startup/hhmax-energy/",
        "Independent identity and program summary; relies partly on company statements.",
    ),
    "S007": (
        "Chaoci Xineng 25 T magnet supplier announcement",
        "Shanghai Superconductor",
        "industrial partner primary",
        "2026-08-21",
        "https://www.shsctec.com/zh/news/chaocixineng25T/",
        "Partner confirms coil manufacturing and joint sample work, not full magnet qualification.",
    ),
    "S008": (
        "Chinese private fusion financing landscape",
        "ChinaBaogao",
        "independent industry analysis",
        "2026-07",
        "https://www.chinabaogao.com/baogao/202607/807250.html",
        "Market-level identity and financing evidence; not technical validation.",
    ),
    "S009": (
        "Chinese fusion company landscape",
        "OCN Industry Research",
        "independent industry analysis",
        "2026-09",
        "https://www.ocn.com.cn/industry/latest/202609/tjrja2092030.shtml",
        "Identifies Zhongke Qingneng as cryogenic-system supplier; not a reactor developer.",
    ),
    "S010": (
        "Fusion cryogenic systems industry report",
        "Aijian Securities",
        "independent securities research",
        "2025-11-19",
        "https://pdf.dfcfw.com/pdf/H3_AP202511201784737698_1.pdf?1763627718000.pdf=",
        "Reports commissioned 3 kW at 4.5 K refrigerator and CRAFT application; secondary source.",
    ),
    "S011": (
        "LINEA Innovations official site",
        "LINEA Innovations",
        "official",
        "2026",
        "https://linea-innovations.com/en/",
        "Official approach and corporate updates; prospective performance claims.",
    ),
    "S012": (
        "Japan fusion patent landscape report",
        "Japan Patent Office",
        "government",
        "2026-03",
        "https://www.jpo.go.jp/resources/report/gidou-houkoku/tokkyo/document/index/2025_01.pdf",
        "Government landscape source for Japanese companies and approaches.",
    ),
    "S013": (
        "Starlight Engine established for FAST",
        "Kyoto Fusioneering",
        "parent/project primary",
        "2025-04-16",
        "https://kyotofusioneering.com/en/news/2025/04/16/3006",
        "Confirms legal entity and project role; partner announcement.",
    ),
    "S014": (
        "Furukawa Electric investment in Starlight Engine",
        "Furukawa Electric",
        "independent industrial partner",
        "2026-07-15",
        "https://www.furukawaelectric.com/en/release/2026/metal_20260715.html",
        "Corroborates company, ownership background and FAST role; no reactor performance.",
    ),
    "S015": (
        "MiRESSO official site",
        "MiRESSO",
        "official",
        "2026",
        "https://miresso.co.jp/en/",
        "Official BETA and beryllium-refining program.",
    ),
    "S016": (
        "QST venture support listing for MiRESSO",
        "QST",
        "government research institute",
        "2026",
        "https://www.qst.go.jp/site/venture-support-english/",
        "Confirms QST spin-out certification, establishment and business scope.",
    ),
    "S017": (
        "Eterna Fusion seed investment",
        "Maeil Business Newspaper",
        "independent media",
        "2026-07-06",
        "https://www.mk.co.kr/en/it/12091002",
        "Confirms incorporation, team, funding and tokamak-injection concept; no device result.",
    ),
    "S018": (
        "Eterna Fusion company registry profile",
        "THE VC",
        "independent business database",
        "2026",
        "https://thevc.kr/eternafusion",
        "Corporate identity and founding date; limited technical validation.",
    ),
    "S019": (
        "EnableFusion official site",
        "EnableFusion",
        "official",
        "2026",
        "https://www.enablefusion.com/",
        "Official engineering-platform scope; self-description.",
    ),
    "S020": (
        "Korean fusion commercialization strategy",
        "Korean Ministry of Science and ICT",
        "government",
        "2024",
        "https://www.msit.go.kr/eng/bbs/view.do?bbsSeqNo=42&mId=4&mPid=2&nttSeqNo=1028&pageIndex=&sCode=eng&searchOpt=ALL&searchTxt=",
        "Supports national startup/supply-chain context, not company-specific performance.",
    ),
    "S021": (
        "Quasarus official site",
        "Quasarus",
        "official",
        "2026",
        "https://quasarus.in/",
        "Official early-stage simulation-first scope.",
    ),
    "S022": (
        "Indian fusion startups seek policy clarity",
        "Mint",
        "independent media",
        "2026-07",
        "https://www.livemint.com/companies/start-ups/nuclear-fusion-startups-seek-regulatory-clarity-more-patient-capital-11784795623284.html",
        "Ecosystem context; does not validate individual designs.",
    ),
    "S023": (
        "Hylenr official company page",
        "Hylenr Technologies",
        "official",
        "2026",
        "https://www.hylenr.com/about",
        "Official lattice-confinement claims and company chronology.",
    ),
    "S024": (
        "Indian fusion startup policy report",
        "Mint",
        "independent media",
        "2026-07",
        "https://www.livemint.com/companies/start-ups/nuclear-fusion-startups-seek-regulatory-clarity-more-patient-capital-11784795623284.html",
        "Confirms company participation in Indian startup ecosystem; not independent physics validation.",
    ),
    "S025": (
        "ASPL Fusion positioning",
        "ASPL Fusion",
        "official",
        "2026",
        "https://asplfusion.com/about/positioning.html",
        "Explicitly identifies near-term plasma/neutron systems and disclaims near-term fusion-energy status.",
    ),
    "S026": (
        "ASPL Fusion profile",
        "FusionXInvest",
        "independent specialist directory",
        "2026",
        "https://fusionxinvest.com/company-profile/10276/aspl-fusion/",
        "Confirms legal name, founders and staged program; directory evidence only.",
    ),
    "S027": (
        "SMART Fusion Energy creation",
        "University of Seville",
        "university primary",
        "2026-06-16",
        "https://www.us.es/actualidad-de-la-us/smart-fusion-energy-nace-para-acelerar-la-llegada-de-la-fusion-nuclear",
        "Confirms spin-out, founders and transferred technology.",
    ),
    "S028": (
        "SMART Fusion Energy investment",
        "Cinco Dias",
        "independent media",
        "2026-06-16",
        "https://cincodias.elpais.com/companias/2026-06-16/el-fondo-beable-inyecta-15-millones-en-el-spin-off-de-energia-de-fusion-de-la-universidad-de-sevilla.html",
        "Independent formation/funding coverage; reactor claims remain prospective.",
    ),
    "S029": (
        "TRINITI institute profile",
        "JSC SRC RF TRINITI",
        "official",
        "2026",
        "https://www.triniti.ru/en/company/",
        "Official identity and research scope.",
    ),
    "S030": (
        "Rosatom fusion technology overview",
        "Rosatom",
        "state-corporate primary",
        "2024",
        "https://fusion.rosatom.ru/upload/iblock/0e6/0e61e9f3e42871096bb6628f5ed1d472.pdf",
        "State-program context; not independent validation of a commercial reactor.",
    ),
}

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


def c(
    i: int,
    n: str,
    a: str,
    cl: str,
    co: str,
    yr: int | str,
    st: str,
    ap: str,
    pr: str,
    claim: str,
    tier: str,
    mile: str,
    gap: str,
    primary: str,
    ind: str,
    ids: str,
    dates: str,
    conf: str,
    why: str,
) -> dict[str, str]:
    """Serialize one reviewed discovery record without promoting its claims.

    Parameters
    ----------
    i : int
        Local sequential candidate number.
    n : str
        Recorded organization identity.
    a : str
        Declared aliases separated by semicolons.
    cl : str
        Conservative organization classification.
    co : str
        Recorded country.
    yr : int or str
        Founding year or qualified date text.
    st : str
        Recorded activity status.
    ap : str
        Approach family with stated limitations.
    pr : str
        Named devices or proposed projects.
    claim : str
        Company-supplied claim separated from independent findings.
    tier : str
        Evidence classification and its qualification.
    mile : str
        Highest independently supported bounded milestone.
    gap : str
        Unsupported or ambiguous assertions retained explicitly.
    primary : str
        Recorded primary source link.
    ind : str
        Recorded independent source links.
    ids : str
        Referenced source registry identifiers.
    dates : str
        Record-specific evidence dates.
    conf : str
        Curated confidence level.
    why : str
        Discovery inclusion rationale.

    Returns
    -------
    dict of str
        Original ordered candidate schema with a stable local FC2 identifier.
    """
    return dict(
        zip(
            FIELDS,
            [
                f"FC2-{i:03d}",
                n,
                a,
                cl,
                co,
                str(yr),
                st,
                ap,
                pr,
                claim,
                tier,
                mile,
                gap,
                primary,
                ind,
                ids,
                dates,
                DATE,
                conf,
                why,
            ],
            strict=True,
        )
    )


C = [
    c(
        1,
        "Dongsheng Fusion",
        "Shanghai Dongsheng Fusion; Dongsheng Jubian; 东昇聚变",
        "fusion reactor/device developer",
        "China",
        2025,
        "active; first device announced",
        "magnetic confinement | high-field compact tokamak | D-He3 goal",
        "Chenguang project",
        "Company proposes a compact high-field tokamak using deuterium-helium-3 and reports starting its first experimental device.",
        "C — incorporation, financing and program corroborated; no device result",
        "Investor and independent reporting corroborate formation, university lineage, financing and Chenguang project start.",
        "No independently verified plasma, temperature, confinement, fusion-yield or gain milestone; D-He3 fuel-cycle feasibility and schedule are prospective.",
        SOURCES["S001"][4],
        SOURCES["S002"][4],
        "S001;S002",
        "Qiming 2026-08; Sina 2026-06-11",
        "medium",
        "Major 2025 Chinese entrant omitted from the first 69 records.",
    ),
    c(
        2,
        "Xeonova",
        "Hefei Star Energy Xuanlight Technology; Star Energy Xuanlight; Xingneng Xuanguang; 星能玄光",
        "fusion reactor/device developer",
        "China",
        2024,
        "active; prototype program",
        "linear magnetic confinement | FRC plus tandem mirror/electrostatic plugs",
        "Xeonova-1",
        "Company reports an FRC discharge in Xeonova-1 and proposes modular D-T or advanced-fuel power systems.",
        "B/C — physical prototype publicly documented; performance remains company-led",
        "Official material and independent industry reporting support the existence of Xeonova-1 and an early discharge program.",
        "Plasma parameters, confinement quality, fusion reactions, gain, direct conversion and 2035 plant targets are not independently validated.",
        SOURCES["S003"][4],
        SOURCES["S004"][4],
        "S003;S004",
        "official site accessed 2026-09-27; industry analysis 2026-09",
        "medium",
        "Chinese FRC/mirror company with a named device and durable official site.",
    ),
    c(
        3,
        "Hanhai Energy",
        "HHMAX-Energy; Hanhai Fusion; 瀚海聚能",
        "fusion reactor/device developer",
        "China",
        2022,
        "active; experimental device operating at plasma-formation stage",
        "pulsed magneto-inertial fusion | colliding/compressed FRC",
        "HHMAX-901",
        "Company reports HHMAX-901 first plasma in July 2025 and aims to scale a Helion-like linear FRC system.",
        "B/C — device existence and public first-plasma event; no fusion performance validation",
        "Multiple public sources support construction of HHMAX-901 and a plasma-lighting event; this establishes an operating plasma apparatus only.",
        "Temperature, density, confinement, collision/compression performance, fusion yield, recovery and net energy remain unsupported.",
        SOURCES["S005"][4],
        SOURCES["S006"][4],
        "S005;S006",
        "official chronology 2025-2026; directory updated 2026-09-11",
        "medium",
        "Substantive Chinese FRC developer absent from prior catalogs.",
    ),
    c(
        4,
        "Chaoci Xineng",
        "Chaoci New Energy; 超磁新能",
        "fusion magnet supplier/integrator; not a reactor developer",
        "China",
        2025,
        "active",
        "high-temperature-superconducting high-field magnets",
        "25 T-class toroidal-field model magnet program",
        "Company is developing a 25 T-class HTS toroidal-field model magnet and demountable joints for fusion systems.",
        "B/C — partner-confirmed component manufacturing; integrated qualification pending",
        "A named REBCO supplier confirms pancake-coil batch production and low-resistance joint sample testing.",
        "Full 25 T magnet assembly, structural endurance, irradiation tolerance and reactor deployment are not yet independently demonstrated.",
        SOURCES["S007"][4],
        SOURCES["S008"][4],
        "S007;S008",
        "partner release 2026-08-21; industry report 2026-07",
        "medium",
        "Clearly separable Chinese fusion supply-chain company; excluded from developer counts.",
    ),
    c(
        5,
        "Zhongke Qingneng",
        "中科清能",
        "fusion cryogenic-system supplier; not a reactor developer",
        "China",
        2016,
        "active",
        "large helium cryogenic refrigeration systems",
        "3 kW at 4.5 K refrigerator; CRAFT cryogenic work",
        "Company supplies cryogenic systems intended for superconducting fusion facilities.",
        "B/C — commissioned component reported; company-specific public documentation limited",
        "Independent industry research reports commissioning of a 3 kW at 4.5 K refrigerator for CRAFT-related use.",
        "Broader delivery record, long-duration reliability and any implication of reactor performance remain outside the evidence.",
        SOURCES["S010"][4],
        SOURCES["S009"][4],
        "S009;S010",
        "industry reports 2025-11 and 2026-09",
        "low",
        "Important Chinese upstream supplier, explicitly separated from reactor developers.",
    ),
    c(
        6,
        "LINEA Innovations",
        "LINEA Innovations Inc.; 株式会社LINEAイノベーション",
        "fusion reactor/device developer",
        "Japan",
        2023,
        "active; design and component R&D",
        "magnetic confinement | FRC/mirror hybrid | p-B11 long-term",
        "beam-assisted FRC demonstration program",
        "Company proposes a beam-supported FRC/mirror system and long-term proton-boron operation.",
        "B/C — government ecosystem recognition; no integrated device result",
        "Japanese government/patent-landscape sources and company releases establish the program and conditional 2026 demonstration-program selection.",
        "Plasma performance, p-B11 feasibility, gain and 2030s electricity targets remain prospective.",
        SOURCES["S011"][4],
        SOURCES["S012"][4],
        "S011;S012",
        "official site accessed 2026-09-27; JPO report 2026-03",
        "high",
        "Current Japanese reactor startup missing from both earlier catalogs.",
    ),
    c(
        7,
        "Starlight Engine",
        "Starlight Engine Ltd.; SLE",
        "fusion project company/developer",
        "Japan",
        2025,
        "active; conceptual design completed",
        "magnetic confinement | HTS tokamak integrated power demonstration",
        "FAST",
        "Company leads FAST and targets an integrated fusion-electricity demonstration in the 2030s.",
        "B — legal entity, partnerships and conceptual design independently corroborated",
        "Parent and independent industrial-partner releases confirm establishment, project leadership, financing participation and completion of a conceptual design.",
        "D-T plasma performance, tritium self-sufficiency, heat extraction, net electricity and schedule are not demonstrated.",
        SOURCES["S013"][4],
        SOURCES["S014"][4],
        "S013;S014",
        "entity launch 2025-04-16; partner investment 2026-07-15",
        "high",
        "Distinct project company created after the original audit; not merely an alias of Kyoto Fusioneering.",
    ),
    c(
        8,
        "MiRESSO",
        "MiRESSO Co. Ltd.; 株式会社MiRESSO",
        "fusion materials supplier; not a reactor developer",
        "Japan",
        2023,
        "active; pilot plant development",
        "low-temperature beryllium refining and recycling",
        "BETA pilot plant",
        "Company aims to produce affordable beryllium for fusion blankets using sub-300 °C refining.",
        "A/B — government-certified spin-out with funded demonstration program",
        "QST confirms spin-out certification, scope and founding; Japanese government material documents the FY2023-2027 refining demonstration.",
        "Commercial-scale output, cost, purity and blanket qualification remain future milestones; this is not a fusion reactor program.",
        SOURCES["S015"][4],
        SOURCES["S016"][4],
        "S015;S016",
        "official site accessed 2026-09-27; QST listing current 2026",
        "high",
        "High-value Japanese supplier explicitly excluded from developer totals.",
    ),
    c(
        9,
        "Eterna Fusion",
        "Eterna Fusion Co. Ltd.; 이터나퓨전",
        "fusion reactor/device developer",
        "South Korea",
        2026,
        "active; proof-of-concept stage",
        "magnetic confinement | tokamak current-drive injection",
        "COSMOS concept; Tokamak Injection proof of concept",
        "Company proposes continuous external current drive for a compact modular tokamak.",
        "C — incorporation, team and funding corroborated; no device result",
        "Independent Korean sources corroborate March 2026 incorporation, seed funding and a planned proof-of-concept program.",
        "Continuous plasma sustainment, device construction, fusion performance and commercial power claims remain untested.",
        SOURCES["S017"][4],
        SOURCES["S018"][4],
        "S017;S018",
        "Maeil 2026-07-06; registry profile accessed 2026-09-27",
        "high",
        "New Korean reactor startup established after the earlier catalogs.",
    ),
    c(
        10,
        "EnableFusion",
        "EnableFusion Inc.",
        "fusion engineering platform/supplier; not a reactor developer",
        "South Korea",
        2023,
        "active",
        "fusion engineering platform | HTS, precision manufacturing and AI integration",
        "Fusion Engineering Platform",
        "Company offers an engineering platform intended to connect Korean manufacturing capabilities with fusion developers.",
        "C — active company and national ecosystem context; project deliveries not independently enumerated",
        "Official materials establish the platform scope; Korean government policy confirms the relevant private-sector ecosystem.",
        "No independent evidence found for a company fusion device or specific delivered reactor milestone; do not count it as a reactor developer.",
        SOURCES["S019"][4],
        SOURCES["S020"][4],
        "S019;S020",
        "official site accessed 2026-09-27; MSIT strategy 2024",
        "medium",
        "Korean supply-chain integrator included with explicit non-developer classification.",
    ),
    c(
        11,
        "Quasarus",
        "Quasarus Private Limited",
        "fusion R&D organization; pre-hardware",
        "India",
        2026,
        "active; newly incorporated",
        "fusion modelling and engineering constraints; approach not yet fixed",
        "simulation workflows; subsystem studies",
        "Company states it will establish reproducible models before advancing to subsystem hardware.",
        "C — official early-stage identity; no independent technical milestone",
        "Public company materials establish a 2026 Indian R&D entrant; independent reporting establishes the surrounding Indian fusion-startup ecosystem only.",
        "Confinement approach, device, funding, performance and schedule are not yet sufficiently public.",
        SOURCES["S021"][4],
        SOURCES["S022"][4],
        "S021;S022",
        "official site accessed 2026-09-27; Mint report 2026-07",
        "low",
        "Recent Indian entrant retained conservatively as pre-hardware R&D.",
    ),
    c(
        12,
        "Hylenr Technologies",
        "Hylenr Technologies Private Limited; HYLENR",
        "speculative non-mainstream nuclear claim",
        "India",
        2024,
        "active claims; independent physics validation absent",
        "LENR/lattice-confinement excess-heat and transmutation claims",
        "BRT-NiUCS reactors; HYTHERM concepts",
        "Company claims reproducible excess heat, fusion and elemental transmutation in hydrogen-loaded metal lattices.",
        "D — claim-led; no broadly accepted independent validation",
        "Independent business reporting confirms the company and funding, but no transparent peer-reviewed replication establishes nuclear energy production.",
        "COP 1.8, fusion mechanism, transmutation, scaling to MW systems and absence of radiation/waste remain unsupported.",
        SOURCES["S023"][4],
        SOURCES["S024"][4],
        "S023;S024",
        "official site accessed 2026-09-27; Mint report 2026-07",
        "low",
        "Prominent Indian LENR entrant, explicitly segregated from mainstream fusion.",
    ),
    c(
        13,
        "ASPL Fusion",
        "Agnira Sanlayan Private Limited; Project Sanlayan",
        "applied plasma/neutron systems company; fusion is long-term",
        "India",
        2025,
        "active; early engineering stage",
        "accelerator/plasma neutron systems; advanced magnetic mirror long-term",
        "medical-isotope and BNCT systems; future mirror program",
        "Company explicitly prioritizes near-term neutron and isotope infrastructure, with fusion-class applications only as a long-horizon phase.",
        "C — corporate identity and stated scope corroborated; no fusion device",
        "Official positioning and an independent specialist profile corroborate legal identity, incubation and staged non-power work.",
        "No fusion reactor, plasma-performance or energy milestone is claimed or independently demonstrated.",
        SOURCES["S025"][4],
        SOURCES["S026"][4],
        "S025;S026",
        "official pages and specialist profile accessed 2026-09-27",
        "medium",
        "Indian organization often marketed as fusion; classification prevents near-term reactor misattribution.",
    ),
    c(
        14,
        "SMART Fusion Energy",
        "SMART Fusion Energy Sociedad Limitada; SFE",
        "fusion reactor/device developer",
        "Spain",
        2026,
        "active; university spin-out",
        "magnetic confinement | compact negative-triangularity spherical tokamak | HTS",
        "SMART research platform; HTSMART; proposed BRIGHT pilot",
        "Company proposes transferring University of Seville SMART tokamak research into compact commercial reactor designs.",
        "B — incorporation and technology transfer documented; company hardware milestone not yet separate",
        "University records confirm formation, founders, transferred IP and an operating university SMART research platform.",
        "SMART results belong to the university program; company-attributable HTS device, neutron source, gain and grid schedule remain prospective.",
        SOURCES["S027"][4],
        SOURCES["S028"][4],
        "S027;S028",
        "University and Cinco Dias reports 2026-06-16",
        "high",
        "New European university spin-out formed after the original catalog.",
    ),
    c(
        15,
        "JSC SRC RF TRINITI",
        "Troitsk Institute for Innovation and Fusion Research; JSC TRINITI; ГНЦ РФ ТРИНИТИ",
        "state research operator; not a private commercial reactor developer",
        "Russia",
        1956,
        "active state research institute",
        "magnetic and inertial fusion research; plasma and high-energy-density physics",
        "T-11M tokamak and institutional laser/plasma facilities",
        "Institute conducts controlled-fusion and plasma research within Rosatom's scientific division.",
        "A/B — long-running state research institution and facilities",
        "Official institute and Rosatom records establish active fusion/plasma R&D and state-program role.",
        "Do not classify institutional experiments or national plans as a private commercial reactor claim; current facility-by-facility performance was not re-audited here.",
        SOURCES["S029"][4],
        SOURCES["S030"][4],
        "S029;S030",
        "official institute site accessed 2026-09-27; Rosatom overview 2024",
        "high",
        "Adds a Russian/CIS public industrial-research actor while preserving category boundaries.",
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
        Company audit root with both earlier persisted catalogs.

    Returns
    -------
    set of str
        Normalized primary names and nonblank declared aliases.

    Raises
    ------
    ValueError
        If a previous primary identity or alias is invalid or duplicated.
    """
    protected: set[str] = set()
    for name, fields, key in (
        ("audited_companies.tsv", AUDIT_FIELDS, "company"),
        ("expansion_candidates.tsv", FIRST_FIELDS, "organization"),
    ):
        rows = read(directory / name, fields)
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
        for name in ("audited_companies.tsv", "expansion_candidates.tsv")
    }
    outputs = [args.output_directory / name for name in ("candidates.tsv", "source_registry.tsv")]
    if inputs & {path.resolve() for path in outputs}:
        print("BUILD FAILED: output would replace a protected input")
        raise SystemExit(1)
    try:
        protected = read_protected(args.audit_root)
        check_identities(C, protected)
        sources = [
            dict(zip(SF, [sid, *values, DATE], strict=True))
            for sid, values in sorted(SOURCES.items())
        ]
        args.output_directory.mkdir(parents=True, exist_ok=True)
        write(outputs[0], FIELDS, C)
        write(outputs[1], SF, sources)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"BUILD FAILED: {error}")
        raise SystemExit(1) from None
    print(f"wrote {len(C)} candidates and {len(SOURCES)} source records")


if __name__ == "__main__":
    main()
