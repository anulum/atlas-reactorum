# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — FFDB framing source tests

"""Exercise the frame codec on the complete registered visible-data selection."""

from __future__ import annotations

import importlib
from typing import cast

import pytest

from .test_ffdb_reader import CAPTURE, captured_frames


def test_real_selection_round_trip_retains_character_lengths_and_all_members() -> None:
    framing = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.framing")
    frames = framing.decode_frames(CAPTURE.read_bytes())
    assert framing.encode_frames(frames) == CAPTURE.read_bytes()
    assert frames == captured_frames()


@pytest.mark.parametrize("invalid", [float("inf"), object()])
def test_source_member_that_cannot_be_finite_json_is_refused(invalid: object) -> None:
    framing = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.framing")
    frames = framing.decode_frames(CAPTURE.read_bytes())
    projection = cast(dict[str, object], frames[0]["atlas_projection"])
    projection["retrieved_date"] = invalid
    with pytest.raises(framing.DashboardRefused, match="finite JSON"):
        framing.encode_frames(frames)


def test_integer_decoder_limit_is_an_authored_public_refusal() -> None:
    framing = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.framing")
    first = '{"oversized_integer":' + "1" * 5000 + "}"
    payload = f"{len(first)};{first}2;{{}}".encode()
    with pytest.raises(framing.DashboardRefused, match="invalid JSON"):
        framing.decode_frames(payload)


@pytest.mark.parametrize("surrogate", ["\ud800", "\udfff"])
def test_unrepresentable_utf8_source_value_is_an_authored_public_refusal(
    surrogate: str,
) -> None:
    framing = importlib.import_module("05_global_reactor_map.imports.fusion.ffdb.framing")
    with pytest.raises(framing.DashboardRefused, match="valid UTF-8"):
        framing.encode_frames([{"value": surrogate}, {}])
