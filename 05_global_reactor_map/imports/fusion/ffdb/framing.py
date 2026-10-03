# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — FFDB Unicode response framing

"""Read and write character-length frames without interpreting rendering metadata."""

from __future__ import annotations

import json
import re

from .values import DashboardRefused, object_map

_FRAME = re.compile(r"([1-9][0-9]{0,8});")


def _unique_members(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DashboardRefused("FFDB source contains duplicate JSON members.")
        result[key] = value
    return result


def _refuse_constant(_value: str) -> object:
    raise DashboardRefused("FFDB source contains a nonfinite JSON constant.")


def decode_frames(payload: bytes) -> list[dict[str, object]]:
    """Decode exactly two JSON object frames with Unicode character lengths.

    Parameters
    ----------
    payload : bytes
        UTF-8 publisher response or explicitly labelled data selection.

    Returns
    -------
    list of dict
        Both complete frames, with duplicate members and constants refused.

    Raises
    ------
    DashboardRefused
        If encoding, JSON, framing or the complete frame count is invalid.
    """
    try:
        source = payload.decode("utf-8")
    except UnicodeDecodeError:
        raise DashboardRefused("FFDB source must be valid UTF-8.") from None
    decoder = json.JSONDecoder(object_pairs_hook=_unique_members, parse_constant=_refuse_constant)
    frames: list[dict[str, object]] = []
    offset = 0
    while offset < len(source):
        marker = _FRAME.match(source, offset)
        if marker is None:
            raise DashboardRefused("FFDB source has invalid character-length framing.")
        declared = int(marker[1])
        offset = marker.end()
        try:
            value, end = decoder.raw_decode(source, offset)
        except DashboardRefused:
            raise
        except ValueError:
            raise DashboardRefused("FFDB source contains invalid JSON.") from None
        if end - offset != declared:
            raise DashboardRefused("FFDB source has invalid character-length framing.")
        frames.append(object_map(value))
        offset = end
    if len(frames) != 2:
        raise DashboardRefused("FFDB source requires both complete response frames.")
    return frames


def encode_frames(frames: list[dict[str, object]]) -> bytes:
    """Encode an authored selection using the source's character convention.

    Parameters
    ----------
    frames : list of dict
        Explicit selection header and source-data frame. This function makes
        no claim that its output is an unmodified publisher response.

    Returns
    -------
    bytes
        Deterministic UTF-8 representation, with finite JSON values.

    Raises
    ------
    DashboardRefused
        If a member cannot be represented as finite JSON or valid UTF-8.
    """
    try:
        documents = [
            json.dumps(frame, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
            for frame in frames
        ]
    except (TypeError, ValueError):
        raise DashboardRefused("FFDB selection must contain finite JSON values.") from None
    try:
        return "".join(f"{len(document)};{document}" for document in documents).encode("utf-8")
    except UnicodeEncodeError:
        raise DashboardRefused("FFDB selection must be valid UTF-8.") from None
