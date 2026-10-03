# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — offline FFDB catalogue command

"""Reproduce a pinned FFDB import into a new output directory."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    __package__ = "05_global_reactor_map.imports.fusion.ffdb"

from .catalogue import FIELDS, Catalogue, build_catalogue
from .reader import PROJECTION_KIND, SOURCE_URL, Dashboard, read_dashboard
from .values import DashboardRefused, descend, integer, object_map, text

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SOURCE = Path(__file__).with_name("visible_data.frames")
DEFAULT_MANIFEST = Path(__file__).with_name("source_manifest.json")


def load_source_manifest(path: Path) -> tuple[str, str, str]:
    """Validate the pinned source digest and actual capture date.

    Parameters
    ----------
    path : pathlib.Path
        Local source registry, whose URL and capture identity are explicit.

    Returns
    -------
    tuple of str
        Artifact SHA-256, acquisition date and original-response SHA-256.

    Raises
    ------
    DashboardRefused
        If the registry is unreadable, malformed or has another source identity.
    """
    try:
        value: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise DashboardRefused("FFDB source registry cannot be read as valid JSON.") from None
    manifest = object_map(value)
    if integer(descend(manifest, ("schema_version",))) != 2:
        raise DashboardRefused("FFDB source registry has an unsupported version.")
    if text(descend(manifest, ("source_url",))) != SOURCE_URL:
        raise DashboardRefused("FFDB source registry has a different publisher identity.")
    digest = text(descend(manifest, ("artifact_sha256",)))
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise DashboardRefused("FFDB source registry has an invalid SHA-256.")
    original = text(descend(manifest, ("original_response_sha256",)))
    if re.fullmatch(r"[0-9a-f]{64}", original) is None:
        raise DashboardRefused("FFDB source registry has an invalid original-response SHA-256.")
    if text(descend(manifest, ("artifact_kind",))) != PROJECTION_KIND:
        raise DashboardRefused("FFDB source registry requires an explicit visible-data selection.")
    return digest, text(descend(manifest, ("retrieved_date",))), original


def read_source_revision(source: Path, manifest: Path) -> tuple[Dashboard, str]:
    """Validate the selected artifact and its acquisition/original linkage.

    Parameters
    ----------
    source : pathlib.Path
        Pinned visible-data selection, not a full rendering container.
    manifest : pathlib.Path
        Registry with independent artifact and original-response digests.

    Returns
    -------
    tuple of Dashboard and str
        Complete validated views and their registered acquisition date.

    Raises
    ------
    DashboardRefused
        If bytes, source kind, original identity or acquisition date differ.
    """
    digest, retrieved, original = load_source_manifest(manifest)
    dashboard = read_dashboard(source, digest)
    if (
        dashboard.source_kind != PROJECTION_KIND
        or dashboard.original_response_sha256 != original
        or dashboard.retrieved_date != retrieved
    ):
        raise DashboardRefused("FFDB selection differs from its registered acquisition identity.")
    return dashboard, retrieved


def write_catalogue(catalogue: Catalogue, output: Path) -> None:
    """Write both audit products into a newly owned output directory.

    Parameters
    ----------
    catalogue : Catalogue
        Fully validated rows and their bound source-cell provenance.
    output : pathlib.Path
        New directory whose parent already exists. Existing paths are refused.

    Raises
    ------
    OSError
        If a new output directory or product cannot be created.
    """
    output.mkdir()
    with (output / "fusion_facilities.tsv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(catalogue.rows)
    with (output / "field_provenance.json").open("x", encoding="utf-8") as stream:
        json.dump(catalogue.provenance, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    """Validate or reproduce a frozen source without implicit downloads.

    Parameters
    ----------
    argv : list of str or None
        Explicit arguments, or the process command line.

    Returns
    -------
    int
        Zero for a complete validated source; two for an authored refusal.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, help="New directory for both source-bound products")
    args = parser.parse_args(argv)
    try:
        dashboard, retrieved = read_source_revision(args.source, args.manifest)
        catalogue = build_catalogue(dashboard, retrieved)
        if args.output is not None:
            write_catalogue(catalogue, args.output)
    except DashboardRefused as refusal:
        print(str(refusal), file=sys.stderr)
        return 2
    except OSError:
        print("FFDB output cannot be created in a new directory.", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "source_sha256": dashboard.source_sha256,
                "original_response_sha256": dashboard.original_response_sha256,
                "source_kind": dashboard.source_kind,
                "table_records": len(catalogue.rows),
                "map_records": len(dashboard.map_points),
                "scientific_approval": False,
                "historical146_reconstructed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
