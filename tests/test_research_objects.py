# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete research consumer object admission.
"""Preserve full original research records while refusing invalid public container inputs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.research_objects import object_fields, object_rows

ROOT = Path(__file__).resolve().parents[1]


def test_complete_original_comparison_objects_retain_every_unknown_value() -> None:
    """Admit all complete original profiles/sources and preserve their nested identity and input bytes."""
    path = ROOT / "examples/research/pwr-bwr-comparison.json"
    original = path.read_bytes()
    wire: object = json.loads(original)
    comparison = object_fields(wire)
    profiles = object_rows(comparison["profiles"])
    sources = object_rows(comparison["sources"])
    assert len(profiles) == 2
    assert sources
    for profile in profiles:
        assert object_fields(profile) == profile
        assert object_fields(profile)["claims"] is profile["claims"]
        assert object_rows(profile["claims"]) == profile["claims"]
        assert object_rows(profile["parameters"]) == profile["parameters"]
    assert object_fields({}) == {}
    assert object_rows([]) == []
    assert comparison == wire
    assert path.read_bytes() == original


@pytest.mark.parametrize("value", [None, [], "object", 1, False])
def test_nonobject_public_inputs_refuse(value: object) -> None:
    """Refuse actual nonmapping values at the public field-reader boundary.

    Parameters
    ----------
    value : object
        Deliberately incompatible native input container.
    """
    with pytest.raises(ValueError, match="must be a mapping"):
        object_fields(value)


def test_nonstring_key_in_a_complete_profile_refuses_without_mutation() -> None:
    """Keep every original field while refusing an added non-JSON key on a complete profile."""
    wire: object = json.loads((ROOT / "examples/research/pwr-bwr-comparison.json").read_text())
    original = object_rows(object_fields(wire)["profiles"])[0]
    candidate: dict[object, object] = {key: value for key, value in original.items()}
    candidate[1] = "not a JSON field"
    before = dict(candidate)
    with pytest.raises(ValueError, match="keys must be strings"):
        object_fields(candidate)
    assert candidate == before
    assert original == object_rows(object_fields(wire)["profiles"])[0]


@pytest.mark.parametrize("value", [None, {}, "rows", 1, False])
def test_nonarray_public_inputs_refuse(value: object) -> None:
    """Refuse an incompatible native row container without inventing an empty result.

    Parameters
    ----------
    value : object
        Deliberately incompatible public collection input.
    """
    with pytest.raises(ValueError, match="must be an array"):
        object_rows(value)


def test_invalid_row_after_complete_original_rows_refuses_without_mutation() -> None:
    """Refuse a malformed successor row while retaining the complete original ordered profiles."""
    wire: object = json.loads((ROOT / "examples/research/pwr-bwr-comparison.json").read_text())
    original = object_rows(object_fields(wire)["profiles"])
    candidate: list[object] = [*original, None]
    before = candidate.copy()
    with pytest.raises(ValueError, match="must be a mapping"):
        object_rows(candidate)
    assert candidate == before
