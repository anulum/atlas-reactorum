# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — original boundary source and full release products.
"""Exercise the complete pinned geographic source through its real offline producer."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from metadata.map_basemap.build import SOURCE_SHA256, build

ROOT = Path(__file__).resolve().parents[1]


def test_complete_source_reproduces_both_products_and_preserves_every_line(tmp_path: Path) -> None:
    """Rebuild both products with the actual script and prove all original coordinates survive."""
    source = tmp_path / "metadata/map_basemap"
    source.mkdir(parents=True)
    data = tmp_path / "04_interactive_presentation/data"
    data.mkdir(parents=True)
    for name in ["build.py", "ne_50m_admin_0_boundary_lines_land.geojson"]:
        (source / name).write_bytes((ROOT / "metadata/map_basemap" / name).read_bytes())
    (data / "country-boundaries.json.license").write_bytes(
        (ROOT / "04_interactive_presentation/data/country-boundaries.json.license").read_bytes()
    )
    build(tmp_path)
    result = subprocess.run(
        [sys.executable, str(ROOT / "metadata/map_basemap/build.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for suffix in ["json", "js"]:
        name = f"country-boundaries.{suffix}"
        assert (data / name).read_bytes() == (
            ROOT / "04_interactive_presentation/data" / name
        ).read_bytes()
    original = json.loads((source / "ne_50m_admin_0_boundary_lines_land.geojson").read_text())
    packet = json.loads((data / "country-boundaries.json").read_text())
    assert packet["sha256"] == SOURCE_SHA256
    expected: list[dict[str, Any]] = []
    for feature in original["features"]:
        geometry = feature["geometry"]
        lines = (
            [geometry["coordinates"]]
            if geometry["type"] == "LineString"
            else geometry["coordinates"]
        )
        expected.extend(
            {"classification": feature["properties"]["FEATURECLA"], "points": line}
            for line in lines
        )
    assert packet["borders"] == expected
    assert len(original["features"]) == 390
    assert len(expected) == 393
    assert sum(len(line["points"]) for line in expected) == 19859
    (source / "ne_50m_admin_0_boundary_lines_land.geojson").write_text("{}")
    retained = (data / "country-boundaries.json").read_bytes()
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        build(tmp_path)
    assert (data / "country-boundaries.json").read_bytes() == retained
