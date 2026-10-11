# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — power-unit presentation provenance
"""Resolve source references into self-contained map-detail and export decisions."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from power_contract import mapping, sequence, text
from power_projection import PowerProjection


def presentation_decisions(projection: PowerProjection) -> dict[str, list[dict[str, object]]]:
    """Resolve documentary references while preserving source meaning and field roles.

    Parameters
    ----------
    projection : PowerProjection
        Whole source-bound projection already admitted by its owning consumer.

    Returns
    -------
    dict
        Original target identities mapped to self-contained decisions. Documentary
        citations carry their locators and dates; failed attempts remain separate.
        Nested source and observation mappings are copied before augmentation.
    """
    sources = {text(row, "source_id"): row for row in projection.sources}

    def citations(value: object) -> list[dict[str, object]]:
        """Copy original citations with the referenced source custody metadata."""
        return [
            {**mapping(item), **sources[text(mapping(item), "source_id")]}
            for item in sequence(value)
        ]

    result: dict[str, list[dict[str, object]]] = {}
    for decision in projection.decisions:
        observations: list[dict[str, object]] = []
        for item in sequence(decision["observations"]):
            observation = mapping(item)
            attempts = [
                dict(sources[str(identity)])
                for identity in sequence(observation["capture_attempts"])
            ]
            observations.append(
                {
                    **observation,
                    "citations": citations(observation["citations"]),
                    "capture_attempts": attempts,
                }
            )
        rendered = {
            **decision,
            "citations": citations(decision["citations"]),
            "observations": observations,
        }
        result.setdefault(text(decision, "stable_id"), []).append(rendered)
    return result
