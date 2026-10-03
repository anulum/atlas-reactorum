# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — frozen facility-field release consumer

"""Bind reviewed frozen assertions to unchanged target layers without research fixtures."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import MutableMapping, Sequence
from pathlib import Path

from .inputs import bound_bytes, mapping, original_rows, source_path, text

MEMBERS = (
    "metadata/facility_fields/observations.json",
    "metadata/facility_fields/observations.sha256",
    "metadata/facility_fields/source_pins.json",
)


def apply_fields(root: Path, facilities: Sequence[MutableMapping[str, object]]) -> int:
    """Apply a complete frozen projection to the available unchanged source layers.

    Parameters
    ----------
    root : pathlib.Path
        Release checkout containing the frozen projection and target tables.
        The original preparation fixtures are not required at runtime.
    facilities : sequence of mutable mappings
        Actual assembled records, amended only after all bindings validate.

    Returns
    -------
    int
        Assertions applied to present target layers. A wholly absent projection
        or wholly absent optional target layer contributes no assertions.

    Raises
    ------
    ValueError
        A projection member, digest, source meaning or target identity differs,
        or a new scalar assertion would replace an existing original value.
    KeyError
        A required assertion member or target identity is absent.
    OSError
        A complete frozen member or present target table cannot be read.
    """
    if not any((root / member).exists() or (root / member).is_symlink() for member in MEMBERS):
        return 0
    pins_body = source_path(root, MEMBERS[2]).read_bytes()
    pins = mapping(json.loads(pins_body))
    sources = {
        text(mapping(value)["path"]): mapping(value) for value in mapping(pins["sources"]).values()
    }
    targets = {
        text(mapping(value)["path"]): mapping(value)
        for value in mapping(pins["target_datasets"]).values()
    }
    if (
        type(pins["schema_version"]) is not int
        or pins["schema_version"] != 1
        or len(sources) != 10
        or len(targets) != 4
    ):
        raise ValueError("complete reviewed source pin scope required")
    checksum = source_path(root, MEMBERS[1]).read_text().strip()
    body = bound_bytes(root, MEMBERS[0], checksum)
    document = mapping(json.loads(body))
    rows = original_rows(document["records"])
    if (
        document["schema_version"] != "1.0.0"
        or document["source_pins_sha256"] != hashlib.sha256(pins_body).hexdigest()
        or type(document["record_count"]) is not int
        or document["record_count"] != 1631
        or len(rows) != 1631
        or Counter(row["field"] for row in rows) != {"purpose": 1092, "fuel_or_feed": 539}
    ):
        raise ValueError("complete reviewed frozen projection required")
    active: set[str] = set()
    for relative, metadata in targets.items():
        target_path = root / relative
        if target_path.exists() or target_path.is_symlink():
            bound_bytes(root, relative, text(metadata["sha256"]))
            active.add(relative)
    by_id = {text(row.get("stable_id", row["id"])): row for row in facilities}
    planned: dict[str, list[dict[str, object]]] = {}
    keys: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if len(row) != 13:
            raise ValueError("complete source assertion shape required")
        source, target = text(row["source_artifact"]), text(row["target_dataset"])
        if (
            row["source_sha256"] != sources[source]["sha256"]
            or row["target_sha256"] != targets[target]["sha256"]
        ):
            raise ValueError("frozen source or target binding differs")
        field = text(row["field"])
        basis = text(row["basis"])
        if (field == "purpose" and basis != "published-end-use") or (
            field == "fuel_or_feed"
            and basis
            not in {
                "published-feedstock",
                "fuel-classification",
                "primary-fuel-classification",
                "secondary-fuel-classification",
            }
        ):
            raise ValueError("source field meaning differs")
        for value in row.values():
            text(value)
        key = (text(row["target_id"]), field, source, text(row["source_field"]))
        if key in keys:
            raise ValueError("duplicate frozen source assertion")
        keys.add(key)
        if target in active:
            facility = by_id[key[0]]
            if facility["dataset_source"] != target:
                raise ValueError("source assertion targets a different dataset")
            planned.setdefault(key[0], []).append(row)
    values: dict[str, dict[str, str]] = {}
    for identity, observations in planned.items():
        grouped: dict[str, list[str]] = {}
        for observation in observations:
            grouped.setdefault(text(observation["field"]), []).append(text(observation["value"]))
        values[identity] = {
            field: "; ".join(dict.fromkeys(cells)) for field, cells in grouped.items()
        }
        for field, value in values[identity].items():
            if by_id[identity].get(field) not in (None, "", value):
                raise ValueError("existing original field would be replaced")
    for identity, observations in planned.items():
        by_id[identity]["field_observations"] = observations
        by_id[identity].update(values[identity])
    return sum(len(observations) for observations in planned.values())
