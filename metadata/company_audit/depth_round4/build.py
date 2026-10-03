#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/depth_round4/build.py
"""Build a deterministic 98-record completeness matrix and three exact-name overlays."""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATE = "2026-09-28"
INPUTS = [
    ("core_audit", ROOT / "audited_companies.tsv", "company", "AUD"),
    ("expansion_round1", ROOT / "expansion_candidates.tsv", "organization", "FC1"),
    ("expansion_round2", ROOT / "expansion_round2" / "candidates.tsv", "organization", "FC2"),
    ("expansion_round3", ROOT / "expansion_round3" / "candidates.tsv", "organization", "FC3"),
]
INPUT_FIELDS = {
    "core_audit": [
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
    ],
    "expansion_round1": [
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
    ],
    "expansion_round2": [
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
    ],
    "expansion_round3": [
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
    ],
}
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


def clean_tier(value: str) -> str:
    """Reduce an audit's bounded evidence tier to its published summary band.

    Parameters
    ----------
    value : str
        Original tier label including any scope or uncertainty qualifiers.

    Returns
    -------
    str
        Recognised A/B, B/C, C-H or A-D band, otherwise other.
    """
    value = value.strip()
    if value.startswith("A/B"):
        return "A/B"
    if value.startswith("B/C"):
        return "B/C"
    if value.startswith("C-H"):
        return "C-H"
    if value.startswith("A"):
        return "A"
    if value.startswith("B"):
        return "B"
    if value.startswith("C"):
        return "C"
    if value.startswith("D"):
        return "D"
    return "other"


def semantic_state(value: str, uncertainty: tuple[str, ...] = ()) -> str:
    """Classify disclosed field wording without asserting its scientific truth.

    Parameters
    ----------
    value : str
        Original audited field text.
    uncertainty : tuple of str
        Explicit case-insensitive uncertainty markers for this field.

    Returns
    -------
    str
        Missing for blank text, partial for a marker, otherwise complete.
    """
    if not value.strip():
        return "missing"
    low = value.casefold()
    return "partial" if any(term in low for term in uncertainty) else "complete"


def fuel_cycle(record: Mapping[str, str]) -> str:
    """Extract explicit fuel terms while retaining unspecified isotope limits.

    Parameters
    ----------
    record : mapping of str to str
        Audited approach, claim, device and unsupported-claim wording.

    Returns
    -------
    str
        Disclosed fuel labels or an explicit unspecified-isotope statement.
    """
    text = " ".join(
        record.get(k, "")
        for k in (
            "approach_family",
            "company_claim_summary",
            "public_devices_projects",
            "unsupported_or_ambiguous_claims",
        )
    ).casefold()
    fuels = []
    patterns = [
        ("D-T", r"\bd[ -]?t\b|deuterium[ -]tritium|deuterium and tritium|deuterium-tritium"),
        ("D-He3", r"d[ -]?(?:he3|3he)|deuterium[ -]helium[ -]?3"),
        ("p-B11", r"p[ -]?b11|h[ -]?b11|proton[ -]boron|hydrogen[ -]boron|hydrogen-boron"),
        ("D-D", r"\bd[ -]?d\b|deuterium[ -]deuterium"),
    ]
    for label, pat in patterns:
        if re.search(pat, text):
            fuels.append(label)
    if "aneutronic" in text and not fuels:
        fuels.append("aneutronic fuel claimed; isotope not explicit")
    return "; ".join(fuels) if fuels else "not publicly specified in audited record"


