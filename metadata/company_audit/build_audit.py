#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/build_audit.py
"""Build the fusion-company audit from the frozen discovery candidate set.

The candidate file is treated as an identity register, not as verified evidence.
Overrides below record findings from the 2026-09-26 source review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "metadata/discovery_audit/fusion_companies_candidates.tsv"
OUT = Path(__file__).resolve().parent / "audited_companies.tsv"

INTEGRATORS = {
    "Kyoto Fusioneering": "fusion-plant technology integrator/supplier",
    "SHINE Technologies": "commercial fusion-neutron/isotope company; power aspirant",
    "EX-Fusion": "inertial-fusion enabling-technology developer",
    "Gauss Fusion": "power-plant engineering consortium/developer",
    "Astral Systems": "fusion-neutron/isotope platform developer; not a power developer",
}
SPECULATIVE = {"Brillouin Energy", "Clean Planet", "ENG8 International", "Aureon Energy"}
HISTORICAL = {
    "CTFusion": "closed (reported 2023); historical developer",
    "HyperJet Fusion": "acquired by General Fusion (2023); no longer standalone",
    "EMC2 Fusion Development Corporation": "dormant/status unverified; historical developer",
    "Lockheed Martin Compact Fusion Reactor program": "dormant/no current public program found",
    "Deutelio": "status unverified; no current public program found",
}
UNCERTAIN = {"Alpha Ring", "MIFTI", "Electric Fusion Systems", "Crossfield Fusion", "Stellarex"}

STATUS = {
    "General Fusion": "active; publicly listed as General Fusion Group (Nasdaq: GFUZ since 2026-07)",
    "First Light Fusion": "active; strategy changed in 2025 and FLARE architecture launched",
    "China Fusion Energy Corporation": "active; state-controlled company established 2025",
    "Neo Fusion": "active; state-backed commercialization company",
    "Energy Singularity": "active; HH70 operating",
    "ENN Fusion": "active; experimental program and Helong-2 construction",
    **HISTORICAL,
}

APPROACH = {
    "Commonwealth Fusion Systems": "magnetic confinement | high-field compact tokamak | D-T",
    "TAE Technologies": "magnetic confinement | beam-driven FRC | H-B11 long-term",
    "Helion Energy": "pulsed magneto-inertial | colliding FRC | direct electricity recovery",
    "General Fusion": "magnetized-target fusion | liquid-metal liner compression",
    "Tokamak Energy": "magnetic confinement | spherical tokamak | HTS magnets",
    "Zap Energy": "pulsed magnetic confinement | sheared-flow-stabilized Z pinch",
    "Type One Energy": "magnetic confinement | optimized stellarator | HTS magnets",
    "Thea Energy": "magnetic confinement | planar-coil stellarator",
    "Realta Fusion": "magnetic confinement | axisymmetric mirror | HTS magnets",
    "Pacific Fusion": "pulsed magnetic inertial fusion | pulsed-power driver",
    "Xcimer Energy": "laser inertial fusion | KrF excimer driver",
    "Focused Energy": "laser inertial fusion | proton fast ignition/direct drive",
    "Marvel Fusion": "laser inertial fusion | short-pulse laser/nanostructured target",
    "Renaissance Fusion": "magnetic confinement | stellarator | HTS/liquid-metal wall",
    "Proxima Fusion": "magnetic confinement | quasi-isodynamic stellarator",
    "Gauss Fusion": "magnetic confinement plant concept | tokamak engineering",
    "First Light Fusion": "inertial fusion | pulsed-power compression/fast ignition (FLARE)",
    "HB11 Energy": "laser fusion | proton-boron",
    "OpenStar Technologies": "magnetic confinement | levitated dipole",
    "Avalanche Energy": "electrostatic/beam-target fusion | Orbitron neutron source",
    "LPPFusion": "dense plasma focus | proton-boron aspiration",
    "Princeton Fusion Systems": "magnetic confinement | RF-heated FRC/PFRC",
    "SHINE Technologies": "accelerator beam-target D-T neutron generation",
    "NearStar Fusion": "projectile-driven magneto-inertial fusion",
    "Longview Fusion Energy Systems": "laser inertial fusion | direct drive",
    "Blue Laser Fusion": "laser inertial fusion | blue-laser driver",
    "EX-Fusion": "laser inertial fusion enabling systems | target tracking/control",
    "Helical Fusion": "magnetic confinement | helical/heliotron stellarator",
    "Kyoto Fusioneering": "blanket/tritium/thermal cycle and fusion plant engineering",
    "Energy Singularity": "magnetic confinement | all-HTS compact tokamak",
    "ENN Fusion": "magnetic confinement | spherical torus/FRC | H-B11 goal",
    "Neo Fusion": "magnetic confinement | tokamak engineering/BEST commercialization",
    "China Fusion Energy Corporation": "state fusion engineering/pilot-plant development; approach not yet fully disclosed",
    "nT-Tao": "compact pulsed magnetic confinement | proprietary topology",
    "Alpha Ring": "proprietary electrostatic/beam-fusion concept",
    "Acceleron Fusion": "muon-catalyzed fusion | accelerator muon source",
    "Fuse Energy Technologies": "pulsed-power Z pinch/neutron and radiation platforms",
    "MIFTI": "staged Z pinch | magneto-inertial fusion",
    "Electric Fusion Systems": "proprietary magneto-electric confinement",
    "Crossfield Fusion": "proprietary compact cross-field magnetic confinement",
    "Astral Systems": "lattice-confinement-fusion claimed DT neutron platform",
    "Brillouin Energy": "LENR claim | nickel-hydrogen excess heat",
    "Clean Planet": "LENR claim | metal-hydride anomalous heat",
    "ENG8 International": "LENR/plasma-electrolysis claimed catalyzed fusion",
    "Aureon Energy": "plasma-discharge transmutation/excess-energy claim",
    "CTFusion": "magnetic confinement | spheromak/dynomak",
    "HyperJet Fusion": "plasma-jet magneto-inertial fusion",
    "EMC2 Fusion Development Corporation": "electrostatic confinement | Polywell",
    "Lockheed Martin Compact Fusion Reactor program": "high-beta magnetic mirror/cusp concept",
    "Deutelio": "magnetic confinement | D-T tokamak concept",
    "Stellarex": "stellarator-related concept; undisclosed",
}

OFFICIAL = {
    "Energy Singularity": "https://energysingularity.cn/en/",
    "SHINE Technologies": "https://www.shinefusion.com/",
    "EX-Fusion": "https://ex-fusion.com/",
    "Astral Systems": "https://www.astralsystems.com/",
    "Neo Fusion": "",
    "China Fusion Energy Corporation": "",
}
INDEPENDENT = {
    "Commonwealth Fusion Systems": "https://www.energy.gov/articles/us-department-energy-announces-selectees-107-million-fusion-innovation-research-engine; https://doi.org/10.1109/TASC.2023.3332613",
    "Focused Energy": "https://www.energy.gov/articles/us-department-energy-announces-selectees-107-million-fusion-innovation-research-engine; https://www.energy.gov/nepa/articles/cx-030451-inertial-fusion-energy-high-gain-proton-fast-ignition",
    "Realta Fusion": "https://www.energy.gov/articles/us-department-energy-announces-selectees-107-million-fusion-innovation-research-engine",
    "Thea Energy": "https://www.energy.gov/articles/us-department-energy-announces-selectees-107-million-fusion-innovation-research-engine",
    "Zap Energy": "https://arpa-e.energy.gov/news-and-events/news-and-insights/arpa-e-investor-update-vol-23-zap-energys-fusion-power-plant-demo; https://www.energy.gov/articles/us-department-energy-announces-selectees-107-million-fusion-innovation-research-engine",
    "Energy Singularity": "https://english.shanghai.gov.cn/en-Latest-WhatsNew/20240621/282f58e13a1c4b9797beaa31c2309f41.html; https://doi.org/10.1016/j.supcon.2024.100112",
    "China Fusion Energy Corporation": "https://fusionforenergy.europa.eu/wp-content/uploads/2025/11/F4E_Observatory_2025_digital.pdf",
    "Neo Fusion": "https://fusionforenergy.europa.eu/wp-content/uploads/2025/11/F4E_Observatory_2025_digital.pdf",
    "Astral Systems": "https://www.nasa.gov/glenn/glenn-expertise-space-exploration/lattice-confinement-fusion/; https://www.ukaea.org/about-ukaea/publications/global-fusion-guide-for-smes/",
    "First Light Fusion": "https://www.gov.uk/government/publications/uk-fusion-investment-prospectus/uk-fusion-investment-prospectus-directory-html",
}

MILESTONE = {
    "Commonwealth Fusion Systems": "peer-reviewed 20 T-class large-bore HTS magnet demonstration; SPARC construction independently documented",
    "TAE Technologies": "operated Norman/C-2 series with peer-reviewed FRC plasma results",
    "Helion Energy": "multiple pulsed FRC prototypes operated; no independent net-electricity result",
    "General Fusion": "LM26 constructed and operating per company/public-company disclosures; earlier subsystems independently documented",
    "Tokamak Energy": "ST40 operated with peer-reviewed high-temperature plasma results; HTS magnet hardware tested",
    "Zap Energy": "FuZE/FuZE-Q plasma results peer reviewed; Century operation reported by US ARPA-E",
    "Type One Energy": "DOE-selected design program; component/design work, no operating company fusion device",
    "Thea Energy": "DOE independently reviewed completion of equilibrium-selection and planar HTS-coil milestones",
    "Realta Fusion": "DOE independently reviewed whole-device mirror-model milestone; WHAM platform exists at UW-Madison",
    "Focused Energy": "DOE independently reviewed high-gain target-model and ion-beam-focusing milestones",
    "Energy Singularity": "HH70 first plasma corroborated by Shanghai government; magnet system described in peer-reviewed literature",
    "ENN Fusion": "operated XuanLong/EXL-class experimental devices with scholarly publications",
    "China Fusion Energy Corporation": "company formation and state capitalization independently documented; no attributable reactor milestone",
    "Neo Fusion": "company/program and BEST commercialization role independently documented; no standalone device result attributed",
    "First Light Fusion": "laboratory projectile/target experiments and published papers; no net-energy result",
    "Astral Systems": "NASA-established LCF research basis and public UK ecosystem recognition; company performance claims not independently validated",
    "Kyoto Fusioneering": "public component-test facilities and peer-reviewed blanket/tritium/thermal engineering work; not a confinement device",
    "SHINE Technologies": "commercial accelerator D-T neutron generation and regulated isotope activity; no fusion-power reactor",
    "CTFusion": "historical Dynomak concept and university studies; company reported closed in 2023",
    "HyperJet Fusion": "PLX/plasma-jet hardware and peer-reviewed research; acquired, no standalone power result",
}


def identity_class(name: str) -> str:
    """Classify a reviewed identity without treating its category as performance evidence.

    Parameters
    ----------
    name : str
        Exact original discovery identity.

    Returns
    -------
    str
        Original bounded review wording without scientific promotion.
    """
    if name in SPECULATIVE:
        return "speculative non-mainstream nuclear claim"
    if name in HISTORICAL:
        return "historical/inactive fusion developer"
    if name in INTEGRATORS:
        return INTEGRATORS[name]
    if name == "China Fusion Energy Corporation":
        return "state-controlled fusion developer"
    return "fusion reactor/device developer"


def tier(name: str, maturity: str) -> str:
    """Assign the original conservative evidence tier for a bounded milestone.

    Parameters
    ----------
    name : str
        Exact original discovery identity.
    maturity : str
        Original discovery evidence-maturity text.

    Returns
    -------
    str
        Original bounded review wording without scientific promotion.
    """
    if name in SPECULATIVE:
        return "D — claim-led; no broadly accepted independent validation"
    if name in HISTORICAL:
        return "C-H — historical technical evidence; current activity absent/unclear"
    if name in UNCERTAIN:
        return "C — limited current independent technical evidence"
    if "peer-reviewed" in maturity.lower() or name in {
        "Zap Energy",
        "Energy Singularity",
        "Thea Energy",
        "Realta Fusion",
        "Focused Energy",
        "SHINE Technologies",
        "Kyoto Fusioneering",
    }:
        return "B — independent/government or peer-reviewed support for a bounded milestone"
    return "C — public program/company evidence; claimed performance not independently verified"


def milestone(name: str, r: Mapping[str, str]) -> str:
    """Retain the reviewed override or original discovery maturity wording.

    Parameters
    ----------
    name : str
        Exact original discovery identity.
    r : mapping of str to str
        Original discovery record retained with its review context.

    Returns
    -------
    str
        Original bounded review wording without scientific promotion.
    """
    if name in MILESTONE:
        return MILESTONE[name]
    return r["evidence_maturity"]


def unsupported(name: str, r: Mapping[str, str]) -> str:
    """Retain explicit performance, status and attribution limits for a reviewed identity.

    Parameters
    ----------
    name : str
        Exact original discovery identity.
    r : mapping of str to str
        Original discovery record retained with its review context.

    Returns
    -------
    str
        Original bounded review wording without scientific promotion.
    """
    if name in SPECULATIVE:
        return "claimed excess heat/transmutation or commercial energy output lacks broadly accepted independent replication and complete nuclear-product/energy accounting"
    if name in HISTORICAL:
        return "current operating status and any reactor-scale performance; historical power timelines were not demonstrated"
    if name in {"Kyoto Fusioneering", "SHINE Technologies", "EX-Fusion", "Astral Systems"}:
        return "do not interpret component, neutron-source, isotope, or enabling-system progress as fusion-power gain or a power-reactor demonstration"
    if name in {"China Fusion Energy Corporation", "Neo Fusion", "Stellarex"}:
        return "specific architecture, company-attributable hardware results, performance and schedule remain insufficiently public"
    return "commercial dates, plant economics and any Q/net-electricity implication beyond the independently supported milestone remain company projections"


def normalized_status(name: str, r: Mapping[str, str]) -> str:
    """Select the original review status without implying verified device performance.

    Parameters
    ----------
    name : str
        Exact original discovery identity.
    r : mapping of str to str
        Original discovery record retained with its review context.

    Returns
    -------
    str
        Original bounded review wording without scientific promotion.
    """
    if name in STATUS:
        return STATUS[name]
    if name in UNCERTAIN:
        return "current activity plausible but status/performance not independently confirmed"
    return "active"


SOURCE_FIELDS = [
    "company",
    "aliases",
    "country",
    "founded",
    "active_status",
    "approach",
    "devices/projects",
    "claimed_milestones",
    "evidence_maturity",
    "publications_or_patents",
    "official_url",
    "independent_source_url",
    "registry_sources",
    "last_verified",
]

FIELDS = [
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


class AuditSummary(TypedDict):
    """Original deterministic JSON counts for the generated company audit.

    Attributes
    ----------
    audit_date : str
        Fixed source-review date.
    input_records : int
        Number of accepted discovery records.
    output_records : int
        Number of generated audit records.
    unique_companies : int
        Number of distinct exact identities.
    identity_classes : dict of str to int
        Counts of original conservative classifications.
    evidence_tiers : dict of str to int
        Counts of original bounded evidence tiers.
    confidence : dict of str to int
        Counts of original confidence labels.
    """

    audit_date: str
    input_records: int
    output_records: int
    unique_companies: int
    identity_classes: dict[str, int]
    evidence_tiers: dict[str, int]
    confidence: dict[str, int]


def read_candidates(path: Path) -> list[dict[str, str]]:
    """Read the actual discovery register with its original ordered schema.

    Parameters
    ----------
    path : pathlib.Path
        Discovery TSV containing identities and unverified claim context.

    Returns
    -------
    list of dict
        Original discovery rows, preserving claim and source text.

    Raises
    ------
    ValueError
        If schema, presence or row structure is invalid.
    """
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if reader.fieldnames != SOURCE_FIELDS:
            raise ValueError("discovery header mismatch")
        rows = list(reader)
    if not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError("discovery table empty or malformed")
    return rows


def build_rows(candidates: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    """Project original discovery records through the preserved review overrides.

    Parameters
    ----------
    candidates : sequence of mappings of str to str
        Complete actual discovery records with the SOURCE_FIELDS schema.

    Returns
    -------
    list of dict
        Original seventeen-column bounded review rows in discovery order.

    Raises
    ------
    ValueError
        If schema, primary identities or required claim context is invalid.
    """
    if not candidates or any(set(row) != set(SOURCE_FIELDS) for row in candidates):
        raise ValueError("discovery record schema mismatch or empty input")
    names = ["".join(c for c in row["company"].casefold() if c.isalnum()) for row in candidates]
    if (
        any(not name for name in names)
        or len(set(names)) != len(names)
        or any(row["company"] != row["company"].strip() for row in candidates)
    ):
        raise ValueError("blank, duplicate or padded discovery identity")
    required = ("country", "approach", "claimed_milestones", "evidence_maturity")
    if any(not row[field].strip() for row in candidates for field in required):
        raise ValueError("blank required discovery claim context")
    rows: list[dict[str, str]] = []
    for r in candidates:
        n = r["company"]
        rows.append(
            {
                "company": n,
                "aliases": r["aliases"],
                "founded": r["founded"],
                "identity_class": identity_class(n),
                "normalized_status": normalized_status(n, r),
                "country": r["country"],
                "approach_family": APPROACH.get(n, r["approach"]),
                "public_devices_projects": r["devices/projects"],
                "company_claim_summary": r["claimed_milestones"],
                "evidence_tier": tier(n, r["evidence_maturity"]),
                "highest_independently_supported_milestone": milestone(n, r),
                "unsupported_or_ambiguous_claims": unsupported(n, r),
                "official_url": OFFICIAL.get(n, r["official_url"]),
                "independent_urls": INDEPENDENT.get(n, r["independent_source_url"]),
                "source_dates": "official page accessed 2026-09-26; independent sources 2023-2026; FIA register 2025-07; UKAEA guide 2026-04 where used",
                "audit_date": "2026-09-26",
                "confidence": "high"
                if tier(n, r["evidence_maturity"]).startswith("B")
                else ("low" if n in SPECULATIVE | UNCERTAIN or n in HISTORICAL else "medium"),
            }
        )
    return rows


def summarize(rows: Sequence[Mapping[str, str]]) -> AuditSummary:
    """Count actual generated classifications in original JSON order.

    Parameters
    ----------
    rows : sequence of mappings of str to str
        Complete audit rows produced by build_rows.

    Returns
    -------
    AuditSummary
        Original deterministic record, identity, evidence and confidence counts.
    """
    return {
        "audit_date": "2026-09-26",
        "input_records": len(rows),
        "output_records": len(rows),
        "unique_companies": len({row["company"] for row in rows}),
        "identity_classes": dict(Counter(row["identity_class"] for row in rows)),
        "evidence_tiers": dict(Counter(row["evidence_tier"] for row in rows)),
        "confidence": dict(Counter(row["confidence"] for row in rows)),
    }


def main() -> None:
    """Validate and derive the full audit and summary before writing outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=SRC)
    parser.add_argument("--output-directory", type=Path, default=OUT.parent)
    args = parser.parse_args()
    outputs = [args.output_directory / name for name in ("audited_companies.tsv", "summary.json")]
    if args.input.resolve() in {path.resolve() for path in outputs}:
        print("BUILD FAILED: output would replace discovery input")
        raise SystemExit(1)
    try:
        rows = build_rows(read_candidates(args.input))
        summary = summarize(rows)
        args.output_directory.mkdir(parents=True, exist_ok=True)
        with outputs[0].open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        outputs[1].write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"BUILD FAILED: {error}")
        raise SystemExit(1) from None
    for path in outputs:
        print(hashlib.sha256(path.read_bytes()).hexdigest(), path.name)


if __name__ == "__main__":
    main()
