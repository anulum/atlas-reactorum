#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/company_audit/depth_round5/build.py
"""Build deterministic round-5 exact-name enrichment overlays."""

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
    [
        "Alpha Ring",
        "exact normalized organization name",
        "AUD-035",
        "normalized_status;approach_configuration;named_devices_projects;fuel_cycle;highest_independently_supported_milestone;unsupported_or_ambiguous_claims;official_url;independent_urls;source_dates",
        "fusion research-device and prospective power-device developer",
        "active; current product pages and 2025-2026 IAEA contributions; performance not independently validated",
        "Taiwan / United States",
        "compact electrostatic/beam plasma systems; proprietary electron-catalyzed and proton-boron concepts",
        "Alpha-E tabletop research/education platform; Alpha-F prospective power research programme; Alpha-M medical ion-beam system in development",
        "Alpha-F is explicitly linked by the company to proton-boron fusion; Alpha-E operating fuel is not clearly disclosed in the audited public sources",
        "IAEA-hosted contributions establish that company-affiliated researchers presented Alpha-E experiments and preliminary charged-particle diagnostics. The authors state that further time-resolved and spectroscopic work is needed to confirm particle origin and energy. This supports an active experimental programme, not independently verified fusion yield or power.",
        "Alpha-E sales/installations, fusion-product interpretation, Alpha-F scalability, useful energy, gain and commercial deployment remain company claims or prospective. IAEA hosting and peer presentation are not independent replication.",
        "https://alpharing.com/",
        "https://conferences.iaea.org/event/450/contributions/40817/; https://conferences.iaea.org/event/392/contributions/37816/",
        "A01;A02;A03",
        "official technology page accessed 2026-09-28; IAEA FEC contribution 2025-10-18; IAEA technical-meeting contribution 2026-06-22",
        "2026-09-28",
        "medium-high",
        "Fuel is bounded by programme: p-B11 applies to Alpha-F, not automatically to Alpha-E. No independent performance validation was found.",
    ],
    [
        "MIFTI",
        "exact normalized organization name",
        "AUD-038",
        "normalized_status;approach_configuration;named_devices_projects;fuel_cycle;highest_independently_supported_milestone;unsupported_or_ambiguous_claims;official_url;independent_urls;source_dates",
        "fusion reactor/device developer",
        "active; published Double Eagle experiments in 2026 and announced ongoing LLNL-linked diagnostics/modeling work",
        "United States",
        "staged Z-pinch magneto-inertial fusion driven by multi-megaampere pulsed power",
        "Double Eagle 3.5 MA experimental campaigns; planned Quad Eagle 7 MA campaign; Zebra and Double Eagle are host pulsed-power machines, not proven company-owned reactors",
        "deuterium targets in reported Double Eagle experiments; D-T is the modeled prospective gain fuel",
        "A 2026 peer-reviewed Plasma Physics and Controlled Fusion paper reports argon/krypton liners imploding onto deuterium targets on Double Eagle, with neutron yields above 10^11. A DOE-hosted final report independently documents the MIFTI/FLASH collaboration and Double Eagle simulations. These are experimental and modeling milestones, not gain.",
        "The company-reported agreement with simulation, future 7 MA campaign, alpha heating, D-T gain, power-plant performance and commercial timelines remain unvalidated or prospective; neutron production does not establish net energy.",
        "https://miftifusion.com/",
        "https://doi.org/10.1088/1361-6587/ae66b6; https://www.osti.gov/servlets/purl/2337682",
        "M01;M02;M03",
        "company update 2026-07-22 and 2026-05-13; journal paper 2026; DOE final report 2026",
        "2026-09-28",
        "high",
        "The obsolete mifti.com catalog URL is replaced by the current official site. Host drivers are not represented as MIFTI-owned devices.",
    ],
    [
        "Electric Fusion Systems",
        "exact normalized organization name",
        "AUD-039",
        "normalized_status;approach_configuration;named_devices_projects;fuel_cycle;highest_independently_supported_milestone;unsupported_or_ambiguous_claims;official_url;independent_urls;source_dates",
        "historical fusion concept developer; company winding down",
        "inactive technical development; orderly corporate wind-down announced in 2026; no new research, investment or commercial engagements",
        "United States",
        "historical Light Element Electric Fusion (LEEF) electrically driven discharge concept",
        "historical compact pulsed-fusion / appliance-sized reactor concepts; no named independently documented operating device",
        "company pages describe a lithium-proton / lithium-ammonia working medium; exact demonstrated nuclear reaction was not independently established",
        "The current official transition notice establishes cessation of active development. No independent source located in this audit establishes a reproducible fusion reaction, calibrated yield, gain, or operating power device.",
        "Historical fusion, alpha/helium, appliance-scale power, cost and scalability statements are not independently validated. Archived team and technology pages must not be read as current activity or endorsement.",
        "https://electricfusionsystems.com/",
        "https://www.fusionindustryassociation.org/wp-content/uploads/2025/07/2025-Global-Fusion-Industry-Report.pdf",
        "E01;E02;E03",
        "transition notice accessed 2026-09-28 and copyright 2026; archived technology page accessed 2026-09-28; FIA report 2025-07",
        "2026-09-28",
        "high for wind-down; low for technical claims",
        "Explicit negative finding: no independently supported device or fusion-performance milestone was found. Closure of active development resolves status without validating prior claims.",
    ],
    [
        "Crossfield Fusion",
        "exact normalized organization name",
        "AUD-040",
        "identity_class;normalized_status;approach_configuration;named_devices_projects;fuel_cycle;highest_independently_supported_milestone;unsupported_or_ambiguous_claims;official_url;independent_urls;source_dates",
        "fusion fuel-cycle/isotope-separation technology developer; former compact-reactor developer",
        "active legal entity; reactor path discontinued after 2021 internal negative scalability finding; currently exploring hydrogen-isotope separation",
        "United Kingdom",
        "historical Epicyclotron compact cross-field concept; current application is hydrogen-isotope separation",
        "historical unnamed 2021 Epicyclotron-based device (company-reported); current isotope-separation R&D; no current power-reactor programme",
        "current work addresses hydrogen-isotope separation in the fusion fuel cycle; a specific reactor reaction/fuel is not disclosed in current public pages",
        "UK Companies House confirms an active legal entity and filings through 2026. The company itself reports that experiments and particle-in-cell modeling found its reactor would not scale to net gain and that it pivoted to isotope separation. No independent fusion-output measurement was located.",
        "The 2021 'working fusion device' is company-reported and lacks an independently located yield record. Legal activity does not establish technical activity, and current isotope-separation work is not a reactor-performance milestone.",
        "https://crossfieldfusion.com/",
        "https://find-and-update.company-information.service.gov.uk/company/12220468",
        "C01;C02;C03",
        "mission page accessed 2026-09-28; Companies House last statement 2026-08-21; UK prospectus 2026-09-14",
        "2026-09-28",
        "high for legal status/pivot; medium-low for historical device claim",
        "Identity is deliberately reclassified: the current public programme is fuel-cycle R&D, not development of a net-gain reactor.",
    ],
    [
        "Astral Systems",
        "exact normalized organization name",
        "AUD-041",
        "normalized_status;approach_configuration;named_devices_projects;fuel_cycle;highest_independently_supported_milestone;unsupported_or_ambiguous_claims;official_url;independent_urls;source_dates",
        "fusion-neutron/isotope platform developer; not a fusion-power developer",
        "active; Culham tenant and UK-government-listed commercial neutron/isotope developer",
        "United Kingdom",
        "lattice confinement fusion compact neutron-source modules",
        "compact LCF reactor modules; Small-Scale Experiment for Tritium Breeding (SSETB); isotope-production and irradiation systems",
        "D-T operations and tritium-production work are described in the 2026 UK government prospectus",
        "UKAEA independently confirms Astral's Culham tenancy and SSETB work. A 2026 government investment prospectus states commercial manufacturing, tritium production and more than 60 hours of simultaneous two-module D-T operation; because the prospectus is promotional and provides no metrology, the conservative supported milestone is active compact-neutron-source deployment and public-programme participation, with the D-T duration recorded as government-published but not independently measured.",
        "The 60-hour D-T duration, flux, isotope yields, system validation and commercial performance are not independently metrologically verified in the cited public record. None demonstrates fusion gain, net energy or electricity.",
        "https://www.astralsystems.com/",
        "https://www.gov.uk/government/news/kyoto-fusioneering-and-astral-systems-join-culham-fusion-hub; https://www.gov.uk/government/publications/uk-fusion-investment-prospectus/uk-fusion-investment-prospectus-directory-html",
        "S01;S02;S03",
        "official site accessed 2026-09-28; UKAEA release 2025-06-17; UK prospectus 2026-09-14",
        "2026-09-28",
        "high for status/programme; medium for performance",
        "Government publication is treated as corroboration of programme identity, not as independent instrument-level validation of company-supplied performance figures.",
    ],
    [
        "Deutelio",
        "exact normalized organization name",
        "AUD-050",
        "aliases;identity_class;normalized_status;country;approach_configuration;named_devices_projects;fuel_cycle;highest_independently_supported_milestone;unsupported_or_ambiguous_claims;official_url;independent_urls;source_dates",
        "fusion reactor concept developer",
        "active Swiss legal entity Deutelio AG / SA / Ltd.; technical programme remains pre-device in public evidence",
        "Switzerland",
        "Polomac poloidal magnetic-confinement concept",
        "proposed Polomac prototype; no publicly evidenced operating company device",
        "D-D is stated in the company's FIA survey response; no demonstrated fuel-cycle operation was found",
        "Swiss commercial-register-derived records confirm Deutelio AG was incorporated in 2024, remains active, and moved to Manno in 2025. A 2024 technical paper documents the Polomac concept. No independently documented constructed device, plasma or fusion result was located.",
        "Prototype construction, confinement performance, D-D operation, gain, economics and schedules remain conceptual or company claims. Publication of a company-authored design paper is not experimental validation.",
        "https://www.deutelio.com/",
        "https://www.moneyhouse.ch/en/company/deutelio-ag-3402618371; https://www.jtsp.eu/jtsp/article/download/32/28; https://thefusioncluster.com/wp-content/uploads/2023/08/FIA%E2%80%932023-FINAL.pdf",
        "D01;D02;D03",
        "commercial register entry 2024-04-05 and update 2025-10-08; technical paper 2024; FIA report 2023",
        "2026-09-28",
        "high for identity/status; medium for technical description",
        "Corrects the catalog's Croatia/inactive conflation. Current Deutelio AG is a Swiss entity; no evidence found that it is the historical Croatian entity or that it operates hardware.",
    ],
]