def build_matrix(root: Path) -> list[dict[str, str]]:
    """Build completeness and priority rows from four source audit tables.

    Parameters
    ----------
    root : pathlib.Path
        Company-audit directory containing the four original catalogs.

    Returns
    -------
    list of dict
        Source wording with derived completeness, gap and priority columns.
    """
    rows: list[dict[str, str]] = []
    for catalog, input_path, namecol, prefix in INPUTS:
        path = root / input_path.relative_to(ROOT)
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh, delimiter="\t", strict=True)
            if reader.fieldnames != INPUT_FIELDS[catalog]:
                raise ValueError(f"{catalog}: unexpected source schema")
            records = list(reader)
        if not records or any(None in r or None in r.values() for r in records):
            raise ValueError(f"{catalog}: empty or malformed source rows")
        for index, r in enumerate(records, 1):
            rid = r.get("candidate_id") or f"{prefix}-{index:03d}"
            official = r.get("official_url", r.get("primary_url", ""))
            independent = r.get("independent_urls", "")
            fuel = fuel_cycle(r)
            states = {
                "status": semantic_state(
                    r["normalized_status"],
                    ("unverified", "unclear", "plausible", "no current public program found"),
                ),
                "identity": semantic_state(r["identity_class"], ("unclear", "unclassified")),
                "approach": semantic_state(
                    r["approach_family"],
                    (
                        "undisclosed",
                        "not yet fixed",
                        "not yet fully",
                        "not fully disclosed",
                        "approach not",
                        "insufficiently public",
                        "details evolving",
                    ),
                ),
                "device": semantic_state(
                    r["public_devices_projects"],
                    (
                        "undisclosed",
                        "not stable",
                        "details evolving",
                        "not publicly",
                        "unclear",
                    ),
                ),
                "fuel_cycle": "complete"
                if fuel != "not publicly specified in audited record"
                else "missing",
                "milestone": semantic_state(
                    r["highest_independently_supported_milestone"],
                    (
                        "no maturity inference",
                        "no attributable",
                        "not independently",
                        "insufficient",
                        "no known company device",
                    ),
                ),
                "unsupported_claims": semantic_state(r["unsupported_or_ambiguous_claims"]),
                "official_url": semantic_state(official),
                "independent_source": semantic_state(independent),
                "source_date": semantic_state(r["source_dates"], ("where used", "2023-2026")),
                "country": semantic_state(r["country"]),
                "confidence": semantic_state(r["confidence"]),
            }
            gaps = [key for key, val in states.items() if val != "complete"]
            active_dev = "developer" in r["identity_class"].casefold() and (
                re.search(r"\bactive\b", r["normalized_status"].casefold()) is not None
                or "current activity plausible" in r["normalized_status"].casefold()
            )
            weights = {
                "status": 2,
                "identity": 2,
                "approach": 2,
                "device": 2,
                "fuel_cycle": 1,
                "milestone": 3,
                "unsupported_claims": 2,
                "official_url": 2,
                "independent_source": 3,
                "source_date": 1,
                "country": 2,
                "confidence": 1,
            }
            score = sum(weights[g] for g in gaps) + (3 if active_dev else 0)
            band = "high" if score >= 7 else "medium" if score >= 4 else "low"
            values = [
                rid,
                catalog,
                str(index),
                r[namecol],
                r["country"],
                r["identity_class"],
                r["normalized_status"],
                r["approach_family"],
                r["public_devices_projects"],
                fuel,
                r["highest_independently_supported_milestone"],
                r["unsupported_or_ambiguous_claims"],
                official,
                independent,
                r["source_dates"],
                r["confidence"],
                clean_tier(r["evidence_tier"]),
                *[
                    states[k] + ("" if states[k] == "complete" else ": review")
                    for k in (
                        "status",
                        "identity",
                        "approach",
                        "device",
                        "fuel_cycle",
                        "milestone",
                        "unsupported_claims",
                        "official_url",
                        "independent_source",
                        "source_date",
                        "country",
                        "confidence",
                    )
                ],
                str(len(gaps)),
                str(score),
                band,
                ";".join(gaps),
            ]
            rows.append(dict(zip(MATRIX_FIELDS, values, strict=False)))
    return rows


