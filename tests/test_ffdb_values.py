# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — FFDB typed values real source tests

"""Probe typed dictionary and path failures in copies of the actual publisher response."""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import cast

import pytest

from .test_ffdb_reader import DICTIONARY, TABLE, captured_frames, framed, node

LAYER = "05_global_reactor_map/imports/fusion/ffdb"


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        ("string", False),
        ("integer", True),
        ("integer", 1.5),
        ("real", True),
        ("real", "0.0"),
        ("real", float("inf")),
        ("dictionary_type", "unexpected"),
        ("duplicate_dictionary", "cstring"),
        ("object", []),
        ("array", {}),
        ("pane_boolean", False),
        ("tuple_boolean", True),
    ],
)
def test_real_reader_refuses_wrong_source_json_types(kind: str, value: object) -> None:
    reader: ModuleType = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.reader")
    frames = captured_frames()
    columns = cast(list[dict[str, object]], node(frames[1], (*DICTIONARY, "dataColumns")))
    if kind in {"string", "integer", "real"}:
        dtype = "cstring" if kind == "string" else kind
        column = next(column for column in columns if column["dataType"] == dtype)
        cast(list[object], column["dataValues"])[0] = value
    elif kind == "dictionary_type":
        columns[0]["dataType"] = value
    elif kind == "duplicate_dictionary":
        columns.append(columns[-1])
    elif kind in {"object", "array"}:
        target = cast(dict[str, object], node(frames[1], DICTIONARY))
        target["dataColumns"] = [value] if kind == "object" else value
    elif kind == "pane_boolean":
        target = cast(dict[str, object], node(frames[1], (*TABLE, "vizDataColumns", 1)))
        target["paneIndices"] = [value]
    else:
        target = cast(
            dict[str, object], node(frames[1], (*TABLE, "paneColumnsList", 0, "vizPaneColumns", 0))
        )
        cast(list[object], target["tupleIds"])[0] = value
    with pytest.raises(reader.DashboardRefused):
        reader.parse_dashboard(framed(frames))


def test_valid_json_numeric_overflow_is_refused_at_the_typed_dictionary() -> None:
    reader = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.reader")
    frames = captured_frames()
    columns = cast(list[dict[str, object]], node(frames[1], (*DICTIONARY, "dataColumns")))
    real = next(column for column in columns if column["dataType"] == "real")
    cast(list[object], real["dataValues"])[0] = float("inf")
    payload = framed(frames).replace(b"Infinity", b"1e400   ")
    with pytest.raises(reader.DashboardRefused, match="finite numeric value"):
        reader.parse_dashboard(payload)
