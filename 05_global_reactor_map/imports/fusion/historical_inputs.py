#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — explicit immutable historical inputs
"""Verify explicit offline historical inputs and capture an owned snapshot.

Custody hashes do not grant redistribution. Every input is read once and checked
before output begins. Public inputs contain the attributed compilation selection;
frozen inputs preserve the original complete data. No download fallback exists.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import stat
from pathlib import Path
from typing import Literal, TypedDict

Selection = Literal["public", "frozen"]
MEMBERS = (
    "fusion_facilities.tsv",
    "source_registry.tsv",
    "enrichment/enrichment.tsv",
    "enrichment/new_facilities.tsv",
    "enrichment/source_registry.tsv",
    "enrichment_round2/enrichment_round2.tsv",
    "enrichment_round2/source_registry.tsv",
    "enrichment_round3/enrichment_round3.tsv",
    "enrichment_round3/source_registry.tsv",
)


class InputSpec(TypedDict):
    """Declare exact bytes, schema and row count for one historical input."""

    bytes: int
    sha256: str
    fields: list[str]
    rows: int


SPECIFICATIONS: dict[str, dict[str, InputSpec]] = json.loads(
    Path(__file__).with_name("frozen_input_manifest.json").read_text(encoding="utf-8")
)["selections"]


def read_bundle(source: Path, *, selection: Selection) -> dict[str, bytes]:
    """Read all nine regular files and verify exact bytes, schemas and rows.

    Parameters
    ----------
    source:
        Explicit caller-supplied directory with the declared relative files.
    selection:
        Public attributed subset or original frozen inputs. Neither is a grant.

    Returns
    -------
    dict of str to bytes
        Verified bytes captured once for an owned snapshot.

    Raises
    ------
    ValueError
        For changed, escaped or structurally invalid input.
    OSError
        When an input cannot be read.
    """
    root = source.resolve(strict=True)
    expected = SPECIFICATIONS[selection]
    if set(expected) != set(MEMBERS):
        raise ValueError("historical input manifest has an unexpected member set")
    payloads: dict[str, bytes] = {}
    for member in MEMBERS:
        spec = expected[member]
        path = (root / member).resolve(strict=True)
        if not path.is_relative_to(root):
            raise ValueError(f"{member}: input escapes the supplied bundle")
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ValueError(f"{member}: input must be a regular file")
            data = handle.read(spec["bytes"] + 1)
        if len(data) != spec["bytes"] or hashlib.sha256(data).hexdigest() != spec["sha256"]:
            raise ValueError(f"{member}: historical input bytes or SHA-256 changed")
        reader = csv.DictReader(
            io.StringIO(data.decode("utf-8"), newline=""), delimiter="\t", strict=True
        )
        if reader.fieldnames != spec["fields"]:
            raise ValueError(f"{member}: historical input schema changed")
        rows = list(reader)
        if len(rows) != spec["rows"] or any(None in row or None in row.values() for row in rows):
            raise ValueError(f"{member}: historical input rows changed")
        payloads[member] = data
    return payloads


def materialize(source: Path, destination: Path, *, selection: Selection) -> dict[str, str]:
    """Snapshot verified inputs into an empty caller-owned directory.

    Parameters
    ----------
    source:
        All inputs are validated before output starts.
    destination:
        New or empty owned directory; existing content is never overwritten.
    selection:
        Exact public or complete frozen revision.

    Returns
    -------
    dict of str to str
        Digests of captured inputs. Later source changes cannot alter this copy.

    Raises
    ------
    ValueError
        For invalid input or a nonempty destination.
    OSError
        For input or output I/O failure.
    """
    payloads = read_bundle(source, selection=selection)
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError("historical snapshot destination must be an empty owned directory")
    destination.mkdir(parents=True, exist_ok=True)
    for member, data in payloads.items():
        path = destination / member
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(data)
    return {member: hashlib.sha256(data).hexdigest() for member, data in payloads.items()}


def main(argv: list[str] | None = None) -> int:
    """Snapshot a caller-supplied bundle through the actual offline CLI.

    Parameters
    ----------
    argv:
        Optional arguments. Frozen is the explicit default input selection.

    Returns
    -------
    int
        Zero on success. Invalid inputs receive authored exit2.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--selection", choices=("public", "frozen"), default="frozen")
    args = parser.parse_args(argv)
    try:
        digests = materialize(args.source_root, args.destination, selection=args.selection)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        parser.exit(2, f"Historical inputs refused: {error}\n")
    print(f"PASS: {len(digests)} exact historical inputs captured ({args.selection})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
