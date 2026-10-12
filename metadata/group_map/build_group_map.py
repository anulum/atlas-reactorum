#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/group_map/build_group_map.py
"""Build the SCPN Reactor Systems group map from its dated source snapshot.

The accepted source snapshot records, for every repository of the group, values
read from that repository's own files, from the public Python index and from
the public repository listing. This builder derives the project data file, the
public page with its diagram from that snapshot and from the retained
portfolio citations. It reads nothing else and reaches no network.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = Path(__file__).with_name("source_snapshot.json")
CITATIONS = ROOT / "metadata/reactor_portfolio/links.v1.json"
GROUP = "SCPN-REACTOR-SYSTEMS"
ATLAS = "ATLAS-REACTORUM"
REGISTRY_OWNER = ("SCPN-PHASE-ORCHESTRATOR", "SCPN-SYSTEMS-INTEGRATION-AND-CONTROL")
OUTPUTS = {
    "data": Path("metadata/group_map/ecosystem_projects.json"),
    "page": Path("docs/ecosystem.md"),
}
FAMILIES = {
    "solver_library": "Solver libraries",
    "shared_kernel_library": "Shared kernel library",
    "fusion_device": "Fusion device cores",
    "fission_device": "Fission device scaffolds",
    "chemical_device": "Chemical and biochemical device scaffolds",
    "hybrid_composition": "Hybrid composition scaffolds",
    "catalogue": "Catalogue scaffold",
    "evidence_library": "Evidence library",
}
MANIFEST_FAMILY = {
    "reactor-domain.json": "fusion_device",
    "kernels-domain.json": "shared_kernel_library",
}
CITED_CATEGORY = {
    "fusion_device": "device",
    "shared_kernel_library": "shared_kernel_library",
    "solver_library": "solver_library",
}
KIND = {"solver_library": "package", "shared_kernel_library": "package", "evidence_library": "tool"}
MATURITIES = {"architecture_only", "computational_prototype"}
CLASSIFIERS = {
    "Development Status :: 2 - Pre-Alpha": "pre-alpha",
    "Development Status :: 3 - Alpha": "alpha",
    "Development Status :: 4 - Beta": "beta",
    "Development Status :: 5 - Production/Stable": "stable",
}
STATUS_ORDER = ("released", "under development", "architecture stage")
GROUP_TITLES = {
    "SC-NEUROMORPHIC-COMPUTING-SYSTEMS": "SC Neuromorphic Computing Systems",
    "SCPN-QUANTUM-COMPUTING-SYSTEMS": "SCPN Quantum Computing Systems",
    "SCPN-SYSTEMS-INTEGRATION-AND-CONTROL": "SCPN Systems Integration and Control",
}
HEADER = """<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
ATLAS REACTORUM — SCPN Reactor Systems group and project map
-->
"""


def load_snapshot(path: Path) -> dict[str, Any]:
    """Read and admit the dated source snapshot of the group.

    Parameters
    ----------
    path : pathlib.Path
        Source snapshot envelope.

    Returns
    -------
    dict
        The unchanged envelope.

    Raises
    ------
    ValueError
        If the schema, group, capture date, count or project identities are not
        the ones this builder owns.
    """
    snapshot: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("schema") != "scpn.reactor-group-source-snapshot.v1":
        raise ValueError("source snapshot schema is not recognised")
    if snapshot.get("group") != GROUP:
        raise ValueError("source snapshot belongs to another group")
    try:
        dt.date.fromisoformat(str(snapshot.get("captured")))
    except ValueError as error:
        raise ValueError("source snapshot capture date is not a full ISO date") from error
    records = snapshot.get("records")
    if not isinstance(records, list) or snapshot.get("count") != len(records):
        raise ValueError("source snapshot count differs from its records")
    names = [record["project"] for record in records]
    if names != sorted(set(names)):
        raise ValueError("source snapshot projects are duplicated or unordered")
    return snapshot


def load_citations(path: Path) -> dict[str, str]:
    """Read the category of every project in the retained portfolio citations.

    Parameters
    ----------
    path : pathlib.Path
        Portfolio citation snapshot of this repository.

    Returns
    -------
    dict of str to str
        Cited category by project identifier.

    Raises
    ------
    ValueError
        If the citation snapshot does not belong to the group.
    """
    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if document.get("owner_group") != GROUP:
        raise ValueError("portfolio citations belong to another group")
    return {record["project_id"]: record["category"] for record in document["records"]}


def family_of(record: dict[str, Any], cited: dict[str, str]) -> str:
    """Return the family a repository declares, checked against its citation.

    Parameters
    ----------
    record : dict
        One source snapshot record.
    cited : dict of str to str
        Cited category by project identifier.

    Returns
    -------
    str
        A key of ``FAMILIES``.

    Raises
    ------
    ValueError
        If the repository declares no family this builder knows, or its
        declaration disagrees with the retained citation.
    """
    name = record["project"]
    manifest = record["manifest"]
    if name == ATLAS and manifest is None and name not in cited:
        return "evidence_library"
    if name not in cited:
        raise ValueError(f"{name} has no retained portfolio citation")
    if manifest is None:
        family = cited[name]
    else:
        family = MANIFEST_FAMILY.get(manifest["file"]) or manifest["category"]
    if family not in FAMILIES or family == "evidence_library":
        raise ValueError(f"{name} declares no known family")
    if CITED_CATEGORY.get(family, family) != cited[name]:
        raise ValueError(f"{name} family differs from its retained citation")
    return family


def _licence(record: dict[str, Any]) -> tuple[str, str]:
    licence = record["licence"]
    declared = {value for value in (licence["packaging"], licence["readme_spdx"]) if value}
    if len(declared) != 1:
        raise ValueError(f"{record['project']} states no single licence")
    source = "pyproject.toml [project].license" if licence["packaging"] else "README.md SPDX line"
    return declared.pop(), source


def _function(record: dict[str, Any], plans: dict[str, str]) -> tuple[str, str]:
    manifest = record["manifest"] or {}
    if manifest.get("device_family"):
        family = manifest["device_family"].replace("_", " ")
        return (
            f"Device-level description of the {family} family",
            f"{manifest['file']} device_family",
        )
    if manifest.get("boundary"):
        named = re.sub(
            r"\b[A-Z]\d+\b", lambda code: plans.get(code[0], code[0]), manifest["boundary"]
        )
        return named, f"{manifest['file']} boundary"
    if record["description"]:
        return record["description"], "pyproject.toml [project].description"
    raise ValueError(f"{record['project']} states no function")


def _device(manifest: dict[str, Any]) -> dict[str, Any] | None:
    if not manifest.get("device_family"):
        return None
    return {
        "device_family": manifest["device_family"],
        "confinement_family": manifest["confinement_family"],
        "configurations": manifest["configurations"],
        "implemented_capabilities": manifest["capabilities"],
    }


def _status(record: dict[str, Any], maturity: str | None) -> tuple[str, str]:
    index = record["index"]
    if index and record["release_tags"]:
        return "released", f"index entry {index['name']} {index['version']} with release tags"
    if maturity == "architecture_only":
        return "architecture stage", f"{record['manifest']['file']} evidence_maturity"
    if record["hosting"]["visibility"] == "public":
        return "under development", "public repository without a package release"
    raise ValueError(f"{record['project']} matches no status rule")


def _links(record: dict[str, Any]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    name = record["project"]
    for requirement in record["requirements"]:
        extra = requirement["extra"]
        kind = "optional interface" if extra else "package dependency"
        where = f"{name}/pyproject.toml line {requirement['line']}"
        links.append(
            {
                "to": requirement["to"],
                "to_group": requirement["to_group"],
                "kind": kind,
                "evidence": f"{where} (extra {extra})" if extra else where,
            }
        )
    pin = (record["manifest"] or {}).get("registry_pin")
    if pin:
        digest = pin["digest_sha256"][:12]
        links.append(
            {
                "to": REGISTRY_OWNER[0],
                "to_group": REGISTRY_OWNER[1],
                "kind": "pinned contract",
                "evidence": f"{name}/{record['manifest']['file']} spo_registry version "
                f"{pin['version']} digest {digest}",
            }
        )
    return links


def build_data(
    snapshot: dict[str, Any], cited: dict[str, str], source_sha256: str
) -> dict[str, Any]:
    """Derive the project data file from an admitted source snapshot.

    Parameters
    ----------
    snapshot : dict
        Admitted source snapshot envelope.
    cited : dict of str to str
        Cited category by project identifier.
    source_sha256 : str
        SHA-256 of the exact snapshot bytes the data are derived from.

    Returns
    -------
    dict
        Project data in the ``ecosystem-projects/1.0`` shape, with the group's
        declared evidence maturity and field sources beside it.

    Raises
    ------
    ValueError
        If a record lacks a licence, a function, a known family, a known
        evidence maturity or a status rule, or if the snapshot and the
        retained citations name different projects.
    """
    projects = []
    plans = {
        record["manifest"]["plan_id"]: record["project"]
        for record in snapshot["records"]
        if (record["manifest"] or {}).get("plan_id")
    }
    for record in snapshot["records"]:
        family = family_of(record, cited)
        manifest = record["manifest"] or {}
        maturity = manifest.get("evidence_maturity")
        if maturity is not None and maturity not in MATURITIES:
            raise ValueError(f"{record['project']} declares an unknown evidence maturity")
        function, function_source = _function(record, plans)
        licence, licence_source = _licence(record)
        visibility = record["hosting"]["visibility"]
        if visibility not in {"public", None}:
            raise ValueError(f"{record['project']} is neither public nor unpublished")
        status, status_where = _status(record, maturity)
        index = record["index"]
        classifier = CLASSIFIERS.get(record["classifier"])
        projects.append(
            {
                "name": record["project"],
                "family": family,
                "kind": KIND.get(family, "component"),
                "function": function,
                "function_source": function_source,
                "owning_groups": [GROUP],
                "primary_group": GROUP,
                "status": status,
                "status_source": {"where": status_where, "date": snapshot["captured"]},
                "version": {
                    "value": index["version"] if index else None,
                    "source": f"index entry {index['name']}" if index else None,
                },
                "maturity": {
                    "value": classifier,
                    "source": "pyproject.toml classifier" if classifier else None,
                },
                "declared_evidence_maturity": {"value": maturity, "source": manifest.get("file")},
                "device": _device(manifest),
                "repository": {
                    "hosted_in": record["project"],
                    "visibility": visibility or "not published",
                    "url": f"https://github.com/{record['hosting']['slug']}"
                    if visibility
                    else None,
                },
                "packages": [{"index": f"PyPI {index['name']}", "published": True}]
                if index
                else [],
                "licence": licence,
                "licence_source": licence_source,
                "commercial_licence_available": record["licence"]["commercial_line"] is not None,
                "links": _links(record),
            }
        )
    if {project["name"] for project in projects} != set(cited) | {ATLAS}:
        raise ValueError("source snapshot and portfolio citations name different projects")
    return {
        "format": "ecosystem-projects/1.0",
        "group": GROUP,
        "as_of": snapshot["captured"],
        "source_snapshot": {"file": "source_snapshot.json", "sha256": source_sha256},
        "projects": projects,
    }


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def _name(project: dict[str, Any]) -> str:
    url = project["repository"]["url"]
    return f"[{project['name']}]({url})" if url else project["name"]


def _is_local_scaffold(project: dict[str, Any]) -> bool:
    return (
        project["repository"]["visibility"] == "not published"
        and project["status"] == "architecture stage"
        and project["declared_evidence_maturity"]["value"] == "architecture_only"
        and not project["packages"]
    )


def _device_row(project: dict[str, Any]) -> str:
    device = project["device"]
    cells = [
        _name(project),
        device["confinement_family"].replace("_", " "),
        ", ".join(f"`{item}`" for item in device["configurations"]),
        str(device["implemented_capabilities"]),
        project["status"],
        f"`{project['declared_evidence_maturity']['value']}`",
    ]
    return "| " + " | ".join(cells) + " |"


def _project_row(project: dict[str, Any]) -> str:
    repository = project["repository"]
    name = _name(project)
    package = "none"
    if project["packages"]:
        package = f"{project['packages'][0]['index']} {project['version']['value']}"
        if project["maturity"]["value"]:
            package += f" ({project['maturity']['value']})"
    declared = project["declared_evidence_maturity"]["value"]
    cells = [
        name,
        _cell(project["function"]),
        project["status"],
        f"`{declared}`" if declared else "not declared",
        repository["visibility"],
        package,
    ]
    return "| " + " | ".join(cells) + " |"


def _cross_group(data: dict[str, Any]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for project in data["projects"]:
        for link in project["links"]:
            if link["to_group"] != GROUP:
                key = (link["to_group"], link["to"], link["kind"])
                grouped.setdefault(key, []).append({"project": project, "link": link})
    return dict(sorted(grouped.items()))


def _diagram(data: dict[str, Any]) -> list[str]:
    projects = data["projects"]
    lines = [
        "```mermaid",
        "flowchart LR",
        '  subgraph reactor["SCPN Reactor Systems"]',
        "    direction TB",
    ]
    for family, title in FAMILIES.items():
        members = [p for p in projects if p["family"] == family]
        states = ", ".join(
            f"{sum(1 for p in members if p['status'] == status)} {status}"
            for status in STATUS_ORDER
            if any(p["status"] == status for p in members)
        )
        lines.append(f'    {family}["{title}<br/>{states}"]')
    lines.append("  end")
    cross = _cross_group(data)
    for group in sorted({key[0] for key in cross}):
        lines += [f'  subgraph {_node(group)}["{GROUP_TITLES[group]}"]', "    direction TB"]
        lines += [
            f'    {_node(target)}["{target}"]'
            for target in sorted({k[1] for k in cross if k[0] == group})
        ]
        lines.append("  end")
    users = sum(1 for p in projects if _installs_kernels(p))
    lines.append(
        f'  fusion_device -->|"{users} install it at a pinned commit"| shared_kernel_library'
    )
    edges = sorted(
        {
            (entry["project"]["family"], target, kind)
            for (_group, target, kind), entries in cross.items()
            for entry in entries
        }
    )
    lines += [f'  {family} -.->|"{kind}"| {_node(target)}' for family, target, kind in edges]
    lines.append("```")
    return lines


def _node(name: str) -> str:
    return name.lower().replace("-", "_")


def _installs_kernels(project: dict[str, Any]) -> bool:
    return any(
        link["to"] == "SCPN-REACTOR-KERNELS" and link["kind"] == "package dependency"
        for link in project["links"]
    )


def render_page(data: dict[str, Any]) -> str:
    """Render the public group and project map from the project data.

    Parameters
    ----------
    data : dict
        Project data returned by :func:`build_data`.

    Returns
    -------
    str
        Complete Markdown page.
    """
    projects = data["projects"]
    as_of = data["as_of"]
    counts = {status: sum(1 for p in projects if p["status"] == status) for status in STATUS_ORDER}
    kernel_users = sum(1 for p in projects if _installs_kernels(p))
    pinned = sum(
        1 for p in projects if any(link["kind"] == "pinned contract" for link in p["links"])
    )
    licences = sorted({p["licence"] for p in projects})
    commercial = all(p["commercial_licence_available"] for p in projects)
    lines = [
        HEADER,
        "# SCPN Reactor Systems — group and project map",
        "",
        "This page is generated by `metadata/group_map/build_group_map.py` from the dated source",
        f"snapshot of {as_of} and is not edited by hand. The same data are in",
        "[`ecosystem_projects.json`](../metadata/group_map/ecosystem_projects.json); how they are",
        "collected and what they do not establish is in the",
        "[group map contract](../metadata/group_map/README.md).",
        "",
        "## What the group does",
        "",
        "The SCPN Reactor Systems Research Group models reactor systems. It keeps solver libraries, one",
        "shared kernel library, one repository per device family and this atlas of reactor technology.",
        "It has no single workbench: each repository owns one responsibility. A place in the tables",
        "states a responsibility, not that a project is complete, validated or certified.",
        "",
        *_diagram(data),
        "",
        "Lines in the diagram are for navigation. The solid line is a package dependency inside the",
        "group. Dashed lines are optional interfaces or data-only pins that can be checked in the",
        "cited files; none is a hard dependency between groups.",
        "",
        "## Where a newcomer starts",
        "",
        "- To run something: SCPN-FUSION-CORE, the tokamak solver and control library. Its own README",
        "  states which of its validation lanes are accepted and which are blocked or failing.",
        "- To read about reactor technology with sources: this atlas, a static site with no installation.",
        "- To see how one device family is described: any fusion device core below.",
        "",
        "## Words used",
        "",
        "- **Status** uses the common scale of the ecosystem. *Released*: a package on the public index",
        "  and a release tag. *Under development*: a public repository without a package release.",
        "  *Architecture stage*: the repository declares `architecture_only`.",
        "- **Declared evidence maturity** is the repository's own statement in its manifest, per",
        "  capability. Neither this atlas nor the group validates it.",
        "- **Not published** means a local repository without a public remote.",
        "",
        f"## Projects on {as_of}",
        "",
        "Counts are computed from the data and are the state on that date, never a total or a target: "
        + ", ".join(f"{counts[status]} {status}" for status in STATUS_ORDER if counts[status])
        + ".",
        "",
    ]
    for family, title in FAMILIES.items():
        members = [p for p in projects if p["family"] == family]
        lines += [f"### {title}", ""]
        if family == "fusion_device":
            members.sort(key=lambda p: (p["device"]["confinement_family"], p["name"]))
            lines += [
                "Every fusion device core is a public repository without a package release. The",
                "capability count is the number of capabilities its manifest lists as implemented.",
                "",
                "| Project | Confinement | Configurations | Capabilities | Status | Declared evidence maturity |",
                "|---|---|---|---|---|---|",
                *(_device_row(project) for project in members),
                "",
            ]
            continue
        if all(_is_local_scaffold(project) for project in members):
            lines += [
                "Local and not published. Architecture stage; declared evidence maturity",
                "`architecture_only`; no package.",
                "",
                "| Project | Scope |",
                "|---|---|",
                *(f"| {project['name']} | {_cell(project['function'])} |" for project in members),
                "",
            ]
            continue
        lines += [
            "| Project | Function | Status | Declared evidence maturity | Repository | Package |",
            "|---|---|---|---|---|---|",
            *(_project_row(project) for project in members),
            "",
        ]
    lines += [
        "## How the parts relate",
        "",
        f"- {kernel_users} fusion device cores install the shared kernel library at a pinned commit.",
        f"- {pinned} fusion device cores pin, as data, a version and digest of the reactor registry kept",
        "  in SCPN-PHASE-ORCHESTRATOR.",
        "- The scaffolds hold a reviewed boundary and validation tooling, and no model.",
        "- This atlas cites every other project of the group with source digests in the",
        "  [portfolio citations](../metadata/reactor_portfolio/README.md); it validates none of them.",
        "",
        "## Links to other groups that can be checked",
        "",
        "| From | To | Group of the target | Kind | Where |",
        "|---|---|---|---|---|",
    ]
    for (group, target, kind), entries in _cross_group(data).items():
        if all(entry["project"]["family"] == "fusion_device" for entry in entries):
            source = f"{len(entries)} fusion device cores"
            where = "the manifest of each, as listed per project in the data file"
            lines.append(f"| {source} | {target} | {GROUP_TITLES[group]} | {kind} | {where} |")
            continue
        for entry in entries:
            source, where = entry["project"]["name"], entry["link"]["evidence"]
            lines.append(f"| {source} | {target} | {GROUP_TITLES[group]} | {kind} | {where} |")
    lines += [
        "",
        "## Licensing",
        "",
        f"Every project states {' or '.join(licences)}"
        + ("; a commercial licence is available for each." if commercial else "."),
        "",
    ]
    return "\n".join(lines)


def render(snapshot_path: Path, citations_path: Path) -> dict[str, str]:
    """Render every output of the group map from the given sources.

    Parameters
    ----------
    snapshot_path : pathlib.Path
        Dated source snapshot of the group.
    citations_path : pathlib.Path
        Retained portfolio citations of this repository.

    Returns
    -------
    dict of str to str
        Output text by output name: ``data`` and ``page``.

    Raises
    ------
    ValueError
        If either source is refused.
    """
    raw = snapshot_path.read_bytes()
    snapshot = load_snapshot(snapshot_path)
    data = build_data(snapshot, load_citations(citations_path), hashlib.sha256(raw).hexdigest())
    return {
        "data": json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        "page": render_page(data),
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Check the accepted outputs or write a separate candidate bundle.

    Parameters
    ----------
    argv : sequence of str, optional
        Command-line arguments; the process arguments when omitted.

    Returns
    -------
    int
        Zero when the accepted outputs equal the rendered bytes or the bundle
        was written, one when a source is refused, an accepted output differs
        or the destination lies inside the repository.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SNAPSHOT)
    parser.add_argument("--citations", type=Path, default=CITATIONS)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--output-dir", type=Path)
    arguments = parser.parse_args(argv)
    try:
        rendered = render(arguments.source, arguments.citations)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 1
    if arguments.check:
        differing = [
            str(path)
            for name, path in OUTPUTS.items()
            if not (ROOT / path).is_file()
            or (ROOT / path).read_text(encoding="utf-8") != rendered[name]
        ]
        if differing:
            print("REFUSED: accepted outputs differ: " + ", ".join(differing), file=sys.stderr)
            return 1
        print(f"CHECK PASSED\tprojects\t{len(json.loads(rendered['data'])['projects'])}")
        return 0
    destination = arguments.output_dir.resolve()
    if not destination.is_dir() or destination == ROOT or ROOT in destination.parents:
        print(
            "REFUSED: output directory must exist outside the accepted repository", file=sys.stderr
        )
        return 1
    for name, path in OUTPUTS.items():
        (destination / path.name).write_text(rendered[name], encoding="utf-8")
    print(f"Wrote {len(OUTPUTS)} files to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
