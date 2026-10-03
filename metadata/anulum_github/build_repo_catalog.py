#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — metadata/anulum_github/build_repo_catalog.py
"""Build the public ANULUM reactor-repository catalog from GitHub's API."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import re
import ssl
import tempfile
import urllib.parse
import urllib.request
from datetime import date, datetime
from http.client import HTTPMessage
from pathlib import Path
from typing import IO, Any

HERE = Path(__file__).resolve().parent
LIBRARY = HERE.parents[1]
PRESENTATION_DATA = LIBRARY / "04_interactive_presentation/data"
API = "https://api.github.com/users/anulum/repos?per_page=100&sort=updated"

DEVICE_FAMILIES = {
    "scpn-beam-target-core",
    "scpn-theta-pinch-core",
    "scpn-z-pinch-core",
    "scpn-stellarator-core",
    "scpn-spheromak-core",
    "scpn-rfp-core",
    "scpn-muon-fusion-core",
    "scpn-mirror-core",
    "scpn-magnetic-cusp-core",
    "scpn-levitated-dipole-core",
    "scpn-lattice-fusion-core",
    "scpn-iec-core",
    "scpn-tokamak-core",
    "scpn-mif-plasma-jet-core",
    "scpn-mif-maglif-core",
    "scpn-mif-liner-core",
    "scpn-icf-laser-core",
    "scpn-icf-impact-core",
    "scpn-icf-beam-core",
    "scpn-fusion-fission-hybrid-core",
    "scpn-frc-core",
    "scpn-dense-plasma-focus-core",
}
FOUNDATIONS = {"scpn-fusion-core", "scpn-reactor-kernels"}
INTEGRATION = {"scpn-mif-core", "scpn-control", "scpn-phase-orchestrator", "scpn-quantum-control"}
SUPPORT = {"sc-neurocore", "LOOP-TIMING-WITNESS"}
RELEVANT = DEVICE_FAMILIES | FOUNDATIONS | INTEGRATION | SUPPORT

BOUNDARIES = {
    "device-family architecture": "Repository identity and code establish an implementation boundary, not independent reactor-performance validation.",
    "shared physics / kernels": "Software capability and repository tests are not evidence of physical-device or power-plant performance.",
    "control / integration": "Control, simulation and formal-contract evidence must not be promoted to hardware or reactor validation without the repository's stated gate.",
    "supporting hardware / compute": "Supporting compute or timing evidence is not a reactor result.",
}


def category(name: str) -> str:
    """Classify a repository by the subject it covers."""
    if name in DEVICE_FAMILIES:
        return "device-family architecture"
    if name in FOUNDATIONS:
        return "shared physics / kernels"
    if name in INTEGRATION:
        return "control / integration"
    return "supporting hardware / compute"


USER_AGENT = "reactor-atlas-repository-audit/2.0"
SOURCE = HERE / "source_snapshot.json"
FIELDS = [
    "name",
    "url",
    "description",
    "category",
    "language",
    "license",
    "updated_at",
    "archived",
    "fork",
    "topics",
    "evidence_boundary",
    "source_url",
    "retrieved",
]
OUTPUT_NAMES = (
    "reactor_repositories.tsv",
    "reactor_repositories.json",
    "anulum_reactor_repos.json",
    "anulum_reactor_repos.js",
)


def check_https(url: str) -> None:
    """Require an anonymous HTTPS URL for every request and redirect."""
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.port == 0
        or any(c.isspace() for c in url)
    ):
        raise ValueError("source URL must be valid anonymous HTTPS")


class SourceRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse non-HTTPS or credential-bearing redirect destinations."""

    max_redirections = 5

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> urllib.request.Request | None:
        """Validate the real server's destination before urllib follows it."""
        check_https(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def validate_source(loaded: object) -> list[dict[str, Any]]:
    """Validate real public owner identities and scalar API facts before selection."""
    if isinstance(loaded, dict):
        if (
            loaded.get("schema_version") != "1.0.0"
            or type(loaded.get("record_count")) is not int
            or not isinstance(loaded.get("records"), list)
            or loaded["record_count"] != len(loaded["records"])
        ):
            raise ValueError("source envelope requires its exact schema/count/records")
        records = loaded["records"]
    elif isinstance(loaded, list):
        records = loaded
    else:
        raise ValueError("source must be an API list or a versioned snapshot")
    if not records:
        raise ValueError("public source contains no repositories")
    seen: set[str] = set()
    validated: list[dict[str, Any]] = []
    for repo in records:
        if (
            not isinstance(repo, dict)
            or not isinstance(repo.get("name"), str)
            or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo["name"])
        ):
            raise ValueError("public repository requires a valid name")
        name = repo["name"]
        if name.casefold() in seen:
            raise ValueError("public source contains duplicate repository identities")
        seen.add(name.casefold())
        if (
            repo.get("private") is not False
            or repo.get("html_url") != "https://github.com/anulum/" + name
            or repo.get("url") != "https://api.github.com/repos/anulum/" + name
        ):
            raise ValueError("repository must be public and have the exact ANULUM source identity")
        for field in ("description", "language"):
            if repo.get(field) is not None and not isinstance(repo[field], str):
                raise ValueError("repository description/language must be text or null")
        if type(repo.get("archived")) is not bool or type(repo.get("fork")) is not bool:
            raise ValueError("repository archived/fork flags must be boolean")
        licence = repo.get("license")
        if licence is not None and (
            not isinstance(licence, dict)
            or (licence.get("spdx_id") is not None and not isinstance(licence["spdx_id"], str))
        ):
            raise ValueError("repository licence metadata must be an object with text/null SPDX ID")
        topics = repo.get("topics")
        if topics is not None and (
            not isinstance(topics, list)
            or any(not isinstance(t, str) or not t.strip() for t in topics)
        ):
            raise ValueError("repository topics must be a list of nonempty text")
        if (
            not isinstance(repo.get("updated_at"), str)
            or datetime.fromisoformat(repo["updated_at"]).tzinfo is None
        ):
            raise ValueError("repository updated_at requires an ISO timestamp with timezone")
        validated.append(repo)
    return validated


