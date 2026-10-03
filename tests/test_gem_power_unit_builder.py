# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — GEM power-unit builder conformance

"""Rebuild the real GEM snapshot through file and HTTP entry points."""

from __future__ import annotations

import functools
import hashlib
import json
import threading
from collections.abc import Iterator
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map/imports/power_units"
SOURCE = DIRECTORY / "source_data/gnpt_map_2026-08.geojson"
PUBLISHED = DIRECTORY / "power_reactor_units.tsv"
SCRIPT = DIRECTORY / "scripts/build_from_gem.py"


@pytest.fixture
def snapshot_http(tmp_path: Path) -> Iterator[str]:
    """Serve the unchanged licensed snapshot through a real loopback HTTP server."""
    (tmp_path / SOURCE.name).write_bytes(SOURCE.read_bytes())
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/{SOURCE.name}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("transport", ["file", "http"])
def test_frozen_gem_snapshot_reproduces_published_units(
    tmp_path: Path, snapshot_http: str, transport: str
) -> None:
    """Both actual transports preserve the full checked-in TSV byte for byte."""
    destination = tmp_path / "rebuilt.tsv"
    option, value = (
        ("--source", str(SOURCE)) if transport == "file" else ("--source-url", snapshot_http)
    )
    result = run_cli(SCRIPT, option, value, "--out", str(destination), "--date", "2026-09-27")
    assert result.returncode == 0, result.stdout + result.stderr
    assert destination.read_bytes() == PUBLISHED.read_bytes()
    assert "1823 fission/unknown-type" in result.stdout
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() in result.stdout


def test_changed_gem_bytes_require_explicit_review(tmp_path: Path) -> None:
    """A checksum change cannot silently overwrite a previously built output."""
    source = tmp_path / SOURCE.name
    source.write_bytes(SOURCE.read_bytes() + b"\n")
    destination = tmp_path / "units.tsv"
    destination.write_bytes(PUBLISHED.read_bytes())
    result = run_cli(SCRIPT, "--source", str(source), "--out", str(destination))
    assert result.returncode == 1 and "source SHA-256 changed" in result.stderr
    assert destination.read_bytes() == PUBLISHED.read_bytes()
    accepted = run_cli(
        SCRIPT,
        "--source",
        str(source),
        "--out",
        str(destination),
        "--date",
        "2026-09-27",
        "--allow-changed-source",
    )
    assert accepted.returncode == 0
    assert destination.read_bytes() == PUBLISHED.read_bytes()


@pytest.mark.parametrize(
    ("corruption", "diagnostic"),
    [
        ("invalid_json", "invalid source JSON"),
        ("invalid_utf8", "invalid source JSON"),
        ("root_array", "GeoJSON FeatureCollection"),
        ("wrong_type", "GeoJSON FeatureCollection"),
        ("features_object", "GeoJSON FeatureCollection"),
        ("feature_array", "object properties"),
        ("properties_array", "object properties"),
        ("missing_unit_id", "lacks unit-id"),
        ("nonfinite_capacity", "must be finite"),
        ("invalid_latitude", "invalid source number"),
        ("empty_features", "no fission or unknown-type units"),
    ],
)
def test_corrupt_gem_source_refuses_without_overwriting_output(
    tmp_path: Path, corruption: str, diagnostic: str
) -> None:
    """Reviewed changed bytes must still satisfy the actual builder's input contract."""
    data = json.loads(SOURCE.read_bytes())
    if corruption == "root_array":
        data = []
    elif corruption == "wrong_type":
        data["type"] = "Point"
    elif corruption == "features_object":
        data["features"] = {}
    elif corruption == "feature_array":
        data["features"][0] = []
    elif corruption == "properties_array":
        data["features"][0]["properties"] = []
    elif corruption == "missing_unit_id":
        data["features"][0]["properties"].pop("unit-id")
    elif corruption == "nonfinite_capacity":
        data["features"][0]["properties"]["capacity"] = "NaN"
    elif corruption == "invalid_latitude":
        data["features"][0]["properties"]["Latitude"] = "unknown"
    elif corruption == "empty_features":
        data["features"] = []
    source = tmp_path / SOURCE.name
    source.write_bytes(
        b"{"
        if corruption == "invalid_json"
        else b"\xff"
        if corruption == "invalid_utf8"
        else json.dumps(data).encode()
    )
    destination = tmp_path / "units.tsv"
    destination.write_bytes(PUBLISHED.read_bytes())
    result = run_cli(
        SCRIPT,
        "--source",
        str(source),
        "--out",
        str(destination),
        "--allow-changed-source",
        optimize=True,
    )
    assert result.returncode == 1
    assert diagnostic in result.stderr
    assert "Traceback" not in result.stderr
    assert destination.read_bytes() == PUBLISHED.read_bytes()


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf"])
def test_gem_transport_timeout_must_be_bounded(tmp_path: Path, timeout: str) -> None:
    """Invalid timeouts fail before any source or destination is opened."""
    destination = tmp_path / "units.tsv"
    result = run_cli(
        SCRIPT, "--source", str(SOURCE), "--out", str(destination), "--timeout", timeout
    )
    assert result.returncode == 2 and "positive and finite" in result.stderr
    assert not destination.exists()


@pytest.mark.parametrize("failure", ["missing_file", "http_404", "unsupported_scheme"])
def test_gem_source_transport_errors_refuse(
    tmp_path: Path, snapshot_http: str, failure: str
) -> None:
    """Actual file, HTTP-status and URL-adapter failures cannot become a build."""
    option = "--source" if failure == "missing_file" else "--source-url"
    value = (
        str(tmp_path / "missing.json")
        if failure == "missing_file"
        else snapshot_http + ".missing"
        if failure == "http_404"
        else "file:///unsupported.json"
    )
    destination = tmp_path / "units.tsv"
    result = run_cli(SCRIPT, option, value, "--out", str(destination))
    assert result.returncode == 1 and "cannot read source" in result.stderr
    assert "Traceback" not in result.stderr
    assert not destination.exists()


def test_gem_public_field_normalization_preserves_unknowns() -> None:
    """Source-value normalization keeps absent values distinct from zero."""
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_gem_builder")
    assert module.text(None) == module.text("Unknown") == ""
    assert module.text("  Nuclear  ") == "Nuclear"
    assert module.number(None) == module.number("") == ""
    assert module.number(0) == "0"
    _, rows = read_table(PUBLISHED)
    assert module.number(rows[0]["nameplate_mw"]) == rows[0]["nameplate_mw"]
    with pytest.raises(ValueError, match="must be finite"):
        module.number("NaN")
