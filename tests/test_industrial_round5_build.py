# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — UK/French process-specific producer conformance

"""Build all accepted UK/French process records from original source cells and read-only snapshots."""

from __future__ import annotations

import csv
import io
import json
import math
import shutil
import ssl
import subprocess
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from urllib.error import HTTPError, URLError

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map/imports/industrial_facilities/expansion_round5"
SCRIPT = DIRECTORY / "build_dataset.py"
SNAPSHOT = DIRECTORY / "selected_source_snapshot.tsv"
DATA = DIRECTORY / "industrial_facilities_round5.tsv"
SOURCE = ROOT / "tests/data/industrial_round5/repd.csv"
ADEME = SOURCE.parent / "ademe.json"
METADATA = SOURCE.parent / "ademe-metadata.json"
REFERENCES = SOURCE.parent / "projection_reference.json"


@pytest.fixture
def producer() -> ModuleType:
    """Load the actual UK/French process producer in its own module namespace.

    Returns
    -------
    types.ModuleType
        Production projection, snapshot, build and HTTPS acquisition API.
    """
    return load_module(str(SCRIPT.relative_to(ROOT)), "atlas_industrial_round5_build")


def raw_records() -> tuple[list[str], list[dict[str, str]]]:
    """Read all captured UK source rows, including their genuine exclusion control.

    Returns
    -------
    tuple[list[str], list[dict[str, str]]]
        Original CSV field order and Windows-1252-decoded mutable source rows.
    """
    with SOURCE.open(encoding="windows-1252", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        return list(reader.fieldnames), list(reader)


def raw_payload(fields: list[str], rows: list[dict[str, str]]) -> bytes:
    """Encode explicit CSV fixture mutations without changing other source cells.

    Parameters
    ----------
    fields
        Complete original source header in its accepted order.
    rows
        Complete source rows with only the test-selected cells changed.

    Returns
    -------
    bytes
        Windows-1252 CSV body with the original column contract.
    """
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("windows-1252")


def test_actual_raw_selection_equals_complete_snapshot(producer: ModuleType) -> None:
    """Complete raw UK/French selection reproduces all 393 snapshot records apart from the two declared French capture fields."""
    selected, uk_count, fr_count = producer.select_sources(
        SOURCE.read_bytes(),
        ADEME.read_bytes(),
        ademe_updated=producer.metadata_date(METADATA.read_bytes()),
    )
    assert (uk_count, fr_count, len(selected)) == (364, 32, 393)
    historical = producer.read_snapshot(SNAPSHOT)
    for actual, expected in zip(selected, historical, strict=True):
        ignored = (
            {"source_row_id", "source_record_updated"}
            if actual["source"] == "fr-ademe-h2"
            else set()
        )
        assert {k: v for k, v in actual.items() if k not in ignored} == {
            k: v for k, v in expected.items() if k not in ignored
        }
    assert producer.clean(None) == "" and producer.clean(" observed ") == "observed"


def test_all_original_points_against_independent_projection(producer: ModuleType) -> None:
    """All 362 grid conversions agree with stored references within 0.001 metre; the faulty baseline exceeds 100 metres."""
    references = json.loads(REFERENCES.read_text())["records"]
    assert len(references) == 362
    for record in references:
        lat, lon = producer.osgb36_grid_to_wgs84(record["easting"], record["northing"])
        phi, reference_phi = math.radians(lat), math.radians(record["latitude"])
        difference_phi = phi - reference_phi
        difference_lon = math.radians(lon - record["longitude"])
        distance = (
            6371008.8
            * 2
            * math.asin(
                math.sqrt(
                    math.sin(difference_phi / 2) ** 2
                    + math.cos(phi) * math.cos(reference_phi) * math.sin(difference_lon / 2) ** 2
                )
            )
        )
        assert distance < 0.001
        old_phi = math.radians(record["original_faulty_latitude"])
        old_difference_lon = math.radians(lon - record["original_faulty_longitude"])
        original_error = (
            6371008.8
            * 2
            * math.asin(
                math.sqrt(
                    math.sin((phi - old_phi) / 2) ** 2
                    + math.cos(phi) * math.cos(old_phi) * math.sin(old_difference_lon / 2) ** 2
                )
            )
        )
        assert original_error > 100
    lat, lon = producer.osgb36_grid_to_wgs84(651409.903, 313177.270)
    assert abs(lat - 52.6579785974) < 1e-9 and abs(lon - 1.7160519457) < 1e-9
    for east, north in [(-1, 0), (700001, 0), (0, 1300001), (float("nan"), 0), (0, float("inf"))]:
        with pytest.raises(ValueError, match="BNG point"):
            producer.osgb36_grid_to_wgs84(east, north)


def test_native_full_rebuild_preserves_historical_bytes(
    tmp_path: Path, producer: ModuleType
) -> None:
    """API and normal/optimised CLI builds reproduce all 393 accepted rows without changing source snapshot bytes."""
    before = SNAPSHOT.read_bytes(), DATA.read_bytes()
    for optimize in (False, True):
        output = tmp_path / f"built-{optimize}.tsv"
        result = run_cli(SCRIPT, "--output", str(output), optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        assert output.read_bytes() == DATA.read_bytes()
    assert producer.build(SNAPSHOT, tmp_path / "api.tsv") == 393
    assert (tmp_path / "api.tsv").read_bytes() == DATA.read_bytes()
    assert before == (SNAPSHOT.read_bytes(), DATA.read_bytes())


def test_actual_raw_refresh_is_isolated(tmp_path: Path, producer: ModuleType) -> None:
    """Raw refresh writes only owned snapshot/manifest/output files and reproduces the complete accepted table."""
    snapshot, manifest = tmp_path / "snapshot.tsv", tmp_path / "manifest.tsv"
    counts = producer.refresh_snapshot(
        SOURCE.read_bytes(),
        ADEME.read_bytes(),
        ademe_updated=producer.metadata_date(METADATA.read_bytes()),
        snapshot=snapshot,
        manifest=manifest,
        retrieved="2026-09-28",
    )
    assert counts == (364, 32, 362, 31)
    assert len(read_table(snapshot)[1]) == 393
    assert producer.build(snapshot, tmp_path / "api.tsv") == 393
    assert (tmp_path / "api.tsv").read_bytes() == DATA.read_bytes()
    assert {r["source"] for r in read_table(manifest)[1]} == {"uk-repd-ad", "fr-ademe-h2"}
    for optimize in (False, True):
        result = run_cli(
            SCRIPT,
            "--refresh",
            "--repd-source",
            str(SOURCE),
            "--ademe-source",
            str(ADEME),
            "--ademe-metadata",
            str(METADATA),
            "--snapshot",
            str(tmp_path / "cli-snapshot.tsv"),
            "--manifest",
            str(tmp_path / "cli-manifest.tsv"),
            "--output",
            str(tmp_path / "cli.tsv"),
            "--date",
            "2026-09-28",
            optimize=optimize,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert (tmp_path / "cli.tsv").read_bytes() == DATA.read_bytes()


@pytest.mark.parametrize(
    ("source", "field", "value"),
    [
        ("uk-repd-ad", "source_x", "unknown"),
        ("uk-repd-ad", "source_y", "1300001"),
        ("uk-repd-ad", "lat", "0"),
        ("uk-repd-ad", "country", "unknown"),
        ("uk-repd-ad", "region_or_commune", "Northern Ireland"),
        ("uk-repd-ad", "technology_type", "Wind"),
        ("fr-ademe-h2", "country", "unknown"),
        ("fr-ademe-h2", "technology_type", "Distribution"),
        ("fr-ademe-h2", "process_detail", "unknown"),
        ("fr-ademe-h2", "source", "unknown"),
        ("fr-ademe-h2", "source_record_id", ""),
        ("fr-ademe-h2", "facility_name", ""),
        ("fr-ademe-h2", "lat", "NaN"),
        ("fr-ademe-h2", "lon", "181"),
    ],
)
def test_full_snapshot_mutations_refuse(
    tmp_path: Path, source: str, field: str, value: str
) -> None:
    """Invalid selected-source identity, location or process cells refuse before creating the optimised CLI output."""
    fields, rows = read_table(SNAPSHOT)
    next(r for r in rows if r["source"] == source)[field] = value
    path = tmp_path / "changed.tsv"
    write_table(path, fields, rows)
    result = run_cli(
        SCRIPT, "--snapshot", str(path), "--output", str(tmp_path / "out.tsv"), optimize=True
    )
    assert result.returncode == 1 and "FAIL" in result.stdout and "Traceback" not in result.stderr
    assert not (tmp_path / "out.tsv").exists()


@pytest.mark.parametrize(
    "corruption", ["empty", "header", "extra", "short", "quote", "utf8", "duplicate", "missing"]
)
def test_snapshot_integrity_refuses(tmp_path: Path, corruption: str) -> None:
    """Malformed, incomplete, duplicate or unavailable snapshot tables return trace-free native failures."""
    fields, rows = read_table(SNAPSHOT)
    path = tmp_path / "changed.tsv"
    if corruption == "empty":
        rows.clear()
    elif corruption == "header":
        fields = fields[::-1]
    elif corruption == "duplicate":
        rows.append(rows[0].copy())
    write_table(path, fields, rows)
    if corruption == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif corruption == "short":
        path.write_text("\t".join(fields) + "\nonly-one-cell\n")
    elif corruption == "quote":
        path.write_text("\t".join(fields) + '\n"unterminated')
    elif corruption == "utf8":
        path.write_bytes(b"\xff")
    elif corruption == "missing":
        path.unlink()
    result = run_cli(SCRIPT, "--snapshot", str(path), "--output", str(tmp_path / "output.tsv"))
    assert result.returncode == 1 and "Traceback" not in result.stderr


def test_original_optional_activity_and_public_schema(producer: ModuleType) -> None:
    """Additional source status wording survives, while missing required string cells and empty selection refuse."""
    rows = producer.read_snapshot(SNAPSHOT)
    next(r for r in rows if r["source"] == "fr-ademe-h2")["status"] = (
        "source-specific additional status"
    )
    output = producer.rows_from_snapshot(rows)
    assert len(output) == 393 and "source-specific additional status" in output[0]["status"]
    with pytest.raises(ValueError, match="no records"):
        producer.rows_from_snapshot([])
    changed = json.loads(json.dumps(rows))
    changed[0]["facility_name"] = None
    with pytest.raises(ValueError, match="schema"):
        producer.rows_from_snapshot(changed)
    rows[0].pop("country")
    with pytest.raises(ValueError, match="schema"):
        producer.rows_from_snapshot(rows)


@pytest.mark.parametrize(
    "corruption", ["header", "empty", "extra", "short", "no_selection", "empty_id", "duplicate"]
)
def test_actual_raw_boundaries_refuse(producer: ModuleType, corruption: str) -> None:
    """Source header, shape, selection and identity defects refuse through the actual raw selector."""
    fields, rows = raw_records()
    fr = json.loads(ADEME.read_text())
    if corruption == "header":
        fields[0] = "unexpected"
        rows = [
            {"unexpected" if k == "Technology Type" else k: v for k, v in r.items()} for r in rows
        ]
    elif corruption == "empty":
        rows.clear()
        fr["results"] = []
        fr["total"] = 0
    elif corruption == "no_selection":
        for row in rows:
            row["Technology Type"] = "Wind"
        for row in fr["results"]:
            row["site_type"] = "Distribution"
    elif corruption == "empty_id":
        rows[0]["Ref ID"] = ""
    elif corruption == "duplicate":
        rows.append(rows[0].copy())
    raw = raw_payload(fields, rows)
    if corruption == "extra":
        raw += (
            raw_payload(fields, rows).decode("windows-1252").splitlines()[1].encode("windows-1252")
            + b",extra\r\n"
        )
    elif corruption == "short":
        raw += b"one-cell\r\n"
    with pytest.raises(ValueError):
        producer.select_sources(raw, json.dumps(fr).encode(), ademe_updated="2026-09-30")


@pytest.mark.parametrize(
    "corruption",
    [
        "root",
        "results",
        "total",
        "record",
        "nested",
        "missing",
        "negative",
        "nonfinite",
        "boolean",
        "invalid_number",
    ],
)
def test_complete_ademe_response_refusals(producer: ModuleType, corruption: str) -> None:
    """Malformed French envelopes or invalid megawatt values refuse without silently replacing source observations."""
    body = json.loads(ADEME.read_text())
    if corruption == "root":
        body = []
    elif corruption == "results":
        body["results"] = {}
    elif corruption == "total":
        body["total"] += 1
    elif corruption == "record":
        body["results"][0] = []
    elif corruption == "nested":
        body["results"][0]["site_nom"] = {"unexpected": "object"}
    elif corruption == "missing":
        body["results"][0].pop("_id")
    else:
        body["results"][0]["puissance_mw"] = {
            "negative": -1,
            "nonfinite": float("nan"),
            "boolean": True,
            "invalid_number": "unknown",
        }[corruption]
    with pytest.raises(ValueError):
        producer.select_sources(
            SOURCE.read_bytes(), json.dumps(body).encode(), ademe_updated="2026-09-30"
        )


@pytest.mark.parametrize(
    "value",
    [
        {},
        [],
        {"dataUpdatedAt": None},
        {"dataUpdatedAt": "unknown"},
        {"dataUpdatedAt": "2026-09-30T07:00:00"},
    ],
)
def test_actual_metadata_contract_refusals(producer: ModuleType, value: object) -> None:
    """Missing or noncanonical timezone-qualified metadata update dates cannot supply a valid source date."""
    with pytest.raises(ValueError):
        producer.metadata_date(json.dumps(value).encode())


@pytest.mark.parametrize("date", ["20260928", "2026-02-30"])
def test_exact_retrieval_dates_required(tmp_path: Path, producer: ModuleType, date: str) -> None:
    """Noncanonical or impossible dates refuse row conversion, selection and isolated refresh."""
    with pytest.raises(ValueError):
        producer.rows_from_snapshot(producer.read_snapshot(SNAPSHOT), retrieved=date)
    with pytest.raises(ValueError):
        producer.select_sources(SOURCE.read_bytes(), ADEME.read_bytes(), ademe_updated=date)
    with pytest.raises(ValueError):
        producer.refresh_snapshot(
            SOURCE.read_bytes(),
            ADEME.read_bytes(),
            ademe_updated="2026-09-30",
            snapshot=tmp_path / "s.tsv",
            manifest=tmp_path / "m.tsv",
            retrieved=date,
        )


def test_historical_protection_and_atomic_failures(tmp_path: Path, producer: ModuleType) -> None:
    """Input aliases, unwritable destinations and unencodable output preserve accepted data and remove temporary residue."""
    before = DATA.read_bytes(), SNAPSHOT.read_bytes()
    for target in [DATA, SNAPSHOT, tmp_path / "link.tsv"]:
        if target.name == "link.tsv":
            target.symlink_to(DATA)
        result = run_cli(SCRIPT, "--output", str(target))
        assert result.returncode == 1 and "separate" in result.stdout
    occupied = tmp_path / "occupied"
    occupied.write_text("preserve")
    assert producer.main(["--output", str(occupied / "output.tsv")]) == 1
    directory = tmp_path / "directory"
    directory.mkdir()
    assert producer.main(["--output", str(directory)]) == 1
    rows = producer.rows_from_snapshot(producer.read_snapshot(SNAPSHOT))
    rows[0]["facility_name"] = "\ud800"
    output = tmp_path / "atomic.tsv"
    output.write_text("preserve")
    with pytest.raises(UnicodeError):
        producer.write_table(output, producer.FIELDS, rows)
    assert output.read_text() == "preserve" and not list(tmp_path.glob("*.tmp"))
    assert before == (DATA.read_bytes(), SNAPSHOT.read_bytes())


def test_cli_refresh_refuses_bad_configuration(tmp_path: Path, producer: ModuleType) -> None:
    """Incomplete refresh options, overlapping outputs and absent source files return failure through the real CLI."""
    assert (
        producer.main(
            ["--output", str(tmp_path / "out.tsv"), "--manifest", str(tmp_path / "m.tsv")]
        )
        == 1
    )
    assert producer.main(["--refresh", "--output", str(tmp_path / "out.tsv")]) == 1
    assert (
        producer.main(
            [
                "--refresh",
                "--snapshot",
                str(tmp_path / "s.tsv"),
                "--manifest",
                str(tmp_path / "s.tsv"),
                "--output",
                str(tmp_path / "out.tsv"),
            ]
        )
        == 1
    )
    assert (
        producer.main(
            [
                "--refresh",
                "--snapshot",
                str(tmp_path / "s.tsv"),
                "--manifest",
                str(tmp_path / "m.tsv"),
                "--output",
                str(tmp_path / "out.tsv"),
                "--repd-source",
                str(tmp_path / "missing.csv"),
            ]
        )
        == 1
    )
    assert run_cli(SCRIPT).returncode == 2


class SourceServer(ThreadingHTTPServer):
    """Serve the complete genuine UK selection over a real trusted TLS socket."""

    bodies: dict[str, bytes]


class SourceHandler(BaseHTTPRequestHandler):
    """Provide real HTTP response, redirect and timeout controls."""

    def do_GET(self) -> None:
        """Serve the selected real body, status or redirect; the stall control delays its body by 0.2 seconds."""
        server = self.server
        assert isinstance(server, SourceServer)
        if self.path in {"/redirect", "/downgrade", "/credentials", "/loop"}:
            self.send_response(302)
            target = {
                "/redirect": "/csv",
                "/downgrade": "http://127.0.0.1/source",
                "/credentials": "https://user:secret@localhost/source",
                "/loop": "/loop",
            }[self.path]
            self.send_header("Location", target)
            self.end_headers()
            return
        self.send_response(
            201 if self.path == "/created" else 404 if self.path == "/missing" else 200
        )
        body = server.bodies.get(self.path, server.bodies["/repd"])
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.path == "/stall":
            time.sleep(0.2)
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ssl.SSLError):
            pass

    def log_message(self, fmt: str, *args: object) -> None:
        """Keep native HTTP diagnostics out of successful test output."""


@pytest.fixture
def tls_source(tmp_path: Path) -> Iterator[tuple[str, Path]]:
    """Serve captured UK, French and metadata responses on a real trusted TLS socket.

    Parameters
    ----------
    tmp_path
        Pytest-owned certificate and key directory.

    Yields
    ------
    tuple[str, pathlib.Path]
        Anonymous local HTTPS origin and the certificate trusted by the real client.

    Raises
    ------
    RuntimeError
        OpenSSL is unavailable; native TLS conformance cannot be reported as passing.

    Notes
    -----
    The listener and owned serving thread are shut down when the fixture closes.
    """
    ca, key = tmp_path / "ca.pem", tmp_path / "key.pem"
    openssl = shutil.which("openssl")
    if openssl is None:
        raise RuntimeError("Native TLS conformance requires OpenSSL")
    subprocess.run(
        [
            openssl,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key),
            "-out",
            str(ca),
            "-days",
            "1",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost,IP:127.0.0.1",
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    server = SourceServer(("127.0.0.1", 0), SourceHandler)
    server.bodies = {
        "/repd": SOURCE.read_bytes(),
        "/ademe": ADEME.read_bytes(),
        "/metadata": METADATA.read_bytes(),
    }
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(ca, key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"https://127.0.0.1:{server.server_port}", ca
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_real_tls_and_complete_native_refresh(
    tmp_path: Path, producer: ModuleType, tls_source: tuple[str, Path]
) -> None:
    """Trusted real HTTPS refresh emits 393 rows and rejects output aliasing the trusted certificate."""
    url, ca = tls_source
    assert producer.download(url + "/redirect", ca_file=ca) == SOURCE.read_bytes()
    result = run_cli(
        SCRIPT,
        "--refresh",
        "--snapshot",
        str(tmp_path / "snapshot.tsv"),
        "--manifest",
        str(tmp_path / "manifest.tsv"),
        "--output",
        str(tmp_path / "output.tsv"),
        "--repd-url",
        url + "/repd",
        "--ademe-url",
        url + "/ademe",
        "--ademe-metadata-url",
        url + "/metadata",
        "--ca-file",
        str(ca),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(read_table(tmp_path / "output.tsv")[1]) == 393
    assert len(read_table(tmp_path / "snapshot.tsv")[1]) == 393
    before = ca.read_bytes()
    assert (
        producer.main(
            [
                "--refresh",
                "--snapshot",
                str(tmp_path / "guard-snapshot.tsv"),
                "--manifest",
                str(tmp_path / "guard-manifest.tsv"),
                "--output",
                str(ca),
                "--ca-file",
                str(ca),
            ]
        )
        == 1
    )
    assert ca.read_bytes() == before


@pytest.mark.parametrize(
    "path", ["/downgrade", "/credentials", "/loop", "/missing", "/created", "/stall"]
)
def test_native_transport_refusals(
    producer: ModuleType, tls_source: tuple[str, Path], path: str
) -> None:
    """Unsafe redirects, invalid HTTP statuses and a real delayed body refuse with their actual transport errors."""
    url, ca = tls_source
    with pytest.raises((ValueError, HTTPError, URLError, TimeoutError)):
        producer.download(url + path, ca_file=ca, timeout=0.03 if path == "/stall" else 5)


def test_real_certificate_trust_and_limits(
    producer: ModuleType, tls_source: tuple[str, Path]
) -> None:
    """Untrusted TLS, responses over ten bytes, invalid finite limits and unsafe endpoint URLs refuse."""
    url, ca = tls_source
    with pytest.raises(URLError):
        producer.download(url + "/csv")
    with pytest.raises(ValueError, match="byte limit"):
        producer.download(url + "/csv", ca_file=ca, max_bytes=10)
    for timeout, limit in [(0, 100), (float("inf"), 100), (1, 0)]:
        with pytest.raises(ValueError):
            producer.download(url + "/csv", timeout=timeout, max_bytes=limit)
    for invalid in [
        "http://localhost/source",
        "https:///source",
        "https://u:p@localhost/source",
        "https://localhost:0/source",
        "https://localhost:99999/source",
        "https://localhost/white space",
    ]:
        with pytest.raises(ValueError):
            producer.download(invalid)


def test_explicit_optional_capacity_and_operator_fields(producer: ModuleType) -> None:
    """Absent source capacities remain blank and an absent French operator keeps the explicit not-provided marker."""
    fields, rows = raw_records()
    original_id = rows[0]["Ref ID"]
    rows[0]["Installed Capacity (MWelec)"] = "Not set"
    french = json.loads(ADEME.read_text())
    source_id = french["results"][0]["_id"]
    french["results"][0]["puissance_mw"] = None
    french["results"][0]["capacite_production"] = None
    french["results"][0]["station_operateur"] = None
    selected, _, _ = producer.select_sources(
        raw_payload(fields, rows), json.dumps(french).encode(), ademe_updated="2026-09-30"
    )
    assert len(selected) == 393
    uk = next(
        r for r in selected if r["source"] == "uk-repd-ad" and r["source_record_id"] == original_id
    )
    fr = next(
        r for r in selected if r["source"] == "fr-ademe-h2" and r["source_row_id"] == source_id
    )
    assert uk["capacity"] == "" and fr["capacity"] == ""
    assert fr["operator"] == "not provided"