def next_page(link: str, current: str, origin: str) -> str | None:
    """Follow the documented next relation only within the original API endpoint."""
    result = None
    for segment in link.split(",") if link else []:
        match = re.fullmatch(r'<([^<>]+)>;\s*rel="([^"\n]+)"', segment.strip())
        if not match:
            raise ValueError("malformed API Link header")
        if "next" not in match[2].split():
            continue
        if result is not None:
            raise ValueError("API Link header has multiple next relations")
        result = urllib.parse.urljoin(current, match[1])
        check_https(result)
        parsed, base = urllib.parse.urlsplit(result), urllib.parse.urlsplit(origin)
        if (parsed.netloc, parsed.path) != (base.netloc, base.path) or parsed.fragment:
            raise ValueError("pagination must remain within its anonymous API endpoint")
    return result


def fetch_repositories(
    url: str = API,
    *,
    ca_file: Path | None = None,
    timeout: float = 60,
    max_bytes: int = 32 * 1024 * 1024,
    max_pages: int = 100,
) -> list[dict[str, Any]]:
    """Collect every linked API page with trusted TLS and finite resource limits."""
    check_https(url)
    if not math.isfinite(timeout) or timeout <= 0 or max_bytes <= 0 or max_pages <= 0:
        raise ValueError("API limits must be positive and finite")
    context = ssl.create_default_context(cafile=str(ca_file) if ca_file else None)
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=context), SourceRedirect()
    )
    current: str | None = url
    visited: set[str] = set()
    records = []
    total = 0
    while current is not None:
        if current in visited or len(visited) >= max_pages:
            raise ValueError("API pagination loops or exceeds its page limit")
        visited.add(current)
        request = urllib.request.Request(
            current, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
        )
        with opener.open(request, timeout=timeout) as response:
            if response.status != 200:
                raise ValueError(f"API returned HTTP {response.status}")
            raw = response.read(max_bytes - total + 1)
            link = response.headers.get("Link", "")
        total += len(raw)
        if total > max_bytes:
            raise ValueError("API pages exceed the total byte limit")
        payload = json.loads(raw)
        if not isinstance(payload, list):
            raise ValueError("API page must contain a repository list")
        records.extend(payload)
        current = next_page(link, current, url)
    return validate_source(records)


