# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — offline FFDB visible dashboard reader

"""Decode complete ordinary visible FFDB captures without network access.

Raw publisher values and display aliases remain separate. Rendering tuple
positions are retained for provenance and never used as stable facility IDs.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .framing import decode_frames
from .values import DashboardRefused, descend, integer, number, object_list, object_map, text

type Scalar = str | int | float
TABLE_FIELDS = (
    "Configuration",
    "Country",
    "Organization",
    "Facility Name",
    "Ownership",
    "Design",
    "Status",
    "Type",
)
MAP_FIELDS = (*TABLE_FIELDS, "Latitude", "Longitude", "Website")
SOURCE_URL = "https://nucleus.iaea.org/sites/fusion-portal/SitePages/FFDB.aspx?web=1"
PROJECTION_KIND = "atlas-ffdb-visible-data-selection-v1"


@dataclass(frozen=True)
class Cell:
    """Retain the source value and its independently supplied display alias."""

    raw: Scalar
    display: Scalar


@dataclass(frozen=True)
class Record:
    """Retain one visible record, including its view-local rendering position."""

    view: str
    tuple_id: int
    cells: dict[str, Cell]

    @property
    def identity(self) -> tuple[str, str, str]:
        """Return exact facility, country and organisation source text."""
        return (
            text(self.cells["Facility Name"].raw),
            text(self.cells["Country"].raw),
            text(self.cells["Organization"].raw),
        )


@dataclass(frozen=True)
class Dashboard:
    """Carry the complete visible table and its source-specific map subset."""

    table: tuple[Record, ...]
    map_points: tuple[Record, ...]
    source_sha256: str
    original_response_sha256: str
    source_kind: str
    retrieved_date: str | None


def _origin(header: dict[str, object], digest: str) -> tuple[str, str, str | None]:
    if "atlas_projection" not in header:
        return digest, "publisher-viewer-response", None
    projection = object_map(descend(header, ("atlas_projection",)))
    required = {
        "schema_version",
        "kind",
        "source_url",
        "original_response_sha256",
        "retrieved_date",
    }
    if set(header) != {"atlas_projection"} or set(projection) != required:
        raise DashboardRefused("FFDB selection header has an invalid member set.")
    if (
        integer(descend(projection, ("schema_version",))) != 1
        or text(descend(projection, ("kind",))) != PROJECTION_KIND
        or text(descend(projection, ("source_url",))) != SOURCE_URL
    ):
        raise DashboardRefused("FFDB selection header has an unsupported source identity.")
    original = text(descend(projection, ("original_response_sha256",)))
    if re.fullmatch(r"[0-9a-f]{64}", original) is None:
        raise DashboardRefused("FFDB selection header has an invalid original-response SHA-256.")
    retrieved = text(descend(projection, ("retrieved_date",)))
    try:
        checked = date.fromisoformat(retrieved)
    except ValueError:
        raise DashboardRefused("FFDB selection acquisition date must be canonical ISO.") from None
    if checked.isoformat() != retrieved:
        raise DashboardRefused("FFDB selection acquisition date must be canonical ISO.")
    return original, PROJECTION_KIND, retrieved


def _dictionaries(secondary: dict[str, object]) -> dict[str, tuple[Scalar, ...]]:
    columns = object_list(
        descend(
            secondary,
            (
                "dataDictionary",
                "presModelHolder",
                "genDataDictionaryPresModel",
                "dataSegments",
                "0",
                "dataColumns",
            ),
        )
    )
    dictionaries: dict[str, tuple[Scalar, ...]] = {}
    for column in columns:
        dtype = text(descend(column, ("dataType",)))
        if dtype not in {"cstring", "integer", "real"} or dtype in dictionaries:
            raise DashboardRefused("FFDB source has unsupported or duplicate dictionary types.")
        members = object_list(descend(column, ("dataValues",)))
        if dtype == "cstring":
            values: tuple[Scalar, ...] = tuple(text(member) for member in members)
        elif dtype == "integer":
            values = tuple(integer(member) for member in members)
        else:
            values = tuple(number(member) for member in members)
        dictionaries[dtype] = values
    if set(dictionaries) != {"cstring", "integer", "real"}:
        raise DashboardRefused("FFDB source is missing a typed dictionary.")
    return dictionaries


def _indices(column: object, name: str, count: int) -> list[int]:
    indices = [integer(value) for value in object_list(descend(column, (name,)))]
    if len(indices) != count:
        raise DashboardRefused("FFDB source column lengths do not match its records.")
    return indices


def _cells(
    column: object,
    dictionary: tuple[Scalar, ...],
    aliases: tuple[Scalar, ...],
    count: int,
) -> tuple[Cell, ...]:
    values = _indices(column, "valueIndices", count)
    display = _indices(column, "aliasIndices", count)
    result: list[Cell] = []
    for value, alias in zip(values, display, strict=True):
        alias_position = -alias - 1 if alias < 0 else alias
        if not 0 <= value < len(dictionary) or not 0 <= alias_position < len(aliases):
            raise DashboardRefused("FFDB source dictionary index is out of bounds.")
        raw = dictionary[value]
        result.append(Cell(raw, aliases[alias_position]))
    return tuple(result)


def _view(
    views: dict[str, object],
    name: str,
    dictionaries: dict[str, tuple[Scalar, ...]],
) -> tuple[Record, ...]:
    pane = descend(
        views,
        (
            name,
            "presModelHolder",
            "genVizDataPresModel",
            "paneColumnsData",
        ),
    )
    panes = object_list(descend(pane, ("paneColumnsList",)))
    if len(panes) != 1:
        raise DashboardRefused("FFDB source requires one complete visible pane.")
    columns = object_list(descend(panes[0], ("vizPaneColumns",)))
    if not columns:
        raise DashboardRefused("FFDB source has no visible columns.")
    tuple_ids = [integer(value) for value in object_list(descend(columns[0], ("tupleIds",)))]
    if not tuple_ids or min(tuple_ids) < 0 or len(set(tuple_ids)) != len(tuple_ids):
        raise DashboardRefused("FFDB source tuple positions must be nonnegative and unique.")
    metadata = object_list(descend(pane, ("vizDataColumns",)))
    if not metadata or [
        integer(index) for index in object_list(descend(metadata[0], ("columnIndices",)))
    ] != [0]:
        raise DashboardRefused("FFDB source has an invalid tuple column.")
    fields: dict[str, tuple[Cell, ...]] = {}
    column_positions: set[int] = {0}
    for meta in metadata[1:]:
        caption = text(descend(meta, ("fieldCaption",)))
        dtype = text(descend(meta, ("dataType",)))
        expected = "real" if caption in {"Latitude", "Longitude"} else "cstring"
        if dtype != expected or caption in fields:
            raise DashboardRefused("FFDB source has invalid field captions or types.")
        pane_indices = object_list(descend(meta, ("paneIndices",)))
        column_indices = object_list(descend(meta, ("columnIndices",)))
        if [integer(index) for index in pane_indices] != [0] or len(column_indices) != 1:
            raise DashboardRefused("FFDB source has unsupported pane or column references.")
        index = integer(column_indices[0])
        if not 0 < index < len(columns) or index in column_positions:
            raise DashboardRefused("FFDB source column reference is out of bounds or duplicated.")
        column_positions.add(index)
        fields[caption] = _cells(
            columns[index], dictionaries[dtype], dictionaries["cstring"], len(tuple_ids)
        )
    required = TABLE_FIELDS if name == "Table" else MAP_FIELDS
    if set(fields) != set(required) or column_positions != set(range(len(columns))):
        raise DashboardRefused("FFDB source does not contain its complete visible field set.")
    records = tuple(
        Record(name, identifier, {field: cells[row] for field, cells in fields.items()})
        for row, identifier in enumerate(tuple_ids)
    )
    for record in records:
        for field in TABLE_FIELDS:
            value = text(record.cells[field].raw)
            if not value.strip() or any(char in value for char in "\t\r\n\x00"):
                raise DashboardRefused("FFDB source contains an empty or multiline table field.")
    if len({record.identity for record in records}) != len(records):
        raise DashboardRefused("FFDB source contains duplicate facility identities.")
    return records


def parse_dashboard(payload: bytes) -> Dashboard:
    """Decode and validate both complete visible publisher views.

    Parameters
    ----------
    payload : bytes
        Original viewer response or explicitly labelled selection. Frame lengths
        count Unicode characters; selected bytes carry a distinct digest.

    Returns
    -------
    Dashboard
        Source table, map subset, artifact digest and original-response linkage.

    Raises
    ------
    DashboardRefused
        If framing, dictionaries, view structure, identity or coordinates fail.
    """
    frames = decode_frames(payload)
    digest = hashlib.sha256(payload).hexdigest()
    original_digest, kind, retrieved = _origin(frames[0], digest)
    secondary = object_map(descend(frames[1], ("secondaryInfo", "presModelMap")))
    dictionaries = _dictionaries(secondary)
    views = object_map(
        descend(
            secondary,
            (
                "vizData",
                "presModelHolder",
                "genPresModelMapPresModel",
                "presModelMap",
            ),
        )
    )
    table = _view(views, "Table", dictionaries)
    points = _view(views, "Main", dictionaries)
    by_identity = {record.identity: record for record in table}
    for point in points:
        original = by_identity.get(point.identity)
        if original is None or any(
            original.cells[field].raw != point.cells[field].raw for field in TABLE_FIELDS
        ):
            raise DashboardRefused("FFDB map does not agree with the complete source table.")
        lat, lon = number(point.cells["Latitude"].raw), number(point.cells["Longitude"].raw)
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise DashboardRefused("FFDB source map coordinates are outside geographic bounds.")
        text(point.cells["Website"].raw)
    return Dashboard(table, points, digest, original_digest, kind, retrieved)


def read_dashboard(source: Path, expected_sha256: str | None = None) -> Dashboard:
    """Read a local capture, optionally requiring its registered SHA-256.

    Parameters
    ----------
    source : pathlib.Path
        Pinned local artifact, never fetched or refreshed by this function.
    expected_sha256 : str or None
        Registered digest when reproducing a frozen source revision.

    Returns
    -------
    Dashboard
        Validated complete visible source views.

    Raises
    ------
    DashboardRefused
        If the source cannot be read, does not match its digest or is malformed.
    """
    try:
        payload = source.read_bytes()
    except OSError:
        raise DashboardRefused("FFDB source cannot be read.") from None
    if expected_sha256 is not None and hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise DashboardRefused("FFDB source does not match its registered SHA-256.")
    return parse_dashboard(payload)
