# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — Brazil/EPA process-specific producer conformance

"""Build all accepted Brazil/EPA process records from original source cells and read-only snapshots."""

from __future__ import annotations

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
from urllib.parse import urlsplit

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

DIRECTORY = ROOT / "05_global_reactor_map/imports/industrial_facilities/expansion_round6"
SCRIPT = DIRECTORY / "build_dataset.py"
SNAPSHOT = DIRECTORY / "selected_source_snapshot.tsv"
DATA = DIRECTORY / "industrial_facilities_round6.tsv"
FIXTURES = ROOT / "tests/data/industrial_round6"
SOURCE = FIXTURES / "br-epe-ethanol.json"
SOURCES = ("br-epe-ethanol", "br-epe-biodiesel", "br-epe-biomethane", "us-epa-lmop")


@pytest.fixture
def producer() -> ModuleType:
    return load_module(str(SCRIPT.relative_to(ROOT)), "atlas_industrial_round6_build")


def test_all_genuine_sources_equal_every_historical_cell(producer: ModuleType) -> None:
    rows = []
    manifest = read_table(DIRECTORY / "source_snapshot_manifest.tsv")[1]
    for source in SOURCES:
        rows.extend(
            producer.select_source(
                source,
                (FIXTURES / (source + ".json")).read_bytes(),
                (FIXTURES / (source + "-count.json")).read_bytes(),
            )
        )
        expected = next(r for r in manifest if r["source"] == source)
        assert producer.query_url(producer.SOURCES[source][0]) == expected["url"]
    rows.sort(key=lambda r: (r["source"], r["source_record_id"]))
    assert len(rows) == 1131 and rows == producer.read_snapshot(SNAPSHOT)
    assert producer.rows_from_snapshot(rows) == read_table(DATA)[1]
    assert producer.clean(None) == "" and producer.clean(" reported ") == "reported"
    assert "returnCountOnly=true" in producer.count_url(
        producer.query_url(producer.SOURCES[SOURCES[0]][0])
    )


def test_full_native_build_and_refresh_are_isolated(tmp_path: Path, producer: ModuleType) -> None:
    before = DATA.read_bytes(), SNAPSHOT.read_bytes()
    for optimize in (False, True):
        result = run_cli(SCRIPT, "--output", str(tmp_path / "offline.tsv"), optimize=optimize)
        assert result.returncode == 0 and (tmp_path / "offline.tsv").read_bytes() == before[0]
    args = [
        "--refresh",
        "--raw-dir",
        str(FIXTURES),
        "--date",
        "2026-09-28",
        "--snapshot",
        str(tmp_path / "snapshot.tsv"),
        "--manifest",
        str(tmp_path / "manifest.tsv"),
        "--output",
        str(tmp_path / "output.tsv"),
    ]
    result = run_cli(SCRIPT, *args)
    assert result.returncode == 0, result.stdout + result.stderr
    assert producer.main(args) == 0
    assert (tmp_path / "snapshot.tsv").read_bytes() == before[1]
    assert (tmp_path / "output.tsv").read_bytes() == before[0]
    assert len(read_table(tmp_path / "manifest.tsv")[1]) == 4
    assert before == (DATA.read_bytes(), SNAPSHOT.read_bytes())


@pytest.mark.parametrize(
    "corruption",
    [
        "count-list",
        "count-missing",
        "count-bool",
        "count-zero",
        "count-error",
        "payload-list",
        "error",
        "features-missing",
        "features-dict",
        "truncated",
        "limit",
        "sr-missing",
        "sr-wrong",
        "feature-list",
        "attributes-list",
        "geometry-list",
        "attribute-list",
        "duplicate",
        "oid-missing",
        "oid-zero",
        "oid-bool",
        "lat-missing",
        "lat-nan",
        "lon-outside",
        "geometry-missing-y",
        "geometry-nan",
        "point-mismatch",
        "capacity-inf",
        "capacity-text",
        "name-empty",
    ],
)
def test_complete_genuine_source_refusals(producer: ModuleType, corruption: str) -> None:
    payload = json.loads(SOURCE.read_text())
    count = json.loads((FIXTURES / "br-epe-ethanol-count.json").read_text())
    feature = payload["features"][0]
    if corruption == "count-list":
        count = []
    elif corruption == "count-missing":
        count = {}
    elif corruption == "count-bool":
        count["count"] = True
    elif corruption == "count-zero":
        count["count"] = 0
    elif corruption == "count-error":
        count["error"] = {"code": 400}
    elif corruption == "payload-list":
        payload = []
    elif corruption == "error":
        payload["error"] = {"code": 400}
    elif corruption == "features-missing":
        payload.pop("features")
    elif corruption == "features-dict":
        payload["features"] = {}
    elif corruption == "truncated":
        payload["features"].pop()
    elif corruption == "limit":
        payload["exceededTransferLimit"] = True
    elif corruption == "sr-missing":
        payload.pop("spatialReference")
    elif corruption == "sr-wrong":
        payload["spatialReference"]["wkid"] = 3857
    elif corruption == "feature-list":
        payload["features"][0] = []
    elif corruption == "attributes-list":
        feature["attributes"] = []
    elif corruption == "geometry-list":
        feature["geometry"] = []
    elif corruption == "attribute-list":
        feature["attributes"]["Nome"] = []
    elif corruption == "duplicate":
        payload["features"][1]["attributes"]["OBJECTID"] = feature["attributes"]["OBJECTID"]
    elif corruption == "oid-missing":
        feature["attributes"].pop("OBJECTID")
    elif corruption == "oid-zero":
        feature["attributes"]["OBJECTID"] = 0
    elif corruption == "oid-bool":
        feature["attributes"]["OBJECTID"] = True
    elif corruption == "lat-missing":
        feature["attributes"].pop("Latitude")
    elif corruption == "lat-nan":
        feature["attributes"]["Latitude"] = "NaN"
    elif corruption == "lon-outside":
        feature["attributes"]["Longitude"] = 181
    elif corruption == "geometry-missing-y":
        feature["geometry"].pop("y")
    elif corruption == "geometry-nan":
        feature["geometry"]["y"] = "NaN"
    elif corruption == "point-mismatch":
        feature["geometry"]["x"] += 1
    elif corruption == "capacity-inf":
        feature["attributes"]["Caprocmi"] = "Infinity"
    elif corruption == "capacity-text":
        feature["attributes"]["Caprocmi"] = "not numeric"
    else:
        feature["attributes"]["Nome"] = ""
    with pytest.raises(ValueError):
        producer.select_source(SOURCES[0], json.dumps(payload).encode(), json.dumps(count).encode())


