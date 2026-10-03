# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — Canadian and Australian industrial producer conformance

"""Rebuild all original records from genuine licensed source cells and snapshots."""

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

DIRECTORY = ROOT / "05_global_reactor_map/imports/industrial_facilities/expansion_round2"
SCRIPT = DIRECTORY / "build_dataset.py"
SNAPSHOT = DIRECTORY / "selected_source_snapshot.tsv"
DATA = DIRECTORY / "industrial_facilities_round2.tsv"
FIXTURES = ROOT / "tests/data/industrial_round2"


@pytest.fixture
def producer() -> ModuleType:
    return load_module(str(SCRIPT.relative_to(ROOT)), "atlas_industrial_round2_build")


def source_csv(path: Path, changes: dict[str, str] | None = None) -> bytes:
    """Serialize the complete real selected raw input after one explicit mutation."""
    encoding = "windows-1252" if path.name == "canada.csv" else "utf-8-sig"
    with path.open(encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames, list(reader)
    assert fields is not None
    if changes:
        rows[0].update(changes)
    body = io.StringIO(newline="")
    writer = csv.DictWriter(body, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return body.getvalue().encode(encoding)


def test_complete_actual_sources_equal_historical_snapshot(producer: ModuleType) -> None:
    canada = (FIXTURES / "canada.csv").read_bytes()
    australia = (FIXTURES / "australia.csv").read_bytes()
    assert producer.select_sources(canada, australia) == producer.read_snapshot(SNAPSHOT)
    assert producer.clean(None) == "" and producer.clean("  observed  ") == "observed"


def test_full_native_build_matches_original_bytes(tmp_path: Path, producer: ModuleType) -> None:
    before = SNAPSHOT.read_bytes(), DATA.read_bytes()
    for optimize in (False, True):
        output = tmp_path / f"built-{optimize}.tsv"
        result = run_cli(SCRIPT, "--output", str(output), optimize=optimize)
        assert result.returncode == 0, result.stdout + result.stderr
        assert output.read_bytes() == DATA.read_bytes()
    assert producer.build(SNAPSHOT, tmp_path / "api.tsv") == 1776
    assert (tmp_path / "api.tsv").read_bytes() == DATA.read_bytes()
    assert before == (SNAPSHOT.read_bytes(), DATA.read_bytes())


def test_genuine_raw_refresh_is_isolated_and_exact(tmp_path: Path, producer: ModuleType) -> None:
    canada, australia = (
        (FIXTURES / "canada.csv").read_bytes(),
        (FIXTURES / "australia.csv").read_bytes(),
    )
    snapshot, manifest = tmp_path / "snapshot.tsv", tmp_path / "manifest.tsv"
    assert producer.refresh_snapshot(
        canada, australia, snapshot=snapshot, manifest=manifest, retrieved="2026-09-27"
    ) == (len(canada), len(australia))
    assert snapshot.read_bytes() == SNAPSHOT.read_bytes()
    records = read_table(manifest)[1]
    assert [r["selected_rows"] for r in records] == ["908", "868"]
    assert (
        producer.main(
            [
                "--refresh",
                "--snapshot",
                str(tmp_path / "cli-snapshot.tsv"),
                "--manifest",
                str(tmp_path / "cli-manifest.tsv"),
                "--output",
                str(tmp_path / "cli.tsv"),
                "--canada-source",
                str(FIXTURES / "canada.csv"),
                "--australia-source",
                str(FIXTURES / "australia.csv"),
                "--date",
                "2026-09-27",
            ]
        )
        == 0
    )
    assert (tmp_path / "cli.tsv").read_bytes() == DATA.read_bytes()


def test_original_field_fallbacks_remain_source_based(producer: ModuleType) -> None:
    snapshot = producer.read_snapshot(SNAPSHOT)
    ca = next(r for r in snapshot if r["source"] == "canada-npri")
    au = next(r for r in snapshot if r["source"] == "australia-npi")
    ca["datum"] = ca["operator"] = ""
    au["source_row_url"] = ""
    au["main_activities"] = au["process_label"]
    rows = producer.rows_from_snapshot(snapshot)
    canadian = next(r for r in rows if r["stable_id"] == "canada-npri:" + ca["source_record_id"])
    australian = next(
        r for r in rows if r["stable_id"] == "australia-npi:" + au["source_record_id"]
    )
    assert canadian["operator"] == "not provided" and "source datum" not in canadian["precision"]
    assert australian["source_url"] == producer.AUSTRALIA_LANDING
    assert "source main activities" not in australian["process_or_activity"]
    au["main_activities"] = ""
    assert len(producer.rows_from_snapshot(snapshot)) == 1776
    ca_raw = source_csv(FIXTURES / "canada.csv", {"Facility Name / Nom de l'installation": ""})
    au_raw = source_csv(FIXTURES / "australia.csv", {"facility_name": ""})
    selected = producer.select_sources(ca_raw, au_raw)
    assert len(selected) == 1776 and all(r["facility_name"] for r in selected)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source", "unknown"),
        ("facility_name", ""),
        ("source_record_id", ""),
        ("lat", "NaN"),
        ("lon", "181"),
        ("lat", "unknown"),
        ("country", "Canada"),
        ("latest_report_year", "2023/2024"),
        ("process_code", "99"),
    ],
)
def test_full_snapshot_mutations_refuse(
    tmp_path: Path, producer: ModuleType, field: str, value: str
) -> None:
    fields, rows = read_table(SNAPSHOT)
    assert rows[0]["source"] == "australia-npi"
    rows[0][field] = value
    snapshot = tmp_path / "changed.tsv"
    write_table(snapshot, fields, rows)
    result = run_cli(
        SCRIPT, "--snapshot", str(snapshot), "--output", str(tmp_path / "output.tsv"), optimize=True
    )
    assert result.returncode == 1 and "FAIL" in result.stdout
    assert "Traceback" not in result.stderr and not (tmp_path / "output.tsv").exists()
    if field in {"country", "latest_report_year", "process_code"}:
        _, rows = read_table(SNAPSHOT)
        ca = next(r for r in rows if r["source"] == "canada-npri")
        ca[field] = "Australia" if field == "country" else value
        with pytest.raises(ValueError, match="Canadian snapshot record"):
            producer.rows_from_snapshot(rows)
        write_table(snapshot, fields, rows)
        result = run_cli(
            SCRIPT, "--snapshot", str(snapshot), "--output", str(tmp_path / "canadian.tsv")
        )
        assert result.returncode == 1 and "Canadian snapshot record" in result.stdout


