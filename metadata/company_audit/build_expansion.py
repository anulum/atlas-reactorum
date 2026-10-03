#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/build_expansion.py
"""Build a conservative, deduplicated expansion-candidate register."""

from __future__ import annotations

import argparse
import csv
from collections.abc import Mapping, Sequence
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDITED = HERE / "audited_companies.tsv"
OUT = HERE / "expansion_candidates.tsv"
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
    "official_url",
    "independent_urls",
    "source_dates",
    "audit_date",
    "confidence",
    "inclusion_rationale",
]

FIA = "https://www.fusionindustryassociation.org/wp-content/uploads/2025/07/2025-Global-Fusion-Industry-Report.pdf"
UKAEA = "https://www.ukaea.org/wp-content/uploads/2026/04/ukaea-global-fusion-guide-smes.pdf"


def row(
    i: int,
    n: str,
    a: str,
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
    official: str,
    independent: str,
    dates: str,
    confidence: str,
    why: str,
) -> dict[str, str]:
    """Serialize one reviewed discovery record while preserving claim limits.

    Parameters
    ----------
    i : int
        Local sequential FCX candidate number.
    n : str
        Declared organization identity.
    a : str
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
    official : str
        Recorded primary source link.
    independent : str
        Recorded independent source links.
    dates : str
        Record-specific source dates.
    confidence : str
        Curated confidence level.
    why : str
        Discovery inclusion rationale.

    Returns
    -------
    dict of str
        Original candidate schema with a stable local FCX identifier.
    """
    return dict(
        zip(
            FIELDS,
            [
                f"FCX-{i:03d}",
                n,
                a,
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
                official,
                independent,
                dates,
                "2026-09-27",
                confidence,
                why,
            ],
            strict=True,
        )
    )