@pytest.mark.parametrize(
    ("source", "field", "value"),
    [
        ("br-epe-ethanol", "country", "unknown"),
        ("br-epe-ethanol", "coordinate_basis", "unknown"),
        ("br-epe-biodiesel", "lat", "NaN"),
        ("br-epe-biomethane", "lon", "-10"),
        ("us-epa-lmop", "country", "unknown"),
        ("us-epa-lmop", "source_status", "planned"),
        ("us-epa-lmop", "coordinate_basis", "unknown"),
        ("us-epa-lmop", "source", "unknown"),
        ("us-epa-lmop", "facility_name", ""),
    ],
)
def test_full_snapshot_mutations_refuse(
    tmp_path: Path, source: str, field: str, value: str
) -> None:
    fields, rows = read_table(SNAPSHOT)
    next(r for r in rows if r["source"] == source)[field] = value
    changed = tmp_path / "changed.tsv"
    write_table(changed, fields, rows)
    result = run_cli(
        SCRIPT, "--snapshot", str(changed), "--output", str(tmp_path / "output.tsv"), optimize=True
    )
    assert (
        result.returncode == 1
        and "Traceback" not in result.stderr
        and not (tmp_path / "output.tsv").exists()
    )


def test_public_schema_and_actual_mapping_boundaries(producer: ModuleType, tmp_path: Path) -> None:
    rows = producer.read_snapshot(SNAPSHOT)
    with pytest.raises(ValueError):
        producer.rows_from_snapshot([])
    changed = json.loads(json.dumps(rows))
    changed[0]["facility_name"] = None
    with pytest.raises(ValueError):
        producer.rows_from_snapshot(changed)
    rows[1]["source_row_id"] = rows[0]["source_row_id"]
    with pytest.raises(ValueError):
        producer.rows_from_snapshot(rows)
    for invalid in ["20260928", "2026-02-30"]:
        with pytest.raises(ValueError):
            producer.rows_from_snapshot(producer.read_snapshot(SNAPSHOT), retrieved=invalid)
    feature = json.loads(SOURCE.read_text())["features"][0]
    with pytest.raises(ValueError):
        producer.epe_snapshot("unknown", feature)
    feature["attributes"]["Latitude"] = None
    with pytest.raises(ValueError):
        producer.epe_snapshot(SOURCES[0], feature)
    feature = json.loads((FIXTURES / "us-epa-lmop.json").read_text())["features"][0]
    feature["attributes"]["longitude"] = None
    with pytest.raises(ValueError):
        producer.lmop_snapshot(feature)
    with pytest.raises(ValueError):
        producer.select_source("unknown", SOURCE.read_bytes(), b"{}")
    for value in [None, "", 0, -1]:
        assert producer.positive(value) == ""
    for invalid_capacity in [True, "Infinity", "not numeric"]:
        with pytest.raises(ValueError):
            producer.positive(invalid_capacity)
    raw = {source: (FIXTURES / (source + ".json")).read_bytes() for source in SOURCES}
    counts = {source: (FIXTURES / (source + "-count.json")).read_bytes() for source in SOURCES}
    for sources, totals in [({}, counts), (raw, {})]:
        with pytest.raises(ValueError):
            producer.refresh_snapshot(
                sources,
                totals,
                snapshot=tmp_path / "s.tsv",
                manifest=tmp_path / "m.tsv",
                retrieved="2026-09-28",
            )