def catalogue_rows(loaded: object, *, retrieved: str) -> list[dict[str, Any]]:
    """Keep the original fixed portfolio selection and evidence boundaries."""
    if date.fromisoformat(retrieved).isoformat() != retrieved:
        raise ValueError("retrieval date must be an exact ISO calendar date")
    repositories = validate_source(loaded)
    rows = []
    for repo in repositories:
        name = repo["name"]
        if name not in RELEVANT:
            continue
        group = category(name)
        rows.append(
            {
                "name": name,
                "url": repo["html_url"],
                "description": repo.get("description") or "No public description provided.",
                "category": group,
                "language": repo.get("language") or "not specified",
                "license": (repo.get("license") or {}).get("spdx_id")
                or "not asserted by GitHub metadata",
                "updated_at": repo["updated_at"],
                "archived": bool(repo.get("archived")),
                "fork": bool(repo.get("fork")),
                "topics": repo.get("topics") or [],
                "evidence_boundary": BOUNDARIES[group],
                "source_url": repo["url"],
                "retrieved": retrieved,
            }
        )
    rows.sort(key=lambda row: (row["category"], row["name"].casefold()))
    if not (len(rows) == len(RELEVANT)):
        raise ValueError(f"expected {len(RELEVANT)} repositories, found {len(rows)}")

    return rows


def render_outputs(rows: list[dict[str, Any]]) -> dict[str, bytes]:
    """Render all four historical formats before any requested output is changed."""
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({**row, "topics": "; ".join(row["topics"])})
    document = {"schema_version": "1.0.0", "record_count": len(rows), "records": rows}
    payload = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    text = {
        OUTPUT_NAMES[0]: stream.getvalue(),
        OUTPUT_NAMES[1]: payload,
        OUTPUT_NAMES[2]: payload,
        OUTPUT_NAMES[3]: "window.ANULUM_REACTOR_REPOS = " + payload.rstrip() + ";\n",
    }
    return {name: value.encode("utf-8") for name, value in text.items()}


def check_output(path: Path, inputs: tuple[Path, ...] = ()) -> None:
    """Protect every accepted Atlas file and resolved caller-supplied input."""
    target = path.resolve()
    if target.is_relative_to(LIBRARY) or target in {p.resolve() for p in inputs}:
        raise ValueError("output must be separate from historical Atlas files and inputs")


def atomic_write(path: Path, body: bytes) -> None:
    """Replace one explicit output atomically; a complete bundle is not a transaction."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(body)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build(
    loaded: object, output_dir: Path, *, retrieved: str, inputs: tuple[Path, ...] = ()
) -> int:
    """Write an isolated catalogue bundle after full source/output validation."""
    for name in OUTPUT_NAMES:
        check_output(output_dir / name, inputs)
    rows = catalogue_rows(loaded, retrieved=retrieved)
    rendered = render_outputs(rows)
    for name, body in rendered.items():
        atomic_write(output_dir / name, body)
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    """Reproduce dated offline catalogues or prepare an explicit online candidate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--snapshot-out", type=Path)
    parser.add_argument("--date")
    parser.add_argument("--api-url", default=API)
    parser.add_argument("--ca-file", type=Path)
    args = parser.parse_args(argv)
    try:
        inputs = (args.source, *((args.ca_file,) if args.ca_file else ()))
        outputs = tuple(args.output_dir / name for name in OUTPUT_NAMES)
        for output in outputs:
            check_output(output, (*inputs, *((args.snapshot_out,) if args.snapshot_out else ())))
        retrieved = args.date or (date.today().isoformat() if args.refresh else "2026-09-27")
        if args.refresh:
            if args.snapshot_out is None:
                raise ValueError("refresh requires an explicit separate snapshot output")
            check_output(args.snapshot_out, (*inputs, *outputs))
            records = fetch_repositories(args.api_url, ca_file=args.ca_file)
            loaded = {
                "schema_version": "1.0.0",
                "record_count": len(records),
                "records": records,
                "retrieved": retrieved,
            }
            # Prepare all bytes first, including date/portfolio checks, before writing snapshot.
            rows = catalogue_rows(loaded, retrieved=retrieved)
            rendered = render_outputs(rows)
            snapshot = (json.dumps(loaded, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            atomic_write(args.snapshot_out, snapshot)
            for name, body in rendered.items():
                atomic_write(args.output_dir / name, body)
            size = len(rows)
        elif args.snapshot_out or args.ca_file or args.api_url != API:
            raise ValueError("API/CA/snapshot options require --refresh")
        else:
            if args.source.resolve() != SOURCE.resolve() and args.date is None:
                raise ValueError("a custom frozen source requires its explicit capture date")
            size = build(
                json.loads(args.source.read_bytes()),
                args.output_dir,
                retrieved=retrieved,
                inputs=inputs,
            )
    except (OSError, UnicodeError, csv.Error, ValueError, TypeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"wrote {size} reactor-ecosystem repositories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
