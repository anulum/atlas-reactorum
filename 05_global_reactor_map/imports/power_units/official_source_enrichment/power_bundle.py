# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — power-unit source bundle
"""Bind power field projection to the frozen TSV and every complete producer input."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from power_contract import digest, mapping
from power_projection import PowerProjection, project_fields

ORIGINAL_SHA256 = "42d46f0426f47886aba872a3711c242dc2c32b3b0f4b535d727d151ed1b77f3b"
MEMBERS = ("primary-sources.json", "primary-fields.json", "primary-projection.json")


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate JSON keys before a later value can conceal an earlier claim."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate power bundle JSON key")
        result[key] = value
    return result


def read_document(path: Path) -> dict[str, object]:
    """Read an original regular UTF-8 JSON member, refusing linked or non-object inputs."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("power bundle member must be a regular original file")
    value: object = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    return mapping(value)


def read_source(path: Path) -> list[dict[str, str]]:
    """Read the pinned original 1,823-row TSV without normalising any source cell.

    Parameters
    ----------
    path : pathlib.Path
        Original power-unit source, or an exact regular copy for an offline build.

    Returns
    -------
    list of dict
        All original string-valued rows in their source order.

    Raises
    ------
    ValueError
        The file is linked, changed or not the complete original cohort.
    OSError
        The original bytes cannot be read.
    """
    if path.is_symlink() or not path.is_file():
        raise ValueError("power baseline must be a regular original TSV")
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != ORIGINAL_SHA256:
        raise ValueError("power baseline differs from the frozen original TSV")
    table = list(csv.reader(io.StringIO(body.decode("utf-8")), delimiter="\t", strict=True))
    header, records = table[0], table[1:]
    return [dict(zip(header, cells, strict=True)) for cells in records]


def produce(source: Path, directory: Path) -> tuple[PowerProjection, dict[str, object]]:
    """Reconstruct the whole projection from source metadata and author field decisions.

    Parameters
    ----------
    source : pathlib.Path
        Byte-identical original power-unit source.
    directory : pathlib.Path
        Directory containing both original source and field metadata members.

    Returns
    -------
    tuple
        Complete projection and the deterministic, hash-bound product document.

    Raises
    ------
    ValueError
        A document schema, baseline binding or entire target set is inconsistent.
    OSError
        An original producer member cannot be read.
    """
    original = read_source(source)
    paths = [directory / name for name in MEMBERS[:2]]
    sources, fields = (read_document(path) for path in paths)
    for document in (sources, fields):
        if document.get("schema_version") != "1.0.0":
            raise ValueError("power producer schema is unsupported")
        if digest(document.get("source_tsv_sha256")) != ORIGINAL_SHA256:
            raise ValueError("power producer binding differs from the original TSV")
    projection = project_fields(original, fields.get("fields"), sources.get("sources"))
    document = {
        "schema_version": "1.0.0",
        "source_tsv_sha256": ORIGINAL_SHA256,
        "sources_sha256": hashlib.sha256(paths[0].read_bytes()).hexdigest(),
        "fields_sha256": hashlib.sha256(paths[1].read_bytes()).hexdigest(),
        "record_count": len(projection.rows),
        "field_count": len(projection.decisions),
        "selected_fields": sum(row["disposition"] == "qualified" for row in projection.decisions),
        "rows": list(projection.rows),
        "decisions": list(projection.decisions),
        "source_records": list(projection.sources),
    }
    return projection, document


def load_projection(source: Path, directory: Path) -> PowerProjection | None:
    """Accept a whole reproducible bundle or preserve an unmodified historical build.

    Parameters
    ----------
    source : pathlib.Path
        Original TSV consumed by the owning power facility builder.
    directory : pathlib.Path
        Source directory containing every member in ``MEMBERS``.

    Returns
    -------
    PowerProjection or None
        Independently reconstructed rows and all decisions. An entirely absent
        historical bundle leaves the caller's original source unchanged.

    Raises
    ------
    ValueError
        A partial, linked, changed or inconsistent bundle is present.
    OSError
        A producer member cannot be read.
    """
    paths = [directory / name for name in MEMBERS]
    present = [path.exists() or path.is_symlink() for path in paths]
    if not any(present):
        return None
    if not all(present):
        raise ValueError("power source bundle is incomplete")
    projection, expected = produce(source, directory)
    actual = read_document(paths[2])
    if (
        any(
            type(actual.get(key)) is not int
            for key in ("record_count", "field_count", "selected_fields")
        )
        or actual != expected
    ):
        raise ValueError("power projection differs from its complete producer inputs")
    return projection