SOURCE_FIELDS = [
    "source_id",
    "organization",
    "title",
    "publisher",
    "source_type",
    "source_date",
    "url",
    "supports",
    "limitations",
    "accessed_on",
]
SOURCES = [
    [
        "A01",
        "Alpha Ring",
        "Technology",
        "Alpha Ring",
        "company primary",
        "accessed 2026-09-28",
        "https://alpharing.com/technology/",
        "Current Alpha-E, Alpha-F and Alpha-M programme descriptions; Alpha-F link to PB Fusion.",
        "Company claims; no independent performance validation.",
    ],
    [
        "A02",
        "Alpha Ring",
        "Charged fusion-product diagnostics poster",
        "IAEA Fusion Energy Conference",
        "company-authored conference contribution",
        "2025-10-18",
        "https://conferences.iaea.org/event/392/contributions/37816/",
        "Company-affiliated experimental contribution and cautious diagnostic interpretation.",
        "IAEA hosting and review do not constitute independent replication.",
    ],
    [
        "A03",
        "Alpha Ring",
        "Alpha-E compact platform contribution",
        "IAEA Technical Meeting",
        "company-authored conference contribution",
        "2026-06-22",
        "https://conferences.iaea.org/event/450/contributions/40817/",
        "Current Alpha-E research-platform identity and activity.",
        "Company-affiliated authors; no independent yield validation.",
    ],
    [
        "M01",
        "MIFTI",
        "Updates: Double Eagle paper and LLNL collaboration",
        "MIFTI Fusion",
        "company primary",
        "2026-05-13; 2026-07-22",
        "https://miftifusion.com/updates/",
        "Current activity, Double Eagle/Quad Eagle programme descriptions and fuel details.",
        "Company summary; future campaign and interpretation remain claims.",
    ],
    [
        "M02",
        "MIFTI",
        "Staged Z-pinch experiments on the Double Eagle pulsed-power driver",
        "Plasma Physics and Controlled Fusion",
        "peer-reviewed journal",
        "2026",
        "https://doi.org/10.1088/1361-6587/ae66b6",
        "Peer-reviewed deuterium-target experiments and neutron-yield report.",
        "Authors include company researchers; neutron yield is not energy gain.",
    ],
    [
        "M03",
        "MIFTI",
        "High-fidelity simulations of the staged Z-pinch platform: final technical report",
        "U.S. DOE OSTI",
        "government-hosted technical report",
        "2026",
        "https://www.osti.gov/servlets/purl/2337682",
        "Independent laboratory collaboration, Double Eagle simulations and prospective D-T modeling.",
        "Simulation report; does not validate net gain or power.",
    ],
    [
        "E01",
        "Electric Fusion Systems",
        "Company Transition Notice",
        "Electric Fusion Systems",
        "company primary",
        "2026 / accessed 2026-09-28",
        "https://electricfusionsystems.com/",
        "Explicit cessation of active technology development and orderly wind-down.",
        "Self-reported corporate status; no dissolution date stated.",
    ],
    [
        "E02",
        "Electric Fusion Systems",
        "Fusion Technology archive",
        "Electric Fusion Systems",
        "company primary archive",
        "accessed 2026-09-28",
        "https://electricfusionsystems.com/fusion-technology/",
        "Historical lithium-proton concept and vessel claims.",
        "Archived company claims; transition notice supersedes as current status.",
    ],
    [
        "E03",
        "Electric Fusion Systems",
        "The Global Fusion Industry in 2025",
        "Fusion Industry Association",
        "industry survey",
        "2025-07",
        "https://www.fusionindustryassociation.org/wp-content/uploads/2025/07/2025-Global-Fusion-Industry-Report.pdf",
        "Historical ecosystem listing before wind-down.",
        "Participant-derived survey; not technical validation and predates wind-down.",
    ],
    [
        "C01",
        "Crossfield Fusion",
        "Mission",
        "Crossfield Fusion",
        "company primary",
        "accessed 2026-09-28",
        "https://crossfieldfusion.com/mission",
        "Historical device claim, internal negative scaling result and pivot to isotope separation.",
        "Device/fusion claim is self-reported; negative result is valuable but not independently reproduced.",
    ],
    [
        "C02",
        "Crossfield Fusion",
        "CROSSFIELD FUSION LTD overview",
        "UK Companies House",
        "government corporate registry",
        "statement 2026-08-21",
        "https://find-and-update.company-information.service.gov.uk/company/12220468",
        "Active legal status, incorporation and filing dates.",
        "Registry status does not establish current technical operations.",
    ],
    [
        "C03",
        "Crossfield Fusion",
        "UK fusion investment prospectus directory",
        "UK Department for Energy Security and Net Zero",
        "government promotional directory",
        "2026-09-14",
        "https://www.gov.uk/government/publications/uk-fusion-investment-prospectus/uk-fusion-investment-prospectus-directory-html",
        "Current UK fusion ecosystem context.",
        "Promotional directory; no independent Crossfield performance measurement.",
    ],
    [
        "S01",
        "Astral Systems",
        "Official site and publications",
        "Astral Systems",
        "company primary",
        "accessed 2026-09-28",
        "https://www.astralsystems.com/",
        "Current LCF neutron/isotope programme and publications.",
        "Company claims; no independent metrology.",
    ],
    [
        "S02",
        "Astral Systems",
        "Kyoto Fusioneering and Astral Systems join Culham fusion hub",
        "UK Atomic Energy Authority",
        "government independent",
        "2025-06-17",
        "https://www.gov.uk/government/news/kyoto-fusioneering-and-astral-systems-join-culham-fusion-hub",
        "Culham tenancy and SSETB activity.",
        "Does not validate reactor performance.",
    ],
    [
        "S03",
        "Astral Systems",
        "UK fusion investment prospectus directory",
        "UK Department for Energy Security and Net Zero",
        "government promotional directory",
        "2026-09-14",
        "https://www.gov.uk/government/publications/uk-fusion-investment-prospectus/uk-fusion-investment-prospectus-directory-html",
        "Government-published LCF, manufacturing, tritium and 60-hour D-T statements.",
        "Promotional text may rely on company-supplied data; no methods or metrology.",
    ],
    [
        "D01",
        "Deutelio",
        "Deutelio AG commercial-register profile",
        "Moneyhouse / SOGC-derived data",
        "commercial registry aggregator",
        "entry 2024-04-05; update 2025-10-08",
        "https://www.moneyhouse.ch/en/company/deutelio-ag-3402618371",
        "Active Swiss entity, UID, aliases, address move and corporate purpose.",
        "Aggregator of official notices; does not establish technical progress.",
    ],
    [
        "D02",
        "Deutelio",
        "The Polomac configuration as a fusion reactor",
        "Journal of Technological and Space Plasmas",
        "company-authored technical paper",
        "2024",
        "https://www.jtsp.eu/jtsp/article/download/32/28",
        "Documents the Polomac design concept.",
        "Company-authored concept paper; no device or experimental validation.",
    ],
    [
        "D03",
        "Deutelio",
        "The Global Fusion Industry in 2023",
        "Fusion Industry Association",
        "industry survey",
        "2023",
        "https://thefusioncluster.com/wp-content/uploads/2023/08/FIA%E2%80%932023-FINAL.pdf",
        "Participant-described D-D fuel and prototype ambition.",
        "Company-survey response; predates Swiss incorporation and is not validation.",
    ],
]