OVERLAY_FIELDS = [
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
]
OVERLAYS = [
    dict(
        zip(
            OVERLAY_FIELDS,
            [
                "Neo Fusion",
                "exact normalized organization name",
                "AUD-030",
                "identity_class;normalized_status;country;approach_configuration;named_devices_projects;fuel_cycle;highest_independently_supported_milestone;unsupported_or_ambiguous_claims;independent_urls;source_dates",
                "state-backed fusion engineering and commercialization company; BEST construction entity",
                "active; BEST under assembly/procurement; no standalone company power result",
                "China",
                "magnetic confinement | fully superconducting tokamak | BEST engineering/commercialization",
                "BEST (Compact Fusion Energy Experimental Device)",
                "D-T planned for BEST; tritium use is prospective",
                "Government procurement records and 2026 public-authority reporting independently identify Neo Fusion's Chinese legal entity as BEST's construction/procurement entity and document active ECRH procurement; this supports project execution, not plasma performance.",
                "BEST completion, D-T operation, fusion-energy output and electricity remain future programme targets; EAST results must not be attributed to Neo Fusion or BEST.",
                "",
                "https://chinabidding.mofcom.gov.cn/bidDetail/bidding/bulletin/202601/ff8080819a82040b019c0dc5f55c092a.html; https://www.cppcc.gov.cn/zxww/2026/03/03/ARTI1772505878945258.shtml; https://www.mee.gov.cn/xxgk2018/xxgk/xxgk06/202504/t20250407_1106558.html",
                "N01;N02;N03",
                "procurement result 2026-01-30; CPPCC 2026-03-03; MEE 2025-04-07",
                DATE,
                "high",
                "No standalone official company website was located; official_url deliberately remains blank rather than substituting a government news page.",
            ],
            strict=False,
        )
    ),
    dict(
        zip(
            OVERLAY_FIELDS,
            [
                "China Fusion Energy Corporation",
                "exact normalized organization name",
                "AUD-031",
                "identity_class;normalized_status;country;approach_configuration;named_devices_projects;fuel_cycle;highest_independently_supported_milestone;unsupported_or_ambiguous_claims;official_url;independent_urls;source_dates",
                "CNNC tier-two state-owned fusion engineering and commercialization company",
                "active; established 2025; system-design, technical-validation and digital-R&D stage",
                "China",
                "compact high-temperature-superconducting magnetic-confinement programme; exact plant configuration not publicly fixed",
                "no independently identified company-operated device; design and validation platforms announced",
                "D-T described for the public compact magnetic-confinement route; company-specific fuel-cycle design undisclosed",
                "CNNC and Shanghai government sources confirm incorporation, ownership level, shareholders and declared system-design/technical-validation remit; a national standards registry confirms participation in drafting magnetic-confinement reactor safety guidance.",
                "No company-attributable device, plasma, fuel-cycle, gain or electricity milestone is public; capitalisation and institutional mandate are not performance evidence.",
                "https://en.cnnc.com.cn/2025-07/31/c_1113670.htm",
                "https://english.shanghai.gov.cn/en-Latest-WhatsNew/20250728/33aaf405e8ca4ec38bdb1a67ea2c7919.html; https://std.samr.gov.cn/gb/search/gbDetailed?id=3DB7CF64C79689D5E06397BE0A0A3E46",
                "C01;C02;C03",
                "CNNC 2025-07-31; Shanghai government 2025-07-23; SAMR registered 2025-09-01",
                DATE,
                "high",
                "Parent-company official announcement is used as the official URL; no standalone CFEC site was found.",
            ],
            strict=False,
        )
    ),
    dict(
        zip(
            OVERLAY_FIELDS,
            [
                "Stellarex",
                "exact normalized organization name",
                "AUD-051",
                "aliases;identity_class;normalized_status;country;approach_configuration;named_devices_projects;fuel_cycle;highest_independently_supported_milestone;unsupported_or_ambiguous_claims;official_url;independent_urls;source_dates",
                "fusion reactor/device developer; Princeton spinout with Canadian programme",
                "active as Stellarex Energy / Stellarex Group; funded Canadian prototype programme",
                "Canada / United States",
                "magnetic confinement | simplified stellarator | staged demonstration devices",
                "unnamed staged prototype/demonstration devices; Ontario Centre for Fusion Energy programme",
                "D-T programme context supported by tritium partnerships; exact device fuel plan not public",
                "Ontario government independently confirms a funded Centre for Fusion Energy partnership and an intended Stellarex prototype; OPG independently corroborates stellarator-development and prospective siting work. No Stellarex plasma device has yet been demonstrated.",
                "Device names, final configuration, construction status, plasma performance, net energy and deployment schedule remain undisclosed or prospective.",
                "https://stellarex.energy/",
                "https://news.ontario.ca/en/release/1006788/ontario-investing-195-million-to-establish-the-centre-for-fusion-energy; https://www.opg.com/releases/opg-and-stellarex-to-explore-fusion-energy-for-ontario/",
                "S01;S02;S03",
                "official site accessed 2026-09-28; Ontario release 2025-12; OPG 2024-06-07",
                DATE,
                "high",
                "Overlay preserves the exact catalog identity while recording current Stellarex Energy branding and Canadian programme; partnership/funding does not validate reactor performance.",
            ],
            strict=False,
        )
    ),
]
# Stable IDs are assigned from the 51-row core audit at build time.
for overlay in OVERLAYS:
    overlay["source_record_id"] = {
        "Neo Fusion": "AUD-032",
        "China Fusion Energy Corporation": "AUD-033",
        "Stellarex": "AUD-051",
    }[overlay["organization"]]

