# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — FFDB selection source tests

"""Check complete data selection, omission and immutable original-source linkage."""

from __future__ import annotations

import hashlib
import importlib
from typing import cast

import pytest

from .test_ffdb_reader import CAPTURE, SECONDARY, captured_frames, framed, node


def test_complete_selection_preserves_every_raw_display_cell_and_origin() -> None:
    selection = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.selection")
    reader = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.reader")
    before = reader.read_dashboard(CAPTURE)
    selected = selection.select_visible_data(CAPTURE.read_bytes(), "2026-10-02")
    after = reader.parse_dashboard(selected)
    assert selected == CAPTURE.read_bytes()
    assert after.table == before.table
    assert after.map_points == before.map_points
    assert after.original_response_sha256 == before.original_response_sha256
    assert after.source_sha256 == hashlib.sha256(selected).hexdigest()
    assert after.source_sha256 != after.original_response_sha256


def test_selection_omits_unrelated_container_members_without_changing_source_cells() -> None:
    selection = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.selection")
    frames = captured_frames()
    frames[1]["unrelated_renderer_member"] = {"accessToken": "deliberately invalid test value"}
    secondary = cast(dict[str, object], node(frames[1], SECONDARY))
    secondary["unrelated_rendering_configuration"] = {"script": "deliberately invalid test value"}
    assert selection.select_visible_data(framed(frames), "2026-10-02") == CAPTURE.read_bytes()


@pytest.mark.parametrize("retrieved", ["", "2026-02-30", "20261002", "2026-10-03"])
def test_selection_refuses_noncanonical_or_changed_acquisition_date(retrieved: str) -> None:
    selection = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.selection")
    with pytest.raises(selection.DashboardRefused):
        selection.select_visible_data(CAPTURE.read_bytes(), retrieved)


def test_unlabelled_frame_is_explicitly_distinguished_from_a_registered_projection() -> None:
    selection = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.selection")
    reader = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.reader")
    frames = captured_frames()
    frames[0] = {}
    unlabelled = framed(frames)
    before = reader.parse_dashboard(unlabelled)
    after = reader.parse_dashboard(selection.select_visible_data(unlabelled, "2026-10-02"))
    assert before.source_kind == "publisher-viewer-response"
    assert after.source_kind == reader.PROJECTION_KIND
    assert after.original_response_sha256 == hashlib.sha256(unlabelled).hexdigest()
    assert after.table == before.table
    assert after.map_points == before.map_points
