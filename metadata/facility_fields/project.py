# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — facility fields complete reviewed projection

"""Assemble every explicit field assertion and check its original dataset identity."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .inputs import read_inputs, text
from .observations import FieldObservation
from .projectors import agstar, bioenergy, round7, wri


def project(root: Path) -> list[FieldObservation]:
    """Project all original end-use, feedstock and fuel-category observations.

    Parameters
    ----------
    root : pathlib.Path
        Complete original research checkout, never modified by this function.

    Returns
    -------
    list of FieldObservation
        All 1,631 original assertions in deterministic target/field/source order.
        Six secondary WRI classifications and three absent AgSTAR end-use cells
        retain their original scope. Classifications do not establish fuel cycles.

    Raises
    ------
    ValueError
        A source identity, target binding or complete projection differs.
    OSError
        Complete original source inputs are unavailable.
    """
    sources, targets = read_inputs(root)
    result = wri(sources["wri"], targets["wri"])
    for key, source in sources.items():
        if key.startswith("agstar-"):
            result.extend(agstar(source, targets["agstar"]))
    for key in ("br-epe-biomethane", "us-epa-lmop"):
        result.extend(
            bioenergy(sources[key], targets["industrial6"], sources["industrial6-snapshot"])
        )
    result.extend(round7(sources["industrial7"], targets["industrial7"]))
    ids = {
        target.path: {text(row[text(target.metadata["id_field"])]) for row in target.rows}
        for target in targets.values()
    }
    keys = [
        (row["target_id"], row["field"], row["source_artifact"], row["source_field"])
        for row in result
    ]
    if len(keys) != len(set(keys)) or any(
        row["target_id"] not in ids[row["target_dataset"]] for row in result
    ):
        raise ValueError("source assertion has a duplicate or unknown target identity")
    if Counter(row["field"] for row in result) != {"purpose": 1092, "fuel_or_feed": 539}:
        raise ValueError("complete reviewed explicit field projection required")
    return sorted(
        result,
        key=lambda row: (
            row["target_dataset"],
            row["target_id"],
            row["field"],
            row["source_field"],
        ),
    )
