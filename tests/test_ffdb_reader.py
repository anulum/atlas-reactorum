# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — FFDB reader real source tests

"""Exercise complete visible captures and structural corruption through the reader."""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest

from .conftest import ROOT

LAYER = "05_global_reactor_map/imports/fusion/ffdb"
CAPTURE = ROOT / "tests/data/fusion_ffdb/visible_data.frames"
SECONDARY = ("secondaryInfo", "presModelMap")
DICTIONARY = (
    *SECONDARY,
    "dataDictionary",
    "presModelHolder",
    "genDataDictionaryPresModel",
    "dataSegments",
    "0",
)
VIEWS = (*SECONDARY, "vizData", "presModelHolder", "genPresModelMapPresModel", "presModelMap")
TABLE = (*VIEWS, "Table", "presModelHolder", "genVizDataPresModel", "paneColumnsData")
MAIN = (*VIEWS, "Main", "presModelHolder", "genVizDataPresModel", "paneColumnsData")


@pytest.fixture
def reader() -> ModuleType:
    """Load the production reader used for both complete captures and corruption probes.

    Returns
    -------
    types.ModuleType
        Public dashboard parser, file reader and DashboardRefused exception.
    """
    return importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.reader")


def captured_frames() -> list[dict[str, object]]:
    """Decode the actual capture solely to introduce named corruption probes.

    Returns
    -------
    list of dict
        Fresh decoded frame objects in source order. Character counts are
        checked against each original framing prefix before mutation.
    """
    source = CAPTURE.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    frames: list[dict[str, object]] = []
    offset = 0
    while offset < len(source):
        separator = source.index(";", offset)
        value, end = decoder.raw_decode(source, separator + 1)
        assert end - separator - 1 == int(source[offset:separator])
        frames.append(cast(dict[str, object], value))
        offset = end
    return frames


def framed(frames: list[dict[str, object]]) -> bytes:
    """Reframe mutated copies using the publisher's Unicode character convention.

    Parameters
    ----------
    frames : list of dict
        Source-shaped frame copies, including deliberate invalid test values.

    Returns
    -------
    bytes
        UTF-8 JSON documents prefixed by their Unicode character lengths.
        This helper does not validate the mutated dashboard's semantics.
    """
    documents = [json.dumps(frame, ensure_ascii=False, separators=(",", ":")) for frame in frames]
    return "".join(f"{len(document)};{document}" for document in documents).encode("utf-8")


def node(document: object, path: tuple[str | int, ...]) -> object:
    """Select a member of the actual source shape before mutating that member.

    Parameters
    ----------
    document : object
        Decoded frame containing the original nested dictionaries and lists.
    path : tuple of str or int
        Dictionary keys and list indices selecting the intended mutation site.

    Returns
    -------
    object
        Referenced member; mutations affect the supplied frame copy.

    Raises
    ------
    AssertionError
        A path component encounters a different container type.
    KeyError
        A named source member is absent.
    IndexError
        A source list index is out of range.
    """
    for member in path:
        if isinstance(member, int):
            assert isinstance(document, list)
            document = document[member]
        else:
            assert isinstance(document, dict)
            document = document[member]
    return document


def test_complete_real_capture_retains_raw_coordinates_and_display_aliases(
    reader: ModuleType,
) -> None:
    """Decode the pinned full capture without replacing raw coordinates by display rounding."""
    dashboard = reader.read_dashboard(
        CAPTURE, "640bae831a78d72503f6de9c7107c7c3b511cf117f83d2fe39a778d6cf045d06"
    )
    assert len(dashboard.table) == 174
    assert len(dashboard.map_points) == 137
    first = dashboard.table[0]
    assert first.identity == ("HB11", "Australia", "HB11 Energy")
    assert first.cells["Design"].raw == "Experimental"
    assert first.cells["Design"].display == "Exp"
    point = dashboard.map_points[0]
    assert point.cells["Latitude"].raw == 34.87691
    assert point.cells["Latitude"].display == "34.9"
    assert point.cells["Longitude"].raw == 134.64973
    assert point.cells["Longitude"].display == "134.6"
    assert point.cells["Website"].raw == "%null%"
    assert (
        dashboard.source_sha256
        == "640bae831a78d72503f6de9c7107c7c3b511cf117f83d2fe39a778d6cf045d06"
    )


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"1;{}",
        b"2;{}",
        b"0;{}",
        b"x;{}",
        b"2;{}junk",
        b"2;[]2;{}",
        b"1;\xff",
        b"1;{",
        b'13;{"x":1,"x":2}',
        b'9;{"x":NaN}',
        b"99999999999999999999999999999;{}",
        b"2;{}2;{}2;{}",
    ],
)
def test_invalid_complete_framing_is_authored_refusal(reader: ModuleType, payload: bytes) -> None:
    """Refuse malformed framing, duplicate keys, nonfinite JSON and incomplete frame sets."""
    with pytest.raises(reader.DashboardRefused):
        reader.parse_dashboard(payload)


