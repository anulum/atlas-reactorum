# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — reviewed primary projection consumer
"""Bind published research decisions to their original rows and producer inputs."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_projection import read_baseline
from projection import FieldProjection, project_fields, read_assertions

MEMBERS = ("primary-baseline.json", "primary-fields.tsv", "primary-projection.json")


def load_projection(
    baseline: Mapping[str, Mapping[str, str]], directory: Path
) -> FieldProjection | None:
    """Accept a complete reproducible bundle or retain an unmodified historical build.

    Parameters
    ----------
    baseline : mapping of str to mapping of str to str
        Every original row after merging the existing research source rounds.
    directory : pathlib.Path
        Source directory containing all three members in ``MEMBERS``. An absent
        bundle is allowed for historical builds; partial bundles are refused.

    Returns
    -------
    FieldProjection or None
        Independently reconstructed rows and all field decisions, or no overlay.

    Raises
    ------
    ValueError
        The bundle is incomplete, aliased, changed, unreviewed or inconsistent
        with its producer inputs or the actual original source rows.
    OSError
        An existing bundle member cannot be read.
    """
    paths = [directory / name for name in MEMBERS]
    present = [path.exists() or path.is_symlink() for path in paths]
    if not any(present):
        return None
    if not all(present) or any(
        not path.is_file() or any(part.is_symlink() for part in (path, *path.parents))
        for path in paths
    ):
        raise ValueError("complete original primary research bundle required")
    original = read_baseline(paths[0])
    if original != baseline:
        raise ValueError("primary research baseline differs from original merged sources")
    result = project_fields(original, read_assertions(paths[1]))
    expected = {
        "schema_version": "1.0.0",
        "baseline_sha256": hashlib.sha256(paths[0].read_bytes()).hexdigest(),
        "ledger_sha256": hashlib.sha256(paths[1].read_bytes()).hexdigest(),
        "record_count": len(result.rows),
        "selected_fields": sum(row["selection"] == "selected" for row in result.assertions),
        "rows": list(result.rows.values()),
        "assertions": list(result.assertions),
    }
    document: object = json.loads(paths[2].read_bytes())
    if (
        not isinstance(document, dict)
        or any(type(document.get(key)) is not int for key in ("record_count", "selected_fields"))
        or document != expected
    ):
        raise ValueError("primary research projection differs from its complete producer inputs")
    return result
