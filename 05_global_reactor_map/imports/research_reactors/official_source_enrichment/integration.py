# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — research enrichment source preservation
"""Merge accepted research layers while retaining their original field sources."""

from __future__ import annotations

import csv
import hashlib
import io
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlsplit

FIELDS = ("operator", "purpose", "first_criticality")


class FieldOrigin(TypedDict):
    """Original accepted cell and the source that supplied it.

    Attributes
    ----------
    field, value : str
        Exact field name and source cell, without semantic inference.
    source_dataset, source_sha256 : str
        Source table and digest of its original bytes.
    source_url, source_role : str
        Publisher link and role retained from the original row.
    source_capture_date : str
        Original retrieval date; never substituted for publication or event date.
    license, scope : str
        Source rights and original verification notes.
    selection : str
        Selected current value or a retained superseded assertion.
    """

    field: str
    value: str
    source_dataset: str
    source_sha256: str
    source_url: str
    source_role: str
    source_capture_date: str
    license: str
    scope: str
    selection: str


@dataclass(frozen=True)
class ResearchLayer:
    """Complete accepted source table and its byte binding.

    Attributes
    ----------
    dataset : str
        Path relative to the configured source root, or an external file name.
    sha256 : str
        Digest of the complete original table.
    rows : dict of str to dict
        Exact source cells indexed by their unique stable identity.
    """

    dataset: str
    sha256: str
    rows: dict[str, dict[str, str]]


def read_layer(path: Path, root: Path) -> ResearchLayer:
    """Read an original TSV without silently dropping malformed or duplicate rows.

    Parameters
    ----------
    path : pathlib.Path
        Existing research table; symlinks are refused.
    root : pathlib.Path
        Source root used to label the table without exposing an absolute path.

    Returns
    -------
    ResearchLayer
        Complete original rows and their source-byte digest.

    Raises
    ------
    ValueError
        A source is aliased, lacks identity or has malformed or duplicate rows.
    OSError
        The original table cannot be read.
    """
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("research source symlinks are refused")
    body = path.read_bytes()
    reader = csv.DictReader(io.StringIO(body.decode("utf-8"), newline=""), delimiter="\t")
    if not reader.fieldnames or "stable_id" not in reader.fieldnames:
        raise ValueError("research source identity column required")
    rows: dict[str, dict[str, str]] = {}
    for original in reader:
        if None in original or any(value is None for value in original.values()):
            raise ValueError("complete original research source rows required")
        row = dict(original)
        identity = row["stable_id"]
        if not identity.strip() or identity in rows:
            raise ValueError("unique nonblank research source identity required")
        rows[identity] = row
    dataset = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name
    return ResearchLayer(dataset, hashlib.sha256(body).hexdigest(), rows)


def merge_layers(
    source_row: dict[str, str], base: ResearchLayer, layers: Sequence[ResearchLayer]
) -> tuple[dict[str, str], list[str], list[FieldOrigin], bool]:
    """Apply accepted layers in order and preserve every original field assertion.

    Parameters
    ----------
    source_row : dict of str to str
        Original base row with its stable identity.
    base : ResearchLayer
        Complete original base source and byte binding.
    layers : sequence of ResearchLayer
        Accepted enrichment sources in their original precedence order.

    Returns
    -------
    tuple
        Merged cells, all source URLs in first-seen order, original operator,
        purpose and criticality assertions, and whether an overlay was applied.
        Superseded values remain assertions; they never replace a selected cell.

    Raises
    ------
    ValueError
        An original row differs from its source or a source URL is unsafe.
    """
    identity = source_row["stable_id"]
    if base.rows.get(identity) != source_row:
        raise ValueError("research row differs from its original base source")
    matched = [layer for layer in layers if identity in layer.rows]
    combined = dict(source_row)
    urls: list[str] = []
    origins: list[FieldOrigin] = []
    for layer in (base, *matched):
        row = layer.rows[identity]
        for url in row.get("source_url", "").split("|"):
            if not url:
                continue
            parsed = urlsplit(url)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
            ):
                raise ValueError("anonymous HTTPS research source required")
            if url not in urls:
                urls.append(url)
        for field in FIELDS:
            value = row.get(field, "")
            if not value:
                continue
            for previous in origins:
                if previous["field"] == field:
                    previous["selection"] = "superseded"
            origins.append(
                FieldOrigin(
                    field=field,
                    value=value,
                    source_dataset=layer.dataset,
                    source_sha256=layer.sha256,
                    source_url=row.get("source_url", ""),
                    source_role=row.get("source_role", ""),
                    source_capture_date=row.get("retrieved", row.get("retrieved_date", "")),
                    license=row.get("license", ""),
                    scope=row.get("verification_notes", ""),
                    selection="selected",
                )
            )
        combined.update({key: value for key, value in row.items() if value})
    if not urls:
        raise ValueError("research row has no original source URL")
    return combined, urls, origins, bool(matched)