@pytest.mark.parametrize(
    ("path", "key", "value"),
    [
        ((), "secondaryInfo", []),
        (SECONDARY, "dataDictionary", {}),
        (DICTIONARY, "dataColumns", []),
        (DICTIONARY, "dataColumns", [{}]),
        (TABLE, "paneColumnsList", []),
        ((*TABLE, "paneColumnsList", 0), "vizPaneColumns", []),
        ((*TABLE, "paneColumnsList", 0, "vizPaneColumns", 0), "tupleIds", []),
        ((*TABLE, "paneColumnsList", 0, "vizPaneColumns", 0), "tupleIds", [-1]),
        ((*TABLE, "paneColumnsList", 0, "vizPaneColumns", 0), "tupleIds", [1, 1]),
        (TABLE, "vizDataColumns", []),
        ((*TABLE, "vizDataColumns", 0), "columnIndices", [1]),
        ((*TABLE, "vizDataColumns", 1), "fieldCaption", "Country"),
        ((*TABLE, "vizDataColumns", 1), "dataType", "integer"),
        ((*TABLE, "vizDataColumns", 1), "paneIndices", [1]),
        ((*TABLE, "vizDataColumns", 1), "columnIndices", []),
        ((*TABLE, "vizDataColumns", 1), "columnIndices", [999]),
        ((*TABLE, "vizDataColumns", 1), "columnIndices", [0]),
        ((*TABLE, "paneColumnsList", 0, "vizPaneColumns", 1), "valueIndices", []),
        ((*TABLE, "paneColumnsList", 0, "vizPaneColumns", 1), "aliasIndices", []),
    ],
)
def test_actual_view_structure_corruption_is_refused(
    reader: ModuleType,
    path: tuple[str | int, ...],
    key: str,
    value: object,
) -> None:
    """Refuse corrupted real dictionary, pane, tuple and column bindings in the full capture."""
    frames = captured_frames()
    target = node(frames[1], path)
    assert isinstance(target, dict)
    target[key] = value
    with pytest.raises(reader.DashboardRefused):
        reader.parse_dashboard(framed(frames))


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        ("value", -1),
        ("value", 999999),
        ("alias", 999999),
        ("alias", -999999),
        ("empty", ""),
        ("multiline", "invalid\tfield"),
        ("latitude", 91.0),
        ("longitude", -181.0),
        ("identity", "Country"),
        ("map_disagreement", "Status"),
        ("duplicate_identity", "Facility Name"),
    ],
)
def test_actual_source_cell_corruption_is_refused(
    reader: ModuleType, kind: str, value: object
) -> None:
    """Reject invalid source indices, coordinates, identities and disagreements between views."""
    frames = captured_frames()
    columns = cast(list[dict[str, object]], node(frames[1], (*DICTIONARY, "dataColumns")))
    dictionaries = {
        str(column["dataType"]): cast(list[object], column["dataValues"]) for column in columns
    }
    pane = cast(dict[str, object], node(frames[1], TABLE))
    data = cast(list[dict[str, object]], node(pane, ("paneColumnsList", 0, "vizPaneColumns")))
    if kind in {"value", "alias"}:
        indices = cast(list[object], data[1]["valueIndices" if kind == "value" else "aliasIndices"])
        indices[0] = value
    elif kind in {"empty", "multiline"}:
        position = cast(list[int], data[1]["valueIndices"])[0]
        dictionaries["cstring"][position] = value
    elif kind in {"latitude", "longitude"}:
        map_data = cast(
            list[dict[str, object]],
            node(frames[1], (*MAIN, "paneColumnsList", 0, "vizPaneColumns")),
        )
        col = 3 if kind == "latitude" else 5
        position = cast(list[int], map_data[col]["valueIndices"])[0]
        dictionaries["real"][position] = value
    elif kind in {"identity", "map_disagreement"}:
        metadata = cast(list[dict[str, object]], node(frames[1], (*MAIN, "vizDataColumns")))
        map_data = cast(
            list[dict[str, object]],
            node(frames[1], (*MAIN, "paneColumnsList", 0, "vizPaneColumns")),
        )
        meta = next(meta for meta in metadata[1:] if meta["fieldCaption"] == value)
        column = map_data[cast(list[int], meta["columnIndices"])[0]]
        positions = cast(list[object], column["valueIndices"])
        positions[0] = next(index for index in positions if index != positions[0])
    else:
        for column in data[1:]:
            positions = cast(list[object], column["valueIndices"])
            positions[1] = positions[0]
    with pytest.raises(reader.DashboardRefused):
        reader.parse_dashboard(framed(frames))


