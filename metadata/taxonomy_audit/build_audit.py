# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/taxonomy_audit/build_audit.py
"""Reproducible editorial audit of the snapshot, not a scientific peer review."""

from __future__ import annotations

import argparse
import collections
import csv
import json
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parent
FIELDS = (
    "id",
    "name",
    "domain",
    "family",
    "parent_id",
    "kind",
    "maturity",
    "evidence",
    "evidence_scope",
    "source_urls",
    "source_audit",
)


class SourceCheck(TypedDict):
    """URL identity, observed response status and access description for triage."""

    url: str
    status: int | str
    access: str
    title: str


class AuditSummary(TypedDict):
    """Historical snapshot counts; no scientific admission or current availability."""

    entries: int
    domains: dict[str, int]
    kinds: dict[str, int]
    original_unique_sources: int
    checked_sources_including_replacements: int
    source_access: dict[str, int]
    misassigned_source_entries: int
    classification_flags: dict[str, int]


FUSION = "https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1562_web.pdf"
HTR = "https://www.inet.tsinghua.edu.cn/ineten/info/1024/1698.htm"
FAST = "https://www.iaea.org/sites/default/files/gc/gc68-inf-4.pdf"
ELECTRO = "https://www.energy.gov/sites/default/files/2024-12/hydrogen-shot-water-electrolysis-technology-assessment.pdf"
ZICF = "https://www.sandia.gov/research/publications/details/dynamics-of-a-z-pinch-x-ray-source-for-heating-icf-relevant-hohlraums-to-12-2000-07-10/"
SPH = "https://str.llnl.gov/sites/str/files/2024-04/1999.12.pdf"
wrong = {
    "https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1854_web.pdf": (
        "Wrong work: Decommissioning of Particle Accelerators, not Fusion Physics.",
        FUSION,
    ),
    "https://doi.org/10.1063/1.873677": (
        "Wrong work: long-time tails and transport/self-organized criticality, not Z-pinch ICF.",
        ZICF,
    ),
    "https://doi.org/10.1088/0741-3335/36/7/001": (
        "Wrong work: particle pinch velocity in compact helical system CHS, not spheromak/FRC.",
        SPH,
    ),
}
special = {
    "pebble-bed-htgr": (
        "maturity-correction",
        "Commercial HTR-PM operation began December 2023; demonstrated-only understates deployment.",
        "Use deployed with commercial-demonstration qualification; do not infer broad fleet maturity.",
        HTR,
    ),
    "sodium-fast-reactor": (
        "maturity-correction",
        "IAEA reports operating sodium fast reactors; demonstrated-only understates power-reactor deployment.",
        "Use deployed for the architecture; distinguish historical prototypes and individual designs.",
        FAST,
    ),
    "magnox-gas-cooled-reactor": (
        "historical-maturity-facet",
        "Historical commercial deployment is collapsed into demonstrated.",
        "Separate highest demonstrated maturity from current fleet activity; retain historical commercial status.",
        "",
    ),
    "heavy-water-pressure-vessel-reactor": (
        "historical-maturity-facet",
        "Historical deployment needs named facility evidence; generic CANDU pressure-tube material is insufficient.",
        "Add Atucha/other pressure-vessel primary sources and explicit historical/deployed scope.",
        "",
    ),
    "prismatic-htgr": (
        "historical-maturity-facet",
        "Experimental and historical power demonstrations differ; present label obscures deployment history.",
        "Add named primary facility histories (e.g. Fort St Vrain) rather than infer current commercialization.",
        "",
    ),
    "integral-pwr": (
        "source-scope-review",
        "General reactor training/design taxonomy does not establish integral-PWR demonstration claims.",
        "Cite a named integral design and demonstrated milestone; separate integral architecture from SMR scale.",
        "",
    ),
    "very-high-temperature-reactor-vhtr": (
        "overlap-facet",
        "VHTR is explicitly a development class overlapping prismatic/pebble-bed HTGR.",
        "Keep as performance/development facet linked to HTGR, not an additive unique architecture.",
        "",
    ),
    "standing-wave-breed-and-burn-reactor": (
        "subtype-source-review",
        "TWR design article may discuss stationary burning wave; per-entry support not inspected.",
        "Verify exact stationary-wave passage and distinguish fuel-management scheme from separate architecture.",
        "",
    ),
    "optimised-modular-stellarator": (
        "overlap-facet",
        "Modular coils and optimization are intersecting stellarator design attributes.",
        "Clarify geometry subtype versus optimization facet; add W7-X primary source.",
        "",
    ),
    "segmented-flow-reactor": (
        "parent-correction",
        "Segmented flow also occurs in meso/millimetre channels; it is not necessarily a microchannel subtype.",
        "Model multiphase-flow regime as a cross-cutting configuration with optional microchannel relationship.",
        "",
    ),
    "plug-flow-tubular-reactor": (
        "model-geometry-conflation",
        "Ideal plug flow is a model; real tubular reactors may have axial dispersion.",
        "Separate ideal flow model from tubular geometry in metadata.",
        "",
    ),
    "homogeneous-photochemical-flow-reactor": (
        "source-scope-review",
        "Photocatalytic Reactor Design source does not by title establish homogeneous photochemistry.",
        "Add a primary homogeneous photochemical flow study; distinguish photocatalysis from direct photolysis.",
        "",
    ),
    "thermal-plasma-arc-reactor": (
        "source-scope-review",
        "Assigned plasma review explicitly addresses non-thermal plasma; thermal-arc deployment is a different scope.",
        "Add thermal-plasma process/facility source; qualify application-specific maturity.",
        "",
    ),
    "moving-fixed-bed-gasifier": (
        "source-scope-review",
        "NETL source is an entrained-flow gasification project, not a general taxonomy of fixed/moving-bed gasifiers.",
        "Add NETL fixed/moving-bed gasification guidance and separate solid motion if needed.",
        "",
    ),
    "fluidised-bed-gasifier": (
        "source-scope-review",
        "NETL source is an entrained-flow gasification project; support for fluidised-bed claims is indirect.",
        "Add NETL fluidised-bed-specific guidance.",
        "",
    ),
    "anion-exchange-membrane-electrolyser": (
        "maturity-review",
        "Research-only may obscure early product commercialization; no direct dated deployment source attached.",
        "Compare commercial availability, durability demonstration and deployment scale separately; retain research pending review.",
        ELECTRO,
    ),
    "solid-oxide-electrolyser": (
        "maturity-review",
        "Demonstrated label needs explicit scale/date; source link is broken and fuel-cell handbook is not electrolyser deployment evidence.",
        "Use updated DOE assessment and dated deployment source; do not infer electrolysis maturity from fuel cells.",
        ELECTRO,
    ),
    "laser-indirect-drive-icf": (
        "evidence-scope-review",
        "Demonstration must specify target ignition/target gain, not wall-plug or net-electric output.",
        "Add LLNL ignition primary results with metric and shot date; retain separate plant maturity.",
        "",
    ),
    "dense-plasma-focus": (
        "source-bias-review",
        "Primary assigned article is developer-authored Focus Fusion progress; it cannot independently validate commercial p-B11 claims.",
        "Retain established plasma-focus physics but independently source advanced-fuel and power-performance claims.",
        "",
    ),
    "polywell": (
        "evidence-scope-review",
        "Electron confinement in a magnetic cusp is not demonstration of an integrated net-energy Polywell reactor.",
        "Keep research; describe exactly the subsystem experimentally supported.",
        "https://doi.org/10.1103/PhysRevX.5.021024",
    ),
    "maglif": (
        "source-directness-review",
        "MagLIF-specific paper is relevant; inherited unrelated Z-ICF DOI should be removed.",
        "Retain correct MagLIF publication and specify experimental rather than plant evidence.",
        "https://doi.org/10.1063/5.0206222",
    ),
    "muon-catalysed-fusion": (
        "domain-facet",
        "Low-temperature fusion mechanism is placed in hybrid domain for presentation, not because it necessarily couples two reactor types.",
        "Add primary nuclear-process domain plus secondary mechanism/integration facets.",
        "https://doi.org/10.1016/0375-9474(92)90412-D",
    ),
    "pyroelectric-fusion-source": (
        "domain-facet",
        "Externally accelerated beam-target neutron source is fusion, not inherently a hybrid reactor.",
        "Cross-list under beam-target fusion and retain no-net-energy scope.",
        "https://www.nature.com/articles/nature03575",
    ),
    "solid-core-nuclear-thermal-rocket": (
        "domain-correction",
        "Fission rocket is an application of a fission reactor; propulsion alone is not hybrid physics.",
        "Primary domain fission, application propulsion; retain ground-test versus flight distinction.",
        "https://ntrs.nasa.gov/citations/19920005899",
    ),
    "fission-fragment-propulsion-reactor": (
        "domain-correction",
        "Direct fragment propulsion is fission-based, not necessarily hybrid.",
        "Primary domain fission with speculative propulsion application.",
        "https://ntrs.nasa.gov/citations/20150002578",
    ),
    "direct-fusion-drive": (
        "domain-correction",
        "FRC fusion propulsion concept is not inherently a fusion-fission or multi-reactor hybrid.",
        "Primary domain fusion, application propulsion; retain concept maturity.",
        "https://doi.org/10.1016/j.actaastro.2014.08.008",
    ),
    "photovoltaic-photothermal-artificial-photosynthesis": (
        "single-study-system",
        "Label describes one integration study rather than a broadly standardized reactor family.",
        "Keep as named system concept with study-specific evidence; avoid counting it as a general architecture.",
        "https://arxiv.org/abs/2204.04971",
    ),
    "cavitation-bubble-fusion": (
        "classification-supported-claim-contested",
        "Assigned replication paper is critical evidence, not demonstration of fusion.",
        "Keep contested; include original claim and independent null studies, never infer a functioning reactor.",
        "https://doi.org/10.1103/PhysRevLett.89.104302",
    ),
}