@pytest.mark.parametrize(
    "corruption", ["empty", "header", "extra", "short", "quote", "utf8", "duplicate", "missing"]
)
def test_snapshot_integrity_refuses(tmp_path: Path, corruption: str) -> None:
    fields, rows = read_table(SNAPSHOT)
    snapshot = tmp_path / "changed.tsv"
    if corruption == "empty":
        rows.clear()
    elif corruption == "header":
        fields = fields[::-1]
    elif corruption == "duplicate":
        rows.append(rows[0].copy())
    write_table(snapshot, fields, rows)
    if corruption == "extra":
        snapshot.write_text(snapshot.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif corruption == "short":
        snapshot.write_text("\t".join(fields) + "\nunknown\n")
    elif corruption == "quote":
        snapshot.write_text("\t".join(fields) + '\n"unterminated')
    elif corruption == "utf8":
        snapshot.write_bytes(b"\xff")
    elif corruption == "missing":
        snapshot.unlink()
    result = run_cli(SCRIPT, "--snapshot", str(snapshot), "--output", str(tmp_path / "output.tsv"))
    assert result.returncode == 1 and "Traceback" not in result.stderr


def test_raw_table_boundaries_and_unknowns_refuse(producer: ModuleType) -> None:
    ca, au = (FIXTURES / "canada.csv").read_bytes(), (FIXTURES / "australia.csv").read_bytes()
    body = ca.decode("windows-1252")
    with pytest.raises(ValueError, match="columns"):
        producer.select_sources(b"unrelated\nvalue\n", au)
    header = body.splitlines()[0]
    with pytest.raises(ValueError, match="no records"):
        producer.select_sources((header + "\n").encode("windows-1252"), au)
    with pytest.raises(ValueError, match="wrong width"):
        producer.select_sources((body + "only-one-cell\n").encode("windows-1252"), au)
    ca_rows = list(csv.DictReader(io.StringIO(body)))
    au_rows = list(csv.DictReader(io.StringIO(au.decode("utf-8-sig"))))
    for row in ca_rows:
        row[producer.CANADA_REQUIRED[0]] = "1900"
    for row in au_rows:
        row["latest_report_year"] = "1900/1901"
    for rows, encoding, destination in [
        (ca_rows, "windows-1252", "ca"),
        (au_rows, "utf-8-sig", "au"),
    ]:
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        if destination == "ca":
            ca = stream.getvalue().encode(encoding)
        else:
            au = stream.getvalue().encode(encoding)
    with pytest.raises(ValueError, match="no qualifying"):
        producer.select_sources(ca, au)
    snapshot = producer.read_snapshot(SNAPSHOT)
    with pytest.raises(ValueError, match="no records"):
        producer.rows_from_snapshot([])
    changed = json.loads(json.dumps(snapshot))
    changed[0]["facility_name"] = None
    with pytest.raises(ValueError, match="schema"):
        producer.rows_from_snapshot(changed)
    snapshot[0].pop("country")
    with pytest.raises(ValueError, match="schema"):
        producer.rows_from_snapshot(snapshot)


@pytest.mark.parametrize("date", ["20260927", "2026-02-30"])
def test_exact_retrieval_date_required(tmp_path: Path, producer: ModuleType, date: str) -> None:
    with pytest.raises(ValueError):
        producer.rows_from_snapshot(producer.read_snapshot(SNAPSHOT), retrieved=date)
    with pytest.raises(ValueError):
        producer.refresh_snapshot(
            (FIXTURES / "canada.csv").read_bytes(),
            (FIXTURES / "australia.csv").read_bytes(),
            snapshot=tmp_path / "snapshot.tsv",
            manifest=tmp_path / "manifest.tsv",
            retrieved=date,
        )


def test_historical_input_and_atomic_output_protection(
    tmp_path: Path, producer: ModuleType
) -> None:
    before = DATA.read_bytes(), SNAPSHOT.read_bytes()
    for target in (DATA, SNAPSHOT, tmp_path / "link.tsv"):
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
    assert not list(tmp_path.glob("*.tmp"))
    rows = producer.rows_from_snapshot(producer.read_snapshot(SNAPSHOT))
    rows[0]["facility_name"] = "\ud800"
    output = tmp_path / "atomic.tsv"
    output.write_text("preserve")
    with pytest.raises(UnicodeError):
        producer.write_table(output, producer.FIELDS, rows)
    assert output.read_text() == "preserve" and not list(tmp_path.glob("*.tmp"))
    assert before == (DATA.read_bytes(), SNAPSHOT.read_bytes())


def test_cli_refresh_options_cannot_overwrite_inputs(tmp_path: Path, producer: ModuleType) -> None:
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
                "--canada-source",
                str(tmp_path / "absent.csv"),
            ]
        )
        == 1
    )
    result = run_cli(SCRIPT)
    assert result.returncode == 2 and "--output" in result.stderr