R = [
    row(
        1,
        "Anubal Fusion",
        "Anubal Fusion Pvt Ltd",
        "fusion reactor/device developer",
        "India",
        2024,
        "active; early stage",
        "laser inertial fusion | direct-drive p-B11",
        "proposed petawatt-laser experiment and interim plant",
        "Company proposes direct laser-driven proton-boron fusion and direct conversion.",
        "C — company profile and industry-registry evidence only",
        "FIA 2025 records the company and its self-reported program; no independently replicated reactor milestone located.",
        "Neutron yield, gain, pilot date and economics remain company claims.",
        "https://anubalfusion.com/",
        FIA,
        "official material accessed 2026-09-27; FIA report 2025-07",
        "low",
        "Named 2025 FIA profile absent from the 51-row audit.",
    ),
    row(
        2,
        "Helicity Space",
        "Helicity Space Corporation",
        "fusion propulsion/device developer",
        "United States",
        2018,
        "active",
        "pulsed magneto-inertial fusion | plectoneme plasma",
        "prototype propulsion/power experiments",
        "Company proposes compact fusion propulsion and later power systems.",
        "C — company and industry-registry evidence; no power milestone",
        "Company existence, team and laboratory program are documented; no independently verified fusion gain.",
        "Plasma performance, propulsion performance and 300 MWe extrapolation remain unverified.",
        "https://www.helicityspace.com/",
        FIA,
        "official material accessed 2026-09-27; FIA report 2025-07",
        "medium",
        "Current FIA-profiled space-fusion developer absent from the audit.",
    ),
    row(
        3,
        "Horne Technologies",
        "Horne Technologies LLC",
        "fusion reactor/device developer",
        "United States",
        2008,
        "active",
        "hybrid magnetic/electrostatic confinement | spindle cusp and shielded-grid IEC",
        "Horne Hybrid Reactor; Generation 2; Icarus",
        "Company reports first plasma in a dual-confinement prototype and proposes modular neutron and power systems.",
        "B/C — device existence independently catalogued; performance mainly company-reported",
        "IAEA 2022 device survey listed the Horne Hybrid Reactor as under construction; public evidence supports prototype activity, not reactor gain.",
        "First-plasma quality, fusion rate, continuous-operation capability and commercial schedule lack independent technical validation.",
        "https://www.hornetechnologies.com/",
        "https://www-pub.iaea.org/MTCD/publications/PDF/CRCP-FUS-001webRev.pdf; " + FIA,
        "IAEA device survey 2022; FIA report 2025-07; official site accessed 2026-09-27",
        "medium",
        "IAEA/FIA-listed developer absent from the audit.",
    ),
    row(
        4,
        "LaserFusionX",
        "LaserFusionX Inc.",
        "fusion reactor/device developer",
        "United States",
        2022,
        "active; early stage",
        "laser inertial fusion | ArF deep-UV direct drive",
        "proposed 30 kJ ArF beamline; prototype plant",
        "Company claims ArF wavelength can enable high-gain direct drive with lower driver energy.",
        "B/C — underlying NRL science is published; company hardware milestone not established",
        "Peer-reviewed NRL-origin ArF/direct-drive studies support the physics research basis; the company itself has not demonstrated an integrated fusion device.",
        "Projected target gain, laser efficiency, repetition rate, tritium breeding and plant economics are simulations/design claims.",
        "https://laserfusionx.net/",
        FIA,
        "official site accessed 2026-09-27; FIA report 2025-07",
        "medium",
        "Current FIA-profiled laser-fusion developer absent from the audit.",
    ),
    row(
        5,
        "Maritime Fusion",
        "Maritime Fusion Inc.",
        "fusion reactor/device developer",
        "United States",
        2024,
        "active; early stage",
        "magnetic confinement | low-power-density HTS tokamak",
        "Yinsen marine/off-grid reactor study",
        "Company proposes 25 MWe-class HTS tokamaks for ships and off-grid markets.",
        "C — conceptual design/company and industry-registry evidence",
        "FIA 2025 documents the venture; a public Yinsen preprint supports that a design study exists, not that hardware operates.",
        "Breakeven, lifetime blanket, maritime licensing, cost and deployment dates are prospective.",
        "https://www.maritimefusion.com",
        FIA,
        "official material accessed 2026-09-27; FIA report 2025-07",
        "medium",
        "Current FIA-profiled developer absent from the audit.",
    ),
    row(
        6,
        "Novatron Fusion Group",
        "Novatron Fusion Group AB; Novatron Fusion",
        "fusion reactor/device developer",
        "Sweden",
        2019,
        "active",
        "magnetic confinement | open magnetic mirror",
        "Novatron 1; proposed Novatron 2/3/4",
        "Company proposes an axisymmetric mirror system and staged path to a pilot plant.",
        "C — operating R&D project reported; performance not independently established",
        "Independent ecosystem and industry sources document Novatron 1 and the company program; no fusion gain milestone is established.",
        "Confinement scaling, stability, 1.5 GWe commercial design and 2034 pilot timing remain projections.",
        "https://novatronfusion.com/",
        FIA,
        "official site accessed 2026-09-27; FIA report 2025-07",
        "medium",
        "Current FIA-profiled mirror developer absent from the audit.",
    ),
    row(
        7,
        "Pranos Fusion",
        "Pranos Fusion Energy Pvt Ltd",
        "fusion reactor/device developer",
        "India",
        2024,
        "active; early stage",
        "magnetic confinement | spherical tokamak",
        "planned modular 50 MW reactor; coil and vacuum R&D",
        "Company proposes modular spherical-tokamak power units.",
        "C — company/industry-registry evidence only",
        "FIA 2025 supports company identity and an engineering-stage program; no operating company tokamak was independently located.",
        "50 MW module, timelines, plasma performance and economics are prospective.",
        "https://pranosfusion.energy/",
        FIA,
        "official material accessed 2026-09-27; FIA report 2025-07",
        "low",
        "Current FIA-profiled Indian developer absent from the audit.",
    ),
    row(
        8,
        "Pulsar Fusion",
        "Pulsar Fusion Ltd.",
        "fusion propulsion/device developer",
        "United Kingdom",
        2011,
        "active",
        "pulsed magnetic confinement | direct fusion drive/space propulsion",
        "Duel direct fusion drive experimental program",
        "Company targets nuclear-fusion propulsion and reports a 2026 first-plasma milestone.",
        "C — public prototype reporting; no independently measured propulsion or gain result",
        "Independent reporting corroborates a first-plasma event in 2026; it does not establish fusion reactions, thrust or energy gain.",
        "Fusion yield, net thrust, flight readiness and power performance remain unverified.",
        "https://pulsarfusion.com/",
        "https://www.techradar.com/pro/the-future-of-space-will-look-less-like-single-use-expeditionary-missions-and-more-like-a-transport-network-pulsar-fusions-quest-to-build-a-nuclear-fusion-exhaust-system-for-deep-space-travel-hits-first-plasma-milestone; "
        + FIA,
        "first-plasma report 2026-04-22; FIA report 2025-07; official site accessed 2026-09-27",
        "medium",
        "Current FIA-profiled propulsion developer absent from the audit.",
    ),
    row(
        9,
        "Startorus Fusion",
        "Shaanxi Startorus Fusion Technology Co.; StarTorch Fusion",
        "fusion reactor/device developer",
        "China",
        2021,
        "active",
        "magnetic confinement | pulsed HTS spherical tokamak and magnetic-reconnection heating",
        "SUNIST-linked research; H850 magnet; planned next-step device",
        "Company proposes repetitive-pulse compact spherical tokamaks and reports full-scale HTS magnet tests.",
        "B/C — independent recognition and research lineage; company reactor performance not yet established",
        "IEA 2026 independently identifies Startorus and its negative-triangularity/HTS work; public evidence supports magnet engineering and SUNIST lineage, not reactor gain.",
        "Company-attributable plasma performance, target gain, schedule and economics remain prospective.",
        "https://startorus.com/",
        "https://www.iea.org/reports/the-state-of-energy-innovation-2026; " + FIA,
        "FIA report 2025-07; IEA report 2026-02-17; official site accessed 2026-09-27",
        "high",
        "Major current Chinese developer independently recognized by IEA and omitted from the audit.",
    ),
    row(
        10,
        "Terra Fusion Energy Corporation",
        "Terra Fusion; TF Energy",
        "fusion reactor/device developer",
        "United States",
        2024,
        "active; early stage",
        "magnetic confinement | centrifugal magnetic mirror",
        "CMFX-derived commercial concept",
        "Company proposes commercial systems derived from the University of Maryland Baltimore County centrifugal mirror experiment.",
        "B/C — university/ARPA-E physics platform exists; company commercialization is conceptual",
        "The ARPA-E-supported CMFX research platform establishes the technical lineage; no company net-energy device exists.",
        "Commercial scale-up, 5–100 MWe units and 2032 pilot timing are projections.",
        "https://tf.energy/",
        FIA,
        "official material accessed 2026-09-27; FIA report 2025-07",
        "medium",
        "Current FIA-profiled mirror spinout absent from the audit.",
    ),
    row(
        11,
        "Tibbar Plasma Technologies",
        "Tibbar Technologies; Tibbar Plasma Technologies LLC",
        "fusion reactor/device developer",
        "United States",
        2015,
        "active status not independently confirmed",
        "hybrid electrostatic/magnetic confinement | p-B11 aspiration",
        "tabletop prototypes; proposed pilot",
        "Company proposes magnetic-electrostatic confinement and direct conversion using proton-boron fuel.",
        "C — industry-profile and limited technical trail",
        "FIA 2025 documents the organization and self-reported program; no independently validated reactor milestone located.",
        "Fusion yield, confinement performance, direct conversion and 2030 pilot claim remain unverified.",
        "https://tibbartech.com/",
        FIA,
        "official/registry material accessed 2026-09-27; FIA report 2025-07",
        "low",
        "FIA-profiled venture absent from the audit; retained with status caveat.",
    ),
    row(
        12,
        "GenF",
        "GenF SAS; GenF Systems",
        "fusion reactor/device developer",
        "France",
        2024,
        "active",
        "laser inertial fusion | DT direct drive",
        "laser and target modelling; planned experiments at CEA/CNRS facilities",
        "Company proposes an industrial laser-driven inertial-fusion reactor.",
        "B/C — corporate and public-research partnership independently documented; no company fusion shot",
        "CNRS/Thales material confirms company formation and institutional collaboration; no integrated company device or gain result exists.",
        "Pilot schedule, repetition rate, target cost, net electricity and 1 GWe plant claim remain prospective.",
        "https://genf-systems.com/",
        "https://www.cnrs.fr/sites/default/files/press_info/2025-05/Communiqu%C3%A9%20de%20presse_GenF_15mai_VDef.pdf; "
        + FIA,
        "CNRS/Thales release 2025-05; FIA report 2025-07; official site accessed 2026-09-27",
        "high",
        "Current French developer formed after much of the original discovery baseline.",
    ),
    row(
        13,
        "Inertia",
        "Inertia Enterprises Inc.",
        "fusion reactor/device developer",
        "United States",
        2025,
        "active",
        "laser inertial fusion | indirect drive",
        "commercial target/laser design; LLNL LIFT collaboration",
        "Company proposes a 10 MJ high-repetition laser and mass-produced targets for a 1.5 GWe plant.",
        "B/C — LLNL collaboration and inherited NIF physics basis; company performance is modeled",
        "LLNL confirms a 2026 partnership on laser technology, targets and designs; NIF ignition is a government-lab milestone, not an Inertia device milestone.",
        "Claimed >25 target gain is simulation-based; 10 Hz operation, target cost and plant output are not demonstrated.",
        "https://inertia.com/",
        "https://www.llnl.gov/article/54261/llnl-partners-inertia-develop-fusion-energy-technology",
        "LLNL release 2026-04-14; official site accessed 2026-09-27",
        "high",
        "New 2025 company with a 2026 national-laboratory partnership; absent from original audit.",
    ),
    row(
        14,
        "NovaFusionX",
        "Shanghai NovaFusionX Energy Technology Co.; Nova Fusion",
        "fusion reactor/device developer",
        "China",
        2025,
        "active; device under assembly",
        "pulsed magneto-inertial fusion | colliding FRC | small modular reactor concept",
        "Nova 1",
        "Company reports component prototypes and plans first plasma for Nova 1 by end-2026.",
        "B/C — government-zone reporting confirms company, financing and assembly; no plasma milestone yet",
        "Shanghai Lin-gang government reporting confirms Nova 1 final assembly and component prototypes as of 2026; first plasma is still a target.",
        "100 million °C in 2027, Q>1 in 2029 and 50–100 MW plant in 2030–35 are company projections.",
        "https://www.novafusionx.com/",
        "https://www.lingang.gov.cn/html/website/lg/English/News1630758253379031042/Updates/2097854259582238722.html; "
        + UKAEA,
        "Lin-gang government update 2026; UKAEA guide 2026-04; official material accessed 2026-09-27",
        "high",
        "Substantive post-2025 Chinese entrant independently documented by government and UKAEA.",
    ),
    row(
        15,
        "Fusion Power Corporation",
        "FPC",
        "historical/dormant fusion developer",
        "United States",
        2011,
        "dormant or inactive; website retained",
        "heavy-ion inertial fusion | RF accelerator driver",
        "heavy-ion fusion power-plant concept",
        "Website claims known accelerator and target technology could deliver fusion power.",
        "C-H — historical concept; no current development evidence",
        "A historical website and industry lists establish the venture; no recent operating program or integrated result was located.",
        "Claimed near-term delivery was not achieved; current corporate status and all performance claims are unverified.",
        "https://fusionpowercorporation.com/",
        "https://en.wikipedia.org/wiki/List_of_nuclear_fusion_companies",
        "official website copyright 2011 and accessed 2026-09-27; secondary list accessed 2026-09-27",
        "low",
        "Historical venture omitted from the audit; included to prevent mistaken treatment as current.",
    ),
    row(
        16,
        "Leonardo Corporation",
        "E-Cat; Energy Catalyzer; Leonardo Corp.",
        "speculative non-mainstream nuclear claim",
        "United States / Italy",
        "2008",
        "active claims; scientific validation absent",
        "LENR/cold-fusion-like nickel-hydrogen energy claim",
        "E-Cat SKLep; claimed industrial thermoelectric plant",
        "Company claims self-sustaining excess electricity/heat from E-Cat systems.",
        "D — claim-led; no broadly accepted independent validation",
        "No convincing independent, reproducible nuclear-energy demonstration located; published critiques identify measurement and independence problems.",
        "Self-sustain, excess energy, nuclear mechanism, product availability and grid-scale operation remain unsupported.",
        "https://ecatthenewfire.com/",
        "https://arxiv.org/abs/1306.6364",
        "company update 2026-05; critical analysis 2013; audited 2026-09-27",
        "low",
        "Prominent omitted LENR venture; explicitly segregated from mainstream fusion.",
    ),
    row(
        17,
        "General Atomics Magnetic Fusion Energy",
        "General Atomics Fusion; GA Fusion",
        "public-program operator and fusion technology supplier; not a standalone private power-plant developer",
        "United States",
        1955,
        "active",
        "magnetic confinement research/engineering | tokamak",
        "DIII-D National Fusion Facility; ITER central solenoid and diagnostics",
        "General Atomics operates DIII-D for DOE and supplies major ITER components and fusion diagnostics.",
        "A — government-verified operating facility and delivered engineering work",
        "DOE confirms GA operates DIII-D under a 2025–2028 cooperative agreement; GA's role is research/operator/supplier, not a claimed private commercial reactor demonstration.",
        "Do not classify DIII-D research results or ITER component delivery as a GA commercial fusion-power plant.",
        "https://ga.com/magnetic-fusion/",
        "https://www.energy.gov/nepa/articles/cx-034320-funding-extension-diii-d-national-fusion-facility-research-and-operations",
        "DOE extension dated 2025-07-24; official site accessed 2026-09-27",
        "high",
        "Large industrial fusion actor omitted because the original list focused on startups; classification prevents category error.",
    ),
    row(
        18,
        "Oxford Sigma",
        "Oxford Sigma Ltd.",
        "fusion materials supplier/integrator; not a reactor developer",
        "United Kingdom",
        2019,
        "active",
        "fusion materials engineering, testing and qualification",
        "advanced materials manufacturing and qualification programs",
        "Company provides advanced-materials technology and engineering for fusion and other extreme environments.",
        "B — current supplier activity corroborated by UKAEA",
        "UKAEA program material documents Oxford Sigma participation in fusion shielding/materials activity; no confinement reactor is claimed.",
        "Do not count supplier contracts or materials facilities as reactor or fusion-gain milestones.",
        "https://oxfordsigma.com/",
        "https://indico.ukaea.uk/event/720/page/339-agenda",
        "UKAEA event 2026-04-29; official site accessed 2026-09-27",
        "high",
        "Clearly classified supply-chain company useful to the atlas without inflating developer counts.",
    ),
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


def read_protected(path: Path) -> set[str]:
    """Read the required original audit before generating discovery candidates.

    Parameters
    ----------
    path : pathlib.Path
        Original audited-company table with its exact producer schema.

    Returns
    -------
    set of str
        Normalized company names and nonblank declared aliases.

    Raises
    ------
    ValueError
        If primaries duplicate or any company/alias has no usable identity.
    """
    rows = read(path, AUDIT_FIELDS)
    primary = [norm(row["company"]) for row in rows]
    if any(not value for value in primary) or len(set(primary)) != len(primary):
        raise ValueError("protected audit has blank or duplicate primary identities")
    protected: set[str] = set()
    for row in rows:
        for value in [row["company"], *row["aliases"].split(";")]:
            if value.strip():
                normalized = norm(value)
                if not normalized:
                    raise ValueError("protected audit has invalid alias")
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
    """Check original audited identities before writing the expansion output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audited", type=Path, default=AUDITED)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    if args.output.resolve() == args.audited.resolve():
        print("BUILD FAILED: output would replace protected audit")
        raise SystemExit(1)
    try:
        check_identities(R, read_protected(args.audited))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write(args.output, FIELDS, R)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"BUILD FAILED: {error}")
        raise SystemExit(1) from None
    print(f"wrote {len(R)} rows to {args.output}")


if __name__ == "__main__":
    main()