def _validate_rows(rows: list[dict[str, str]]) -> None:
    if not rows or any(tuple(row) != FIELDS for row in rows):
        raise ValueError("taxonomy schema mismatch or empty snapshot")
    identifiers: set[str] = set()
    for row in rows:
        identifier = row["id"]
        if not identifier or identifier != identifier.strip() or identifier in identifiers:
            raise ValueError("invalid or duplicate taxonomy identity")
        identifiers.add(identifier)
        if any(not row[key].strip() for key in ("name", "domain", "family", "kind", "source_urls")):
            raise ValueError("blank taxonomy audit context")
        if any(not url.strip() for url in row["source_urls"].split(" | ")):
            raise ValueError("blank taxonomy source URL")


def read_snapshot(path: Path) -> list[dict[str, str]]:
    """Read an intact historical taxonomy table without changing its claims.

    Parameters
    ----------
    path : pathlib.Path
        UTF-8 TSV with the original eleven columns in their recorded order.

    Returns
    -------
    list of dict
        Snapshot rows, preserving order and editorial source text.

    Raises
    ------
    ValueError
        Header, row shape, identity or required context is invalid.
    """
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t", strict=True)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError("taxonomy header mismatch")
        rows: list[dict[str, str]] = []
        for raw in reader:
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError("taxonomy row shape mismatch")
            rows.append({key: str(raw[key]) for key in FIELDS})
    _validate_rows(rows)
    return rows