class SourceServer(ThreadingHTTPServer):
    """Serve complete licensed source selections through a real TLS socket."""

    ca_body: bytes
    au_body: bytes


class SourceHandler(BaseHTTPRequestHandler):
    """Provide actual payloads and native redirects, errors and deadlines."""

    def do_GET(self) -> None:
        server = self.server
        assert isinstance(server, SourceServer)
        if self.path in {"/redirect", "/downgrade", "/credentials", "/loop"}:
            self.send_response(302)
            location = {
                "/redirect": "/ca",
                "/downgrade": "http://127.0.0.1/source",
                "/credentials": "https://user:secret@localhost/source",
                "/loop": "/loop",
            }[self.path]
            self.send_header("Location", location)
            self.end_headers()
            return
        body = server.au_body if self.path == "/au" else server.ca_body
        self.send_response(
            201 if self.path == "/created" else 404 if self.path == "/missing" else 200
        )
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.path == "/stall":
            time.sleep(0.2)
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ssl.SSLError):
            pass

    def log_message(self, fmt: str, *args: object) -> None:
        """Keep native HTTP diagnostics out of the test result stream."""


@pytest.fixture
def tls_sources(tmp_path: Path) -> Iterator[tuple[str, Path]]:
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
    server.ca_body = (FIXTURES / "canada.csv").read_bytes()
    server.au_body = (FIXTURES / "australia.csv").read_bytes()
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


def test_native_tls_download_and_full_cli_refresh(
    tmp_path: Path, producer: ModuleType, tls_sources: tuple[str, Path]
) -> None:
    url, ca = tls_sources
    assert (
        producer.download(url + "/redirect", ca_file=ca) == (FIXTURES / "canada.csv").read_bytes()
    )
    result = run_cli(
        SCRIPT,
        "--refresh",
        "--snapshot",
        str(tmp_path / "snapshot.tsv"),
        "--manifest",
        str(tmp_path / "manifest.tsv"),
        "--output",
        str(tmp_path / "output.tsv"),
        "--canada-url",
        url + "/ca",
        "--australia-url",
        url + "/au",
        "--ca-file",
        str(ca),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    rows = read_table(tmp_path / "output.tsv")[1]
    assert len(rows) == 1776 and len({r["retrieved"] for r in rows}) == 1
    assert (tmp_path / "snapshot.tsv").read_bytes() == SNAPSHOT.read_bytes()


@pytest.mark.parametrize(
    "path", ["/downgrade", "/credentials", "/loop", "/missing", "/created", "/stall"]
)
def test_native_transport_refusals(
    producer: ModuleType, tls_sources: tuple[str, Path], path: str
) -> None:
    url, ca = tls_sources
    with pytest.raises((ValueError, HTTPError, URLError, TimeoutError)):
        producer.download(url + path, ca_file=ca, timeout=0.03 if path == "/stall" else 5)


def test_native_transport_trust_and_limits(
    producer: ModuleType, tls_sources: tuple[str, Path]
) -> None:
    url, ca = tls_sources
    before = ca.read_bytes()
    assert (
        producer.main(
            [
                "--refresh",
                "--snapshot",
                str(ca.with_name("guard-snapshot.tsv")),
                "--manifest",
                str(ca.with_name("guard-manifest.tsv")),
                "--output",
                str(ca),
                "--ca-file",
                str(ca),
                "--canada-url",
                url + "/ca",
                "--australia-url",
                url + "/au",
            ]
        )
        == 1
    )
    assert ca.read_bytes() == before
    with pytest.raises(URLError):
        producer.download(url + "/ca")
    with pytest.raises(ValueError, match="byte limit"):
        producer.download(url + "/ca", ca_file=ca, max_bytes=10)
    for timeout, limit in [(0, 100), (float("inf"), 100), (1, 0)]:
        with pytest.raises(ValueError, match="limits"):
            producer.download(url + "/ca", timeout=timeout, max_bytes=limit)
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