SOURCES = {
    "N01": (
        "BEST ECRH gyrotron procurement result",
        "China International Bidding / Ministry of Commerce platform",
        "government procurement record",
        "2026-01-30",
        "https://chinabidding.mofcom.gov.cn/bidDetail/bidding/bulletin/202601/ff8080819a82040b019c0dc5f55c092a.html",
        "Names Neo Fusion (Anhui) as procuring entity; confirms procurement, not system operation.",
    ),
    "N02": (
        "Interview with Neo Fusion chairman on BEST construction",
        "National Committee of the Chinese People's Political Consultative Conference",
        "public-authority news",
        "2026-03-03",
        "https://www.cppcc.gov.cn/zxww/2026/03/03/ARTI1772505878945258.shtml",
        "Confirms chairman and active BEST role; target statements remain participant claims.",
    ),
    "N03": (
        "Notice on radiation-safety management of fusion facilities",
        "Ministry of Ecology and Environment of China",
        "government regulation",
        "2025-04-07",
        "https://www.mee.gov.cn/xxgk2018/xxgk/xxgk06/202504/t20250407_1106558.html",
        "Independently establishes planned tritium use in the in-construction compact fusion device; no performance claim.",
    ),
    "C01": (
        "China Fusion Energy Co. Ltd established in Shanghai",
        "China National Nuclear Corporation",
        "parent-company primary",
        "2025-07-31",
        "https://en.cnnc.com.cn/2025-07/31/c_1113670.htm",
        "Confirms entity, ownership level and remit; no hardware performance.",
    ),
    "C02": (
        "Shanghai backs launch of China Fusion Energy",
        "Shanghai Municipal Government",
        "government independent",
        "2025-07-23",
        "https://english.shanghai.gov.cn/en-Latest-WhatsNew/20250728/33aaf405e8ca4ec38bdb1a67ea2c7919.html",
        "Corroborates launch and system-design/validation remit.",
    ),
    "C03": (
        "Safety guidelines for magnetic confinement fusion reactor",
        "National Standards Information Public Service Platform (SAMR)",
        "government standards registry",
        "2025-09-01",
        "https://std.samr.gov.cn/gb/search/gbDetailed?id=3DB7CF64C79689D5E06397BE0A0A3E46",
        "Confirms CFEC as drafting participant; a standards role is not a reactor milestone.",
    ),
    "S01": (
        "Stellarex Energy official site",
        "Stellarex Energy",
        "company primary",
        "accessed 2026-09-28",
        "https://stellarex.energy/",
        "Current branding, country focus and staged-device claims; self-reported.",
    ),
    "S02": (
        "Ontario investing $19.5 million to establish Centre for Fusion Energy",
        "Government of Ontario",
        "government independent",
        "2025-12",
        "https://news.ontario.ca/en/release/1006788/ontario-investing-195-million-to-establish-the-centre-for-fusion-energy",
        "Confirms partnership, public funding and intended prototype; not device construction or performance.",
    ),
    "S03": (
        "OPG and Stellarex to explore fusion energy for Ontario",
        "Ontario Power Generation",
        "independent utility partner",
        "2024-06-07",
        "https://www.opg.com/releases/opg-and-stellarex-to-explore-fusion-energy-for-ontario/",
        "Corroborates stellarator identity and prospective siting collaboration; MOU is not technical validation.",
    ),
}