def read_checks(path: Path) -> list[SourceCheck]:
    """Read the checker schema 1.0.0 envelope or the historical bare array.

    Parameters
    ----------
    path : pathlib.Path
        Saved JSON observations. This function makes no network requests.

    Returns
    -------
    list of SourceCheck
        Unique URL observations needed by the editorial rules.

    Raises
    ------
    ValueError
        Envelope, record count or consumed observation fields are invalid.
    """
    document: object = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(document, dict):
        if (
            set(document) != {"schema_version", "record_count", "records"}
            or document["schema_version"] != "1.0.0"
        ):
            raise ValueError("unsupported URL check envelope")
        records: object = document["records"]
        count: object = document["record_count"]
        if type(count) is not int or not isinstance(records, list) or count != len(records):
            raise ValueError("URL check record count mismatch")
    else:
        records = document
    if not isinstance(records, list) or not records:
        raise ValueError("URL checks must be a nonempty array")
    checks: list[SourceCheck] = []
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("URL check must be an object")
        url: object = record.get("url")
        access: object = record.get("access")
        status: object = record.get("status")
        title: object = record.get("title", "")
        if not isinstance(url, str) or not url.strip() or url != url.strip() or url in seen:
            raise ValueError("invalid or duplicate checked URL")
        if not isinstance(access, str) or not access.strip() or not isinstance(title, str):
            raise ValueError("invalid URL check access or title")
        if isinstance(status, bool) or not isinstance(status, (str, int)):
            raise ValueError("invalid URL check status")
        if isinstance(status, int):
            if not 100 <= status <= 599:
                raise ValueError("invalid URL check status")
        elif status != "":
            raise ValueError("invalid URL check status")
        checks.append(SourceCheck(url=url, status=status, access=access, title=title))
        seen.add(url)
    return checks


