# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — source-bound classification and attained development.

"""Bind overlapping facets and scoped development to entry-owned evidence."""

from __future__ import annotations

from typing import cast


class DimensionError(ValueError):
    """Refuse an unbound classification or unsupported attained-stage relationship."""


def _references(
    item: dict[str, object], claims: set[str], observations: dict[str, dict[str, object]]
) -> list[str]:
    """Check nonempty entry-owned references after whole-input schema admission."""
    claim_ids = cast(list[str], item["claim_ids"])
    observation_ids = cast(list[str], item["observation_ids"])
    if not claim_ids and not observation_ids:
        raise DimensionError("Author dimension has no supporting evidence.")
    if not set(claim_ids).issubset(claims) or not set(observation_ids).issubset(observations):
        raise DimensionError("Author dimension refers to another or absent entry evidence.")
    return observation_ids


def validate_dimensions(record: dict[str, object], claims: set[str]) -> None:
    """Admit independent classification axes and scoped attained-stage evidence.

    Parameters
    ----------
    record : dict of str to object
        Complete entry after owning schema and observation admission.
    claims : set of str
        Original claim identities belonging to this entry alone.

    Raises
    ------
    DimensionError
        A facet lacks entry-owned support, duplicates an axis/value pair,
        omits the primary role or claims an attained stage from a forecast.
    """
    observations = {
        cast(str, item["id"]): item
        for item in cast(list[dict[str, object]], record["observations"])
    }
    facets = cast(list[dict[str, object]], record["facets"])
    seen: set[tuple[str, str]] = set()
    for facet in facets:
        _references(facet, claims, observations)
        pair = cast(str, facet["axis"]), cast(str, facet["value"])
        if pair in seen:
            raise DimensionError("Author classification duplicates an axis and value.")
        seen.add(pair)
    if ("entity-role", cast(str, record["entity_category"])) not in seen:
        raise DimensionError("Author classification omits its declared primary role.")
    ids: set[str] = set()
    for item in cast(list[dict[str, object]], record["development_assessments"]):
        referenced = _references(item, claims, observations)
        identity = cast(str, item["id"])
        if identity in ids:
            raise DimensionError("Author development duplicates an assessment identity.")
        ids.add(identity)
        if not referenced or any(
            observations[ref]["temporal_role"] != "attained"
            or observations[ref]["topic"] != "maturity"
            for ref in referenced
        ):
            raise DimensionError("Attained development requires attained maturity observations.")
        if any(
            observations[ref]["evidence_object"] != item["evidence_object"] for ref in referenced
        ):
            raise DimensionError("Attained development differs from its source evidence object.")
        if item["evidence_object"] != "operation" and item["stage"] in {"pilot", "industrial"}:
            raise DimensionError("Pilot or industrial development requires operation evidence.")