def test_native_cli_configuration_refuses_without_writes(
    producer: ModuleType, tmp_path: Path
) -> None:
    output = tmp_path / "out.tsv"
    for extra in [
        ["--refresh"],
        ["--raw-dir", str(FIXTURES)],
        ["--manifest", str(tmp_path / "m.tsv")],
        ["--source-url", "unknown=https://localhost/query"],
        ["--source-url", "invalid"],
        ["--source-url", "br-epe-ethanol=http://localhost/query"],
        [
            "--source-url",
            "br-epe-ethanol=https://localhost/a",
            "--source-url",
            "br-epe-ethanol=https://localhost/b",
        ],
        ["--refresh", "--snapshot", str(tmp_path / "s.tsv"), "--manifest", str(tmp_path / "s.tsv")],
        [
            "--refresh",
            "--snapshot",
            str(tmp_path / "s.tsv"),
            "--manifest",
            str(tmp_path / "m.tsv"),
            "--raw-dir",
            str(tmp_path / "missing"),
        ],
    ]:
        assert producer.main(["--output", str(output), *extra]) == 1
        assert not output.exists()
    assert run_cli(SCRIPT).returncode == 2


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


class SourceServer(ThreadingHTTPServer):
    """Serve the complete genuine UK selection over a real trusted TLS socket."""

    bodies: dict[str, bytes]


class SourceHandler(BaseHTTPRequestHandler):
    """Provide real HTTP response, redirect and timeout controls."""

    def do_GET(self) -> None:
        server = self.server
        assert isinstance(server, SourceServer)
        path = urlsplit(self.path).path
        if path in {"/redirect", "/downgrade", "/credentials", "/loop"}:
            self.send_response(302)
            target = {
                "/redirect": "/source/br-epe-ethanol",
                "/downgrade": "http://127.0.0.1/source",
                "/credentials": "https://user:secret@localhost/source",
                "/loop": "/loop",
            }[path]
            self.send_header("Location", target)
            self.end_headers()
            return
        self.send_response(201 if path == "/created" else 404 if path == "/missing" else 200)
        body = server.bodies.get(
            path + ("-count" if "returnCountOnly=true" in self.path else ""), SOURCE.read_bytes()
        )
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if path == "/stall":
            time.sleep(0.2)
        try:
            self.wfile.write(body)
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
    server.bodies = {
        "/source/" + source + suffix: (FIXTURES / (source + filename)).read_bytes()
        for source in SOURCES
        for suffix, filename in [("", ".json"), ("-count", "-count.json")]
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


def test_real_tls_complete_four_source_refresh(
    producer: ModuleType, tmp_path: Path, tls_source: tuple[str, Path]
) -> None:
    url, ca = tls_source
    assert producer.download(url + "/redirect", ca_file=ca) == SOURCE.read_bytes()
    args = [
        "--refresh",
        "--date",
        "2026-09-28",
        "--snapshot",
        str(tmp_path / "s.tsv"),
        "--manifest",
        str(tmp_path / "m.tsv"),
        "--output",
        str(tmp_path / "o.tsv"),
        "--ca-file",
        str(ca),
    ]
    for source in SOURCES:
        args.extend(["--source-url", source + "=" + url + "/source/" + source])
    result = run_cli(SCRIPT, *args)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "o.tsv").read_bytes() == DATA.read_bytes()
    assert (tmp_path / "s.tsv").read_bytes() == SNAPSHOT.read_bytes()
    before = ca.read_bytes()
    assert (
        producer.main(["--output", str(ca), "--ca-file", str(ca)]) == 1
        and ca.read_bytes() == before
    )


@pytest.mark.parametrize("source", ["br-epe-biodiesel", "br-epe-biomethane"])
def test_full_source_missing_optional_capacity_and_authorization(
    producer: ModuleType, source: str
) -> None:
    payload = json.loads((FIXTURES / (source + ".json")).read_text())
    identifier = str(payload["features"][0]["attributes"]["OBJECTID"])
    if source == "br-epe-biodiesel":
        payload["features"][0]["attributes"]["Capm3dia"] = None
        payload["features"][0]["attributes"]["Capm3ano"] = None
    else:
        payload["features"][0]["attributes"]["Autorizaca"] = None
    rows = producer.select_source(
        source, json.dumps(payload).encode(), (FIXTURES / (source + "-count.json")).read_bytes()
    )
    chosen = next(r for r in rows if r["source_row_id"] == identifier)
    assert len(rows) == (88 if source == "br-epe-biodiesel" else 70)
    if source == "br-epe-biodiesel":
        assert chosen["capacity"] == ""
        output = producer.rows_from_snapshot(rows)
        assert (
            next(r for r in output if r["stable_id"].endswith(chosen["source_record_id"]))[
                "capacity"
            ]
            == ""
        )
    else:
        assert "operation-authorization field" not in chosen["source_status"]