def build_audit(
    rows: list[dict[str, str]], checks: list[SourceCheck]
) -> tuple[list[dict[str, str]], AuditSummary]:
    """Apply the preserved 2026-09-26 editorial rules to a complete snapshot.

    Parameters
    ----------
    rows : list of dict
        Original-schema taxonomy rows, normally supplied by read_snapshot.
    checks : list of SourceCheck
        Saved URL observations, normally supplied by read_checks.

    Returns
    -------
    tuple
        Entry triage and historical counts. The fixed audit date records the
        rule set, not a fresh scientific review or network availability check.

    Raises
    ------
    ValueError
        Snapshot is invalid, observations repeat or any source lacks a check.
    """
    _validate_rows(rows)
    byurl = {check["url"]: check for check in checks}
    if len(byurl) != len(checks):
        raise ValueError("duplicate checked URL")
    if any(url not in byurl for row in rows for url in row["source_urls"].split(" | ")):
        raise ValueError("taxonomy source has no URL check")
    audit: list[dict[str, str]] = []
    for row in rows:
        urls = row["source_urls"].split(" | ")
        issues = []
        actions = []
        verified = []
        classification = "plausible-provisional"
        directness = "introductory-family-mapping; per-claim verification pending"
        if row["kind"] not in ["architecture", "subtype"]:
            classification = "cross-cutting-facet"
            issues.append("Entry kind is " + row["kind"] + "; count overlaps architectures.")
            actions.append(
                "Retain explicit kind; do not sum as mutually exclusive reactor designs."
            )
        if len(urls) > 1:
            issues.append(
                "Sources inherited from family group; applicability of each URL to this entry is not individually established."
            )
            actions.append("Assign references per entry and per claim with page/section pointers.")
        for url in urls:
            if url in wrong:
                msg, replacement = wrong[url]
                issues.append(msg)
                actions.append(
                    "Remove misassigned reference and verify replacement at claim level."
                )
                verified.append(
                    replacement
                    if (
                        replacement not in [SPH, ZICF]
                        or row["id"] in ["spheromak", "z-pinch-driven-indirect-icf"]
                    )
                    else FUSION
                )
                directness = "contains-confirmed-misassigned-work"
            c = byurl[url]
            if c["status"] == 404:
                issues.append("Broken source URL (HTTP 404): " + url)
                actions.append("Replace moved URL with a current authoritative page.")
                if "water-electrolysis" in url:
                    verified.append(ELECTRO)
            if "Captcha" in c.get("title", "") or "Just a moment" in c.get("title", ""):
                issues.append("Access challenge is not substantive article content: " + url)
        if row["id"] in special:
            classification, msg, action, url = special[row["id"]]
            issues.append(msg)
            actions.append(action)
            if url:
                verified.append(url)
        if row["domain"] == "fusion":
            actions.append(
                "Separate demonstrated plasma configuration / fusion output / target gain / net electricity; attach metric and dated source."
            )
        if row["family"] == "Contested nuclear claims":
            issues.append(
                "Claim class, not an established reactor architecture; assigned null/critical sources cannot validate claimed energy production."
            )
            actions.append(
                "Keep contested label; pair exact claim with independent replication outcomes."
            )
            classification = "claim-class-not-established-reactor"
        if row["family"] == "Biochemical culture systems":
            issues.append(
                "Fermentation scale-up review is relevant background but not direct evidence for all fed-batch, chemostat and perfusion subtype claims."
            )
            actions.append("Add mode-specific textbooks or primary perfusion/chemostat references.")
        access = " | ".join(sorted({byurl[u]["access"] for u in urls}))
        audit.append(
            dict(
                id=row["id"],
                name=row["name"],
                classification_ok=classification,
                source_directness=directness,
                source_access=access,
                issue=" ".join(issues)
                or "No specific error found in this introductory audit; scientific claims remain unverified.",
                recommended_action=" ".join(dict.fromkeys(actions))
                or "Verify exact supporting passage and dated maturity evidence.",
                verified_source_url=" | ".join(dict.fromkeys(verified)),
                audit_date="2026-09-26",
            )
        )
    summary = AuditSummary(
        entries=len(rows),
        domains=dict(collections.Counter(r["domain"] for r in rows)),
        kinds=dict(collections.Counter(r["kind"] for r in rows)),
        original_unique_sources=len({u for row in rows for u in row["source_urls"].split(" | ")}),
        checked_sources_including_replacements=len(checks),
        source_access=dict(collections.Counter(r["access"] for r in checks)),
        misassigned_source_entries=sum(
            r["source_directness"] == "contains-confirmed-misassigned-work" for r in audit
        ),
        classification_flags=dict(collections.Counter(r["classification_ok"] for r in audit)),
    )
    return audit, summary


