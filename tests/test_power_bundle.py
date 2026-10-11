# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — whole power documentary bundle conformance
"""Exercise the complete original power-unit cohort through its actual public APIs."""

from __future__ import annotations

import hashlib
import importlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "05_global_reactor_map/imports/power_units/official_source_enrichment"
SOURCE = DIRECTORY.parent / "power_reactor_units.tsv"
BUNDLE = importlib.import_module(
    "05_global_reactor_map.imports.power_units.official_source_enrichment.power_bundle"
)


def build_power_product(root: Path) -> None:
    """Execute the owning producer API for a complete fresh release source copy."""
    cli = importlib.import_module(
        "05_global_reactor_map.imports.power_units.official_source_enrichment.build_power_projection"
    )
    source = root / SOURCE.relative_to(ROOT)
    directory = root / DIRECTORY.relative_to(ROOT)
    assert cli.main([str(source), str(directory)]) == 0


def test_whole_bundle_preserves_original_cells_and_complete_decisions() -> None:
    """Reconstruct every original row and qualify exactly the source-bound blank fills.

    This checks the real complete bundle, rather than a software fixture claiming
    to confer scientific approval. Independent acceptance remains explicitly null.
    """
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    original = BUNDLE.read_source(SOURCE)
    projection = BUNDLE.load_projection(SOURCE, DIRECTORY)
    assert projection is not None
    assert len(original) == len(projection.rows) == 1823
    assert len(projection.decisions) == 930
    assert Counter(row["disposition"] for row in projection.decisions) == {
        "qualified": 54,
        "held": 35,
        "unknown": 841,
    }
    selected = {
        (row["stable_id"], row["field"]): row["value"]
        for row in projection.decisions
        if row["disposition"] == "qualified"
    }
    changed = set()
    for old, new in zip(original, projection.rows, strict=True):
        assert list(new) == list(old)
        for field, value in old.items():
            key = (old["stable_id"], field)
            if key in selected:
                assert not value and new[field] == selected[key]
                changed.add(key)
            else:
                assert new[field] == value
    assert changed == set(selected)
    assert all(row["independent_review"] is None for row in projection.decisions)
    expected = json.loads((DIRECTORY / "primary-projection.json").read_text())
    reconstructed, document = BUNDLE.produce(SOURCE, DIRECTORY)
    assert document == expected
    assert reconstructed == projection
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before
