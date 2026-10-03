# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — UK industrial producer conformance

"""Build all accepted UK facilities from original source cells and read-only snapshots."""

from __future__ import annotations

import csv
import io
import json
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

DIRECTORY = ROOT / "05_global_reactor_map/imports/industrial_facilities/expansion_round3"
SCRIPT = DIRECTORY / "build_dataset.py"
SNAPSHOT = DIRECTORY / "selected_source_snapshot.tsv"
DATA = DIRECTORY / "industrial_facilities_round3.tsv"
SOURCE = ROOT / "tests/data/industrial_round3/uk_prtr.csv"


@pytest.fixture
def producer() -> ModuleType:
    return load_module(str(SCRIPT.relative_to(ROOT)), "atlas_industrial_round3_build")


def raw_records() -> tuple[list[str], list[dict[str, str]]]:
    """Read every actual selected raw record and its genuine exclusion control."""
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        return list(reader.fieldnames), list(reader)


def raw_payload(fields: list[str], rows: list[dict[str, str]]) -> bytes:
    """Serialize complete source copies without changing unmutated source cells."""
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8-sig")


def test_actual_raw_selection_equals_complete_snapshot(producer: ModuleType) -> None:
    selected, count = producer.select_source(SOURCE.read_bytes())
    assert count == 723 and selected == producer.read_snapshot(SNAPSHOT)
    assert len(selected) == 722
    assert producer.clean(None) == "" and producer.clean(" observed ") == "observed"


def test_native_full_rebuild_preserves_historical_bytes(
    tmp_path: Path, producer: ModuleType
) -> None:
    before = SNAPSHOT.read_bytes(), DATA.read_bytes()
    for optimize in (False, True):
        output = tmp_path / f"built-{optimize}.tsv"
        result = run_cli(SCRIPT, "--output", str(output), optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        assert output.read_bytes() == DATA.read_bytes()
    assert producer.build(SNAPSHOT, tmp_path / "api.tsv") == 722
    assert (tmp_path / "api.tsv").read_bytes() == DATA.read_bytes()
    assert before == (SNAPSHOT.read_bytes(), DATA.read_bytes())


def test_actual_raw_refresh_is_isolated(tmp_path: Path, producer: ModuleType) -> None:
    snapshot, manifest = tmp_path / "snapshot.tsv", tmp_path / "manifest.tsv"
    assert producer.refresh_snapshot(
        SOURCE.read_bytes(), snapshot=snapshot, manifest=manifest, retrieved="2026-09-28"
    ) == (723, 722)
    assert snapshot.read_bytes() == SNAPSHOT.read_bytes()
    assert read_table(manifest)[1][0]["selected_rows"] == "722"
    for optimize in (False, True):
        result = run_cli(
            SCRIPT,
            "--refresh",
            "--raw-source",
            str(SOURCE),
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
    ("field", "value"),
    [
        ("source_record_id", ""),
        ("facility_name", ""),
        ("operator", ""),
        ("source", "unknown"),
        ("reporting_year", "2023"),
        ("country", "unknown"),
        ("nace_code", "99"),
        ("lat", "unknown"),
        ("lat", "NaN"),
        ("lon", "181"),
    ],
)
def test_full_snapshot_mutations_refuse(tmp_path: Path, field: str, value: str) -> None:
    fields, rows = read_table(SNAPSHOT)
    rows[0][field] = value
    path = tmp_path / "changed.tsv"
    write_table(path, fields, rows)
    result = run_cli(
        SCRIPT, "--snapshot", str(path), "--output", str(tmp_path / "output.tsv"), optimize=True
    )
    assert result.returncode == 1 and "FAIL" in result.stdout
    assert "Traceback" not in result.stderr and not (tmp_path / "output.tsv").exists()


@pytest.mark.parametrize(
    "corruption", ["empty", "header", "extra", "short", "quote", "utf8", "duplicate", "missing"]
)
def test_snapshot_integrity_refuses(tmp_path: Path, corruption: str) -> None:
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
    rows = producer.read_snapshot(SNAPSHOT)
    rows[0]["annex_i_activity_code"] = ""
    output = producer.rows_from_snapshot(rows)
    assert len(output) == 722 and "UK PRTR Annex I" not in output[0]["process_or_activity"]
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
    "corruption", ["header", "empty", "extra", "short", "duplicate", "empty_id", "no_selection"]
)
def test_actual_raw_boundaries_refuse(producer: ModuleType, corruption: str) -> None:
    fields, rows = raw_records()
    if corruption == "header":
        fields[0] = "unexpected"
        rows = [
            {"unexpected" if k == "FacilityReport_NationalID" else k: v for k, v in r.items()}
            for r in rows
        ]
    elif corruption == "empty":
        rows.clear()
    elif corruption == "duplicate":
        rows.append(rows[0].copy())
    elif corruption == "empty_id":
        rows[0]["FacilityReport_NationalID"] = ""
    elif corruption == "no_selection":
        for row in rows:
            row["FacilityReport_NACEMainEconomicActivityCode"] = "99"
    body = raw_payload(fields, rows)
    if corruption == "extra":
        body += (
            raw_payload(fields, rows).decode("utf-8-sig").splitlines()[1].encode() + b",extra\r\n"
        )
    elif corruption == "short":
        body += b"only-one-cell\r\n"
    with pytest.raises(ValueError):
        producer.select_source(body)


@pytest.mark.parametrize("date", ["20260928", "2026-02-30"])
def test_exact_retrieval_dates_required(tmp_path: Path, producer: ModuleType, date: str) -> None:
    with pytest.raises(ValueError):
        producer.rows_from_snapshot(producer.read_snapshot(SNAPSHOT), retrieved=date)
    with pytest.raises(ValueError):
        producer.refresh_snapshot(
            SOURCE.read_bytes(),
            snapshot=tmp_path / "snapshot.tsv",
            manifest=tmp_path / "manifest.tsv",
            retrieved=date,
        )


def test_historical_protection_and_atomic_failures(tmp_path: Path, producer: ModuleType) -> None:
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
                "--raw-source",
                str(tmp_path / "missing.csv"),
            ]
        )
        == 1
    )
    assert run_cli(SCRIPT).returncode == 2


class SourceServer(ThreadingHTTPServer):
    """Serve the complete genuine UK selection over a real trusted TLS socket."""

    body: bytes


class SourceHandler(BaseHTTPRequestHandler):
    """Provide real HTTP response, redirect and timeout controls."""

    def do_GET(self) -> None:
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
        self.send_header("Content-Length", str(len(server.body)))
        self.end_headers()
        if self.path == "/stall":
            time.sleep(0.2)
        try:
            self.wfile.write(server.body)
        except (BrokenPipeError, ConnectionResetError, ssl.SSLError):
            pass

    def log_message(self, fmt: str, *args: object) -> None:
        """Keep native HTTP diagnostics out of successful test output."""


@pytest.fixture
def tls_source(tmp_path: Path) -> Iterator[tuple[str, Path]]:
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
    server.body = SOURCE.read_bytes()
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
        "--source-url",
        url + "/csv",
        "--ca-file",
        str(ca),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(read_table(tmp_path / "output.tsv")[1]) == 722
    assert (tmp_path / "snapshot.tsv").read_bytes() == SNAPSHOT.read_bytes()
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
    url, ca = tls_source
    with pytest.raises((ValueError, HTTPError, URLError, TimeoutError)):
        producer.download(url + path, ca_file=ca, timeout=0.03 if path == "/stall" else 5)


def test_real_certificate_trust_and_limits(
    producer: ModuleType, tls_source: tuple[str, Path]
) -> None:
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