def write(path: Path, fields: list[str], data: Sequence[Mapping[str, Any]]) -> None:
    """Write deterministic producer rows in their published column order.

    Parameters
    ----------
    path : pathlib.Path
        Destination TSV within the selected output directory.
    fields : list of str
        Ordered producer schema.
    data : sequence of mappings
        Actual derived or curated records without normalization of source text.
    """
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(data)


def summary(rows: list[dict[str, str]], field: str, path: Path) -> None:
    """Summarize completeness and priorities for one actual matrix dimension.

    Parameters
    ----------
    rows : list of dict
        Complete derived matrix, preserving source identities.
    field : str
        Country, identity_class or evidence_tier grouping column.
    path : pathlib.Path
        Summary output TSV.
    """
    groups = defaultdict(list)
    for r in rows:
        groups[r[field]].append(r)
    out = []
    for key, items in sorted(groups.items()):
        out.append(
            {
                field: key,
                "records": len(items),
                "complete_records": sum(int(x["gap_count"]) == 0 for x in items),
                "records_with_gaps": sum(int(x["gap_count"]) > 0 for x in items),
                "high_priority": sum(x["priority_band"] == "high" for x in items),
                "medium_priority": sum(x["priority_band"] == "medium" for x in items),
                "low_priority": sum(x["priority_band"] == "low" for x in items),
                "missing_fuel_cycle": sum(
                    x["fuel_cycle_completeness"].startswith("missing") for x in items
                ),
                "missing_official_url": sum(
                    x["official_url_completeness"].startswith("missing") for x in items
                ),
            }
        )
    write(
        path,
        [
            field,
            "records",
            "complete_records",
            "records_with_gaps",
            "high_priority",
            "medium_priority",
            "low_priority",
            "missing_fuel_cycle",
            "missing_official_url",
        ],
        out,
    )


def main() -> None:
    """Build persisted depth outputs from the explicitly selected audit root."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-root", type=Path, default=ROOT)
    parser.add_argument("--output-directory", type=Path, default=HERE)
    args = parser.parse_args()
    output = args.output_directory
    try:
        rows = build_matrix(args.audit_root)
        output.mkdir(parents=True, exist_ok=True)
        write(output / "gap_matrix.tsv", MATRIX_FIELDS, rows)
        write(output / "enrichment_overlays.tsv", OVERLAY_FIELDS, OVERLAYS)
        sf = [
            "source_id",
            "title",
            "publisher",
            "source_type",
            "source_date",
            "url",
            "scope_and_limitations",
            "accessed_on",
        ]
        write(
            output / "overlay_sources.tsv",
            sf,
            [
                dict(zip(sf, [sid, *vals, DATE], strict=False))
                for sid, vals in sorted(SOURCES.items())
            ],
        )

        summary(rows, "country", output / "summary_by_country.tsv")
        summary(rows, "identity_class", output / "summary_by_identity.tsv")
        summary(rows, "evidence_tier", output / "summary_by_evidence_tier.tsv")
    except (OSError, UnicodeError, csv.Error, ValueError, KeyError) as error:
        print(f"BUILD FAILED: {error}")
        raise SystemExit(1) from None
    print(
        f"wrote {len(rows)} matrix records, {len(OVERLAYS)} overlays and {len(SOURCES)} overlay sources"
    )


if __name__ == "__main__":
    main()