def test_missing_capture_and_changed_digest_refuse(reader: ModuleType, tmp_path: Path) -> None:
    """Refuse an unreadable capture and a source whose digest differs from its registered pin."""
    with pytest.raises(reader.DashboardRefused, match="cannot be read"):
        reader.read_dashboard(tmp_path / "missing.raw")
    with pytest.raises(reader.DashboardRefused, match="registered SHA-256"):
        reader.read_dashboard(CAPTURE, "0" * 64)


def test_complete_reframing_uses_characters_not_utf8_byte_lengths(reader: ModuleType) -> None:
    """Preserve the complete table and map when Unicode character counts frame a UTF-8 payload."""
    frames = captured_frames()
    original = reader.read_dashboard(CAPTURE)
    reproduced = reader.parse_dashboard(framed(frames))
    assert reproduced.table == original.table
    assert reproduced.map_points == original.map_points


def test_incomplete_visible_field_set_is_refused(reader: ModuleType) -> None:
    """Reject a capture with a consistently removed visible column instead of accepting a subset."""
    frames = captured_frames()
    metadata = cast(list[object], node(frames[1], (*TABLE, "vizDataColumns")))
    metadata.pop()
    columns = cast(list[object], node(frames[1], (*TABLE, "paneColumnsList", 0, "vizPaneColumns")))
    columns.pop()
    with pytest.raises(reader.DashboardRefused, match="complete visible field set"):
        reader.parse_dashboard(framed(frames))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", 2),
        ("kind", "unqualified-container"),
        ("source_url", "https://example.org/private"),
        ("original_response_sha256", "invalid"),
        ("retrieved_date", "2026-02-30"),
        ("retrieved_date", "20261002"),
        ("unexpected_member", "unexpected"),
    ],
)
def test_selection_header_corruption_refuses(reader: ModuleType, field: str, value: object) -> None:
    """Reject invalid projection versions, source identity, acquisition dates and extra metadata."""
    frames = captured_frames()
    header = cast(dict[str, object], frames[0]["atlas_projection"])
    header[field] = value
    with pytest.raises(reader.DashboardRefused):
        reader.parse_dashboard(framed(frames))


def test_selection_cannot_mix_authored_header_and_publisher_renderer(reader: ModuleType) -> None:
    """Refuse a frame mixing authored projection metadata with an unrelated renderer member."""
    frames = captured_frames()
    frames[0]["renderer_metadata"] = {}
    with pytest.raises(reader.DashboardRefused, match="member set"):
        reader.parse_dashboard(framed(frames))


def test_registered_artifact_and_original_response_digests_remain_separate(
    reader: ModuleType,
) -> None:
    """Keep the selected artifact's digest, original response pin and acquisition date distinct."""
    dashboard = reader.read_dashboard(CAPTURE)
    assert dashboard.source_sha256 == hashlib.sha256(CAPTURE.read_bytes()).hexdigest()
    assert (
        dashboard.original_response_sha256
        == "a87305137acebaaa3acf4dee2992324061c9d0e3eed433f1abe3cf49e1f9d037"
    )
    assert dashboard.source_kind == reader.PROJECTION_KIND
    assert dashboard.retrieved_date == "2026-10-02"