CLOSURE_FIELDS = [
    "organization",
    "source_record_id",
    "round4_gap_fields",
    "fields_closed",
    "remaining_explicit_limitations",
    "round5_disposition",
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
    """Derive bounded closures for the six reviewed overlays.

    Parameters
    ----------
    overlays : sequence of sequences of str
        Complete reviewed overlay rows in OVERLAY_FIELDS order.
    old : mapping of str to mappings
        Previous matrix indexed by exact organization identity.

    Returns
    -------
    list of list of str
        Closure rows in CLOSURE_FIELDS order, retaining negative findings.

    Raises
    ------
    ValueError
        If targets, row shape or previous identity/priority do not match.
    """
    if any(len(row) != len(OVERLAY_FIELDS) for row in overlays):
        raise ValueError("overlay row shape mismatch")
    target_names = [row[0] for row in overlays]
    if len(target_names) != 6 or len(set(target_names)) != 6:
        raise ValueError("expected six unique overlay targets")
    if any(name not in old for name in target_names):
        raise ValueError("previous matrix missing overlay target")
    if any(
        old[row[0]]["record_id"] != row[2] or old[row[0]]["priority_band"] != "high"
        for row in overlays
    ):
        raise ValueError("previous target identity or high priority mismatch")
    closures: list[list[str]] = []
    for row in overlays:
        name = row[0]
        enriched = set(row[3].split(";"))
        before = old[name]["gap_fields"].split(";")
        closed = [
            field
            for field in before
            if {
                "status": "normalized_status",
                "source_date": "source_dates",
                "milestone": "highest_independently_supported_milestone",
            }.get(field, field)
            in enriched
        ]
        disposition = (
            "closed with bounded evidence"
            if len(closed) == len(before)
            else "partially closed; explicit negative finding retained"
        )
        closures.append(
            [name, row[2], old[name]["gap_fields"], ";".join(closed), row[18], disposition, DATE]
        )
    return closures


def write(path: Path, fields: list[str], rows: list[list[str]]) -> None:
    """Serialize deterministic curated or derived rows without altering claims.

    Parameters
    ----------
    path : pathlib.Path
        Output TSV in the selected directory.
    fields : list of str
        Ordered producer schema.
    rows : list of lists of str
        Actual reviewed source or derived closure rows.
    """
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(fields)
        writer.writerows(rows)


def main() -> None:
    """Generate outputs only after validating the previous matrix and closures."""
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
        old = read_matrix(args.gap_matrix)
        closures = build_closures(OVERLAYS, old)
        args.output_directory.mkdir(parents=True, exist_ok=True)
        write(args.output_directory / "enrichment_overlays.tsv", OVERLAY_FIELDS, OVERLAYS)
        write(
            args.output_directory / "source_registry.tsv",
            SOURCE_FIELDS,
            [[*row, DATE] for row in SOURCES],
        )
        write(args.output_directory / "gap_closure.tsv", CLOSURE_FIELDS, closures)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"BUILD FAILED: {error}")
        raise SystemExit(1) from None
    print(f"wrote {len(OVERLAYS)} overlays, {len(SOURCES)} sources, {len(closures)} closure rows")


if __name__ == "__main__":
    main()
