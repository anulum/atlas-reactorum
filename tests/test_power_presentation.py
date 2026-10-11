# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — owning power facility producer conformance
"""Exercise documentary roles and source references through the actual facility builder."""

from __future__ import annotations

import importlib
from collections import Counter

from .test_power_bundle import BUNDLE, DIRECTORY, SOURCE

BUILDER = importlib.import_module("04_interactive_presentation.scripts.build_datasets")
PRESENTATION = importlib.import_module(
    "05_global_reactor_map.imports.power_units.official_source_enrichment.power_presentation"
)


def test_actual_power_builder_carries_whole_decisions_and_original_stages() -> None:
    """Carry all 930 decisions and citation meanings into the actual 1,823 facility rows."""
    original = BUNDLE.read_source(SOURCE)
    rows = BUILDER.build_power_unit_facilities(SOURCE)
    assert len(rows) == len(original) == 1823
    assert [row["stable_id"] for row in rows] == [row["stable_id"] for row in original]
    decisions = [decision for row in rows for decision in row.get("power_field_decisions", [])]
    assert len(decisions) == 930
    assert Counter(row["disposition"] for row in decisions) == {
        "qualified": 54,
        "held": 35,
        "unknown": 841,
    }
    for old, new in zip(original, rows, strict=True):
        assert new["source_status"] == old["status"]
        assert new["owner"] == old["owner"] and new["model"] == old["model"]
        for field in ("operator", "reactor_type"):
            if old[field]:
                assert new[field] == old[field]
        for decision in new.get("power_field_decisions", []):
            assert decision["stable_id"] == old["stable_id"]
            assert decision["original_context"]["status"] == old["status"]
            for citation in decision["citations"]:
                assert citation["eligible_for_selection"] is True
                assert citation["body_state"] == "qualified_document"
                assert citation["url"] in new["source_urls"]
                assert citation["http_status"] == 200
                assert len(citation["body_sha256"]) == 64
            for observation in decision["observations"]:
                for attempt in observation["capture_attempts"]:
                    assert attempt["body_state"] == "capture_attempt"
                    assert attempt["eligible_for_selection"] is False
    eielson = next(row for row in rows if row["stable_id"] == "gem-gnpt:g100001054849")
    decision = eielson["power_field_decisions"][0]
    assert eielson["operator"] == "Oklo Inc."
    assert decision["role"] == "explicit_intended_operator"
    assert "conditional" in decision["scope"]
    assert eielson["source_status"] == "pre-construction"
    projection = BUNDLE.load_projection(SOURCE, DIRECTORY)
    assert projection is not None
    before = [dict(row) for row in projection.decisions]
    rendered = PRESENTATION.presentation_decisions(projection)
    assert [dict(row) for row in projection.decisions] == before
    assert sum(map(len, rendered.values())) == 930
