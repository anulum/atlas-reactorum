# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — facility fields original input readers

"""Read complete reviewed native inputs without changing their original cells."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

MAX_SOURCE_BYTES = 32 * 1024 * 1024


@dataclass(frozen=True)
class NativeInput:
    """Complete original source or target table and its reviewed binding.

    Attributes
    ----------
    key : str
        Source namespace or target layer.
    path : str
        Relative original-artifact path.
    sha256 : str
        Reviewed digest of every input byte.
    metadata : dict of str to object
        Original URL, licence, capture date and declared shape.
    rows : list of dict
        Complete native records with original scalar values.
    """

    key: str
    path: str
    sha256: str
    metadata: dict[str, object]
    rows: list[dict[str, object]]


def mapping(value: object) -> dict[str, object]:
    """Require a decoded native JSON object.

    Parameters
    ----------
    value : object
        Decoded native JSON value.

    Returns
    -------
    dict of str to object
        Original object values without scalar conversion.

    Raises
    ------
    ValueError
        The decoded value is not a JSON object.
    """
    if not isinstance(value, dict):
        raise ValueError("source object required")
    return cast(dict[str, object], value)


def text(value: object) -> str:
    """Require a nonblank original string while retaining all of its whitespace.

    Parameters
    ----------
    value : object
        Native source value.

    Returns
    -------
    str
        Exact original cell.

    Raises
    ------
    ValueError
        A required original value is absent or not text.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("nonblank original text required")
    return value


def original_rows(value: object) -> list[dict[str, object]]:
    """Require a complete native record array.

    Parameters
    ----------
    value : object
        Decoded records or features.

    Returns
    -------
    list of dict
        Native objects in their original order.

    Raises
    ------
    ValueError
        The source does not contain an array of objects.
    """
    if not isinstance(value, list):
        raise ValueError("source record array required")
    return [mapping(row) for row in value]


def source_path(root: Path, relative: str) -> Path:
    """Resolve an original source path without following symlinks or escapes.

    Parameters
    ----------
    root : pathlib.Path
        Complete original source directory.
    relative : str
        Exact source-relative path.

    Returns
    -------
    pathlib.Path
        Unaliased original input.

    Raises
    ------
    ValueError
        A source path escapes its root or uses a symlink.
    """
    path = Path(relative)
    if (
        any(parent.is_symlink() for parent in (root, *root.parents))
        or path.is_absolute()
        or ".." in path.parts
        or not path.parts
    ):
        raise ValueError("source path must stay inside its original root")
    target = root / path
    if any(
        (root / Path(*path.parts[:index])).is_symlink() for index in range(1, len(path.parts) + 1)
    ):
        raise ValueError("source symlinks are refused")
    if not target.is_file():
        raise ValueError("complete regular source file required")
    return target


def bound_bytes(root: Path, relative: str, sha256: str) -> bytes:
    """Read an exact reviewed input, refusing symlinks or path escapes.

    Parameters
    ----------
    root : pathlib.Path
        Complete original-source checkout.
    relative : str
        Source-relative artifact path.
    sha256 : str
        Reviewed digest retained in the source pin ledger.

    Returns
    -------
    bytes
        Every original byte.

    Raises
    ------
    ValueError
        A path or digest differs from the reviewed input.
    OSError
        The complete original artifact cannot be read.
    """
    target = source_path(root, relative)
    with target.open("rb") as stream:
        body = stream.read(MAX_SOURCE_BYTES + 1)
    if len(body) > MAX_SOURCE_BYTES:
        raise ValueError("source artifact exceeds the bounded-file contract")
    if hashlib.sha256(body).hexdigest() != sha256:
        raise ValueError("source bytes differ from their reviewed digest")
    return body


def read_input(root: Path, key: str, metadata: dict[str, object]) -> NativeInput:
    """Read all native cells under a declared reviewed input contract.

    Parameters
    ----------
    root : pathlib.Path
        Complete source checkout.
    key : str
        Source namespace.
    metadata : dict of str to object
        Reviewed path, digest, row count and native format.

    Returns
    -------
    NativeInput
        Complete original observations, preserving nulls and sentinels.

    Raises
    ------
    ValueError
        Hash, count, native shape or source envelope is invalid.
    OSError
        An original input is unavailable.
    """
    path, digest = text(metadata["path"]), text(metadata["sha256"])
    body = bound_bytes(root, path, digest)
    kind = text(metadata.get("format", "tsv"))
    if kind in {"csv", "tsv"}:
        reader = csv.DictReader(
            io.StringIO(body.decode("utf-8"), newline=""), delimiter="," if kind == "csv" else "\t"
        )
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("source table has incomplete or oversized rows")
            rows.append(mapping(row))
    elif kind in {"records", "features"}:
        document = mapping(json.loads(body))
        rows = original_rows(document[kind])
        if kind == "records" and (
            type(document.get("count")) is not int or document["count"] != len(rows)
        ):
            raise ValueError("source count does not match all records")
        if kind == "features":
            rows = [mapping(row["attributes"]) for row in rows]
    else:
        raise ValueError("unsupported native source format")
    expected = metadata["rows"]
    if type(expected) is not int or expected <= 0 or len(rows) != expected:
        raise ValueError("complete reviewed source count required")
    return NativeInput(key, path, digest, metadata, rows)


def read_inputs(root: Path) -> tuple[dict[str, NativeInput], dict[str, NativeInput]]:
    """Read every reviewed source and all four complete original target tables.

    Parameters
    ----------
    root : pathlib.Path
        Source checkout containing the reviewed original research inputs.

    Returns
    -------
    tuple of dict
        Ten complete native sources and four complete target datasets.

    Raises
    ------
    ValueError
        The pin ledger or any complete input differs from its declared scope.
    OSError
        A required source is unavailable.
    """
    pins = mapping(
        json.loads(source_path(root, "metadata/facility_fields/source_pins.json").read_bytes())
    )
    if type(pins["schema_version"]) is not int or pins["schema_version"] != 1:
        raise ValueError("unsupported source pin schema")
    sources, targets = mapping(pins["sources"]), mapping(pins["target_datasets"])
    if set(sources) != {
        "wri",
        "agstar-Mixed",
        "agstar-Cattle",
        "agstar-Poultry",
        "agstar-Swine",
        "agstar-Dairy",
        "br-epe-biomethane",
        "us-epa-lmop",
        "industrial7",
        "industrial6-snapshot",
    } or set(targets) != {"wri", "agstar", "industrial6", "industrial7"}:
        raise ValueError("complete reviewed source and target scope required")
    return (
        {key: read_input(root, key, mapping(value)) for key, value in sources.items()},
        {key: read_input(root, key, mapping(value)) for key, value in targets.items()},
    )
