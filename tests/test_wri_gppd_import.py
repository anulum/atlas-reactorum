# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — WRI import conformance

"""Rebuild all published WRI nuclear rows from preserved upstream source cells."""

from __future__ import annotations

import csv
import functools
import hashlib
import json
import threading
from collections.abc import Iterator
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, run_cli
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map"
SCRIPT = DIRECTORY / "scripts/fetch_wri_gppd.py"
SOURCE = ROOT / "tests/data/wri_gppd/nuclear_and_filter_control.csv"
PUBLISHED = DIRECTORY / "data/reactors.tsv"


@pytest.fixture
def wri_http(tmp_path: Path) -> Iterator[str]:
    """Serve the actual licensed WRI source selection over loopback HTTP."""
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


@pytest.mark.parametrize("transport", ["file", "http"])
def test_original_wri_cells_reproduce_complete_published_layer(
    tmp_path: Path, wri_http: str, transport: str
) -> None:
    """Both real transports preserve all 195 nuclear rows and exclude the fuel control."""
    metadata = json.loads((SOURCE.parent / "SOURCE.json").read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == metadata["fixture_sha256"]
    destination = tmp_path / "reproduced.tsv"
    option, value = ("--source", str(SOURCE)) if transport == "file" else ("--source-url", wri_http)
    result = run_cli(SCRIPT, option, value, "--out", str(destination), "--date", "2026-09-26")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "195 nuclear plants" in result.stdout
    assert destination.read_bytes() == PUBLISHED.read_bytes()


@pytest.mark.parametrize(
    "corruption",
    [
        "unknown_country",
        "empty_id",
        "duplicate_id",
        "missing_header",
        "truncated_row",
        "extra_cell",
        "no_nuclear",
        "invalid_utf8",
        "unterminated_quote",
    ],
)
def test_corrupt_wri_source_refuses_without_overwriting(tmp_path: Path, corruption: str) -> None:
    """Unusable GPPD records cannot overwrite a valid previous nuclear layer."""
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields, rows = list(reader.fieldnames or []), list(reader)
    if corruption == "unknown_country":
        rows[0]["country"] = "ZZZ"
    elif corruption == "empty_id":
        rows[0]["gppd_idnr"] = ""
    elif corruption == "duplicate_id":
        rows.append(rows[0].copy())
    elif corruption == "missing_header":
        fields.remove("country")
        for row in rows:
            row.pop("country")
    elif corruption == "no_nuclear":
        rows = [row for row in rows if row["primary_fuel"] != "Nuclear"]
    source = tmp_path / SOURCE.name
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    if corruption in {"truncated_row", "extra_cell"}:
        lines = source.read_text().splitlines()
        lines[1] = lines[1].split(",")[0] if corruption == "truncated_row" else lines[1] + ",extra"
        source.write_text("\n".join(lines) + "\n")
    elif corruption == "invalid_utf8":
        source.write_bytes(source.read_bytes() + b"\xff")
    elif corruption == "unterminated_quote":
        source.write_text(",".join(fields) + '\n"unterminated')
    destination = tmp_path / "reactors.tsv"
    destination.write_bytes(PUBLISHED.read_bytes())
    result = run_cli(SCRIPT, "--source", str(source), "--out", str(destination), optimize=True)
    assert result.returncode == 1 and "Traceback" not in result.stderr
    assert destination.read_bytes() == PUBLISHED.read_bytes()


@pytest.mark.parametrize("failure", ["missing_file", "http_404", "unsupported_scheme"])
def test_wri_transport_failures_are_controlled(tmp_path: Path, wri_http: str, failure: str) -> None:
    """Real I/O failures refuse before opening the destination."""
    option = "--source" if failure == "missing_file" else "--source-url"
    value = (
        str(tmp_path / "missing.csv")
        if failure == "missing_file"
        else wri_http + ".missing"
        if failure == "http_404"
        else "file:///unsupported.csv"
    )
    destination = tmp_path / "reactors.tsv"
    result = run_cli(SCRIPT, option, value, "--out", str(destination))
    assert result.returncode == 1 and "cannot read GPPD source" in result.stderr
    assert "Traceback" not in result.stderr
    assert not destination.exists()


def test_wri_timeout_and_public_import_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Timeout validation and the public importer use the same source contract."""
    destination = tmp_path / "reactors.tsv"
    for timeout in ("0", "nan"):
        result = run_cli(
            SCRIPT, "--source", str(SOURCE), "--out", str(destination), "--timeout", timeout
        )
        assert result.returncode == 2 and "positive and finite" in result.stderr
    monkeypatch.syspath_prepend(str(SCRIPT.parent))
    monkeypatch.setattr(
        "sys.argv",
        [str(SCRIPT), "--source", str(SOURCE), "--out", str(destination), "--date", "2026-09-26"],
    )
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_wri_import")
    module.main()
    assert destination.read_bytes() == PUBLISHED.read_bytes()
