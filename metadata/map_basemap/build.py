# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — reproducible country-boundary browser data.
"""Build the complete pinned Natural Earth land-boundary layer without network access."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

SOURCE_SHA256 = "2faac4f6b34386f3d21b6e018cf151f241f00e5c936d44dd17d7d9bfb147fa48"
SOURCE_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/ca96624a56bd078437bca8184e78163e5039ad19/geojson/ne_50m_admin_0_boundary_lines_land.geojson"


def build(root: Path) -> None:
    """Emit both complete browser products from the byte-verified original source.

    Parameters
    ----------
    root : pathlib.Path
        Repository root containing the pinned original GeoJSON and product directory.

    Raises
    ------
    ValueError
        Original source bytes differ from the recorded SHA-256.
    OSError
        A source or product cannot be read or written.
    """
    raw = (root / "metadata/map_basemap/ne_50m_admin_0_boundary_lines_land.geojson").read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Natural Earth boundary source SHA-256 mismatch")
    source = json.loads(raw)
    borders = []
    for feature in source["features"]:
        geometry = feature["geometry"]
        lines = (
            [geometry["coordinates"]]
            if geometry["type"] == "LineString"
            else geometry["coordinates"]
        )
        for line in lines:
            borders.append({"classification": feature["properties"]["FEATURECLA"], "points": line})
    packet = {"source": SOURCE_URL, "version": "5.1.0", "sha256": SOURCE_SHA256, "borders": borders}
    text = json.dumps(packet, ensure_ascii=False, separators=(",", ":")) + "\n"
    data = root / "04_interactive_presentation/data"
    (data / "country-boundaries.json").write_text(text, encoding="utf-8")
    ownership = (data / "country-boundaries.json.license").read_text(encoding="utf-8").splitlines()
    javascript = (
        "\n".join("// " + line for line in ownership)
        + "\nglobalThis.ATLAS_COUNTRY_BOUNDARIES = "
        + text.rstrip()
        + ";\n"
    )
    (data / "country-boundaries.js").write_text(javascript, encoding="utf-8")


if __name__ == "__main__":
    build(Path(__file__).resolve().parents[2])