def main(argv: list[str] | None = None) -> int:
    """Write a historical reproduction into an explicitly separate directory.

    Parameters
    ----------
    argv : list of str, optional
        Command-line arguments; omitted arguments use the process command line.

    Returns
    -------
    int
        Zero on success, one on input or output failure. Argument errors use
        argparse's exit status two. The maintained merged audit is protected.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "input-taxonomy-snapshot.tsv")
    parser.add_argument("--checks", type=Path, default=ROOT / "url_checks.json")
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        output = args.output_directory.resolve()
        if output == ROOT:
            raise ValueError("historical output cannot replace the maintained merged audit")
        outputs = [output / "audit.tsv", output / "summary.json"]
        if any(path.resolve() in {ROOT / "audit.tsv", ROOT / "summary.json"} for path in outputs):
            raise ValueError("historical output cannot replace the maintained merged audit")
        if any(path.resolve() in {args.input.resolve(), args.checks.resolve()} for path in outputs):
            raise ValueError("output cannot replace audit inputs")
        audit, summary = build_audit(read_snapshot(args.input), read_checks(args.checks))
        output.mkdir(parents=True, exist_ok=True)
        with outputs[0].open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(audit[0]), delimiter="\t")
            writer.writeheader()
            writer.writerows(audit)
        outputs[1].write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    except (OSError, UnicodeError, ValueError, csv.Error) as exc:
        print(f"BUILD FAILED: {exc}")
        return 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
