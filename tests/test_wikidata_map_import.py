# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — Wikidata map import conformance

"""Exercise real Wikidata bindings, transport and bounded status interpretation."""

from __future__ import annotations

import functools
import json
import threading
from collections.abc import Iterator
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli
from .conftest import load_module

SCRIPT = ROOT / "05_global_reactor_map/scripts/fetch_wikidata.py"
SOURCE = ROOT / "tests/data/wikidata/bindings.json"


@pytest.fixture
def wikidata_http(tmp_path: Path) -> Iterator[str]:
    """Serve the unchanged primary response over a real snapshot-mirror transport."""
    (tmp_path / SOURCE.name).write_bytes(SOURCE.read_bytes())
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(SimpleHTTPRequestHandler, directory=str(tmp_path))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/{SOURCE.name}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize(
    ("label", "dissolved", "expected"),
    [
        ("in use", "", "operational"),
        ("active", "", "operational"),
        ("operating", "", "operational"),
        ("in partial operation", "", "operational"),
        ("building or structure under construction", "", "under_construction"),
        ("proposed building or structure", "", "planned"),
        ("planned", "", "planned"),
        ("suspended", "", "suspended"),
        ("decommissioned", "", "decommissioned"),
        ("retired", "", "decommissioned"),
        ("nuclear decommissioning", "", "decommissioning"),
        ("permanently closed", "", "shutdown"),
        ("shutdown", "", "shutdown"),
        ("cancelled", "", "cancelled"),
        ("", "2020-01-01", "shutdown"),
        ("", "", "unknown"),
        ("inactive", "", "unknown"),
        ("not operational", "", "unknown"),
        ("postponed", "", "unknown"),
    ],
)
def test_wikidata_public_status_interpretation(label: str, dissolved: str, expected: str) -> None:
    """Known source labels map explicitly; negative or ambiguous labels never imply operation."""
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_wikidata_status")
    assert module.norm_status(label, dissolved) == expected


@pytest.mark.parametrize("transport", ["file", "http"])
def test_primary_wikidata_binding_snapshot_import(
    tmp_path: Path, wikidata_http: str, transport: str
) -> None:
    """Source replay and HTTP replay produce the same uniquely identified discovery layer."""
    destination = tmp_path / "wikidata.tsv"
    option, value = (
        ("--source", str(SOURCE)) if transport == "file" else ("--endpoint", wikidata_http)
    )
    result = run_cli(SCRIPT, option, value, "--out", str(destination), "--date", "2026-09-29")
    assert result.returncode == 0, result.stdout + result.stderr
    _, rows = read_table(destination)
    assert rows and len({row["id"] for row in rows}) == len(rows)
    original = json.loads(SOURCE.read_bytes())["results"]["bindings"]
    supplied = {binding["item"]["value"] for binding in original}
    assert all(row["source_url"] in supplied for row in rows)
    assert all(row["source_license"] == "CC0 1.0" for row in rows)
    assert all(row["last_verified"] == "2026-09-29" for row in rows)
    in_use = {
        binding["item"]["value"]
        for binding in original
        if binding.get("statusLabel", {}).get("value") == "in use"
    }
    assert all(row["status"] == "operational" for row in rows if row["source_url"] in in_use)
    second = tmp_path / "offline.tsv"
    offline = run_cli(
        SCRIPT, "--source", str(SOURCE), "--out", str(second), "--date", "2026-09-29", optimize=True
    )
    assert offline.returncode == 0 and second.read_bytes() == destination.read_bytes()


@pytest.mark.parametrize(
    "corruption",
    [
        "bad_json",
        "root_array",
        "missing_results",
        "bindings_object",
        "binding_array",
        "value_array",
        "unknown_class",
    ],
)
def test_invalid_wikidata_response_refuses(tmp_path: Path, corruption: str) -> None:
    """Malformed API data and unexpected classifications are controlled refusals."""
    data = json.loads(SOURCE.read_bytes())
    if corruption == "root_array":
        data = []
    elif corruption == "missing_results":
        data.pop("results")
    elif corruption == "bindings_object":
        data["results"]["bindings"] = {}
    elif corruption == "binding_array":
        data["results"]["bindings"][0] = []
    elif corruption == "value_array":
        data["results"]["bindings"][0]["coord"] = []
    elif corruption == "unknown_class":
        data["results"]["bindings"][0]["class"]["value"] = "http://www.wikidata.org/entity/Q0"
    source = tmp_path / "changed.json"
    source.write_bytes(b"{" if corruption == "bad_json" else json.dumps(data).encode())
    destination = tmp_path / "wikidata.tsv"
    result = run_cli(SCRIPT, "--source", str(source), "--out", str(destination))
    assert result.returncode == 1 and "Traceback" not in result.stderr
    assert not destination.exists()


@pytest.mark.parametrize(
    "corruption",
    [
        "coordinate_syntax",
        "coordinate_decimal",
        "coordinate_range",
        "country_code",
        "duplicate_binding",
    ],
)
def test_wikidata_unmappable_bindings_and_duplicate_types(tmp_path: Path, corruption: str) -> None:
    """Bad positions are excluded and repeated facts do not duplicate type claims."""
    data = json.loads(SOURCE.read_bytes())
    binding = next(
        b
        for b in data["results"]["bindings"]
        if b.get("countryCode", {}).get("value") and len(b["countryCode"]["value"]) == 2
    )
    selected_id = "wikidata-" + binding["item"]["value"].rsplit("/", 1)[-1].lower()
    data["results"]["bindings"] = [binding]
    if corruption == "coordinate_syntax":
        binding["coord"]["value"] += " trailing-data"
    elif corruption == "coordinate_decimal":
        binding["coord"]["value"] = "Point(--1 20)"
    elif corruption == "coordinate_range":
        binding["coord"]["value"] = "Point(999 91)"
    elif corruption == "country_code":
        binding["countryCode"]["value"] = "12"
    else:
        data["results"]["bindings"].append(binding.copy())
    source = tmp_path / "changed.json"
    source.write_text(json.dumps(data))
    destination = tmp_path / "wikidata.tsv"
    result = run_cli(SCRIPT, "--source", str(source), "--out", str(destination))
    assert result.returncode == 0, result.stderr
    _, rows = read_table(destination)
    if corruption == "duplicate_binding":
        assert len(rows) == 1 and rows[0]["id"] == selected_id
        assert "|" not in rows[0]["reactor_type"]
    else:
        assert rows == []


def test_wikidata_real_transport_and_timeout_failures(tmp_path: Path, wikidata_http: str) -> None:
    """Actual missing-file and HTTP errors retain a controlled CLI contract."""
    destination = tmp_path / "wikidata.tsv"
    for option, value in (
        ("--source", str(tmp_path / "missing.json")),
        ("--endpoint", wikidata_http + ".missing"),
    ):
        result = run_cli(SCRIPT, option, value, "--out", str(destination))
        assert result.returncode == 1 and "Traceback" not in result.stderr
        assert not destination.exists()
    for timeout in ("0", "nan"):
        result = run_cli(
            SCRIPT, "--source", str(SOURCE), "--out", str(destination), "--timeout", timeout
        )
        assert result.returncode == 2


def test_wikidata_public_binding_and_date_apis() -> None:
    """Public field access preserves actual source values and explicit absence."""
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_wikidata_values")
    binding = json.loads(SOURCE.read_bytes())["results"]["bindings"][0]
    assert module.val(binding, "item") == binding["item"]["value"]
    assert module.val(binding, "unbound") == ""
    assert module.date("") == ""
    assert module.date("2020-01-01T00:00:00Z") == "2020-01-01"
