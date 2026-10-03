# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — taxonomy source transport conformance

"""Check complete saved source sets through real TLS, registration and PDF tools."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import shutil
import socket
import ssl
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/taxonomy_audit/check_sources.py"
SNAPSHOT = SCRIPT.with_name("input-taxonomy-snapshot.tsv")
ADDITIONAL = SCRIPT.with_name("additional_sources.json")
SAVED = SCRIPT.with_name("url_checks.json")
DATE = "2026-09-30"


def taxonomy_pdf(*, empty: bool = False) -> bytes:
    """Serialize all real snapshot identities as a valid five-page PDF report."""
    rows = read_table(SNAPSHOT)[1]
    pages = [rows[start : start + 25] for start in range(0, len(rows), 25)]
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for page in pages:
        text = [
            "Taxonomy snapshot: 123 historical entries",
            *[row["id"] + " " + row["name"] for row in page],
        ]
        commands = ["BT /F1 9 Tf 20 770 Td"]
        for line in [] if empty else text:
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"({escaped}) Tj 0 -12 Td")
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1", errors="replace")
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {len(objects) + 2} 0 R >>".encode()
        )
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    children = " ".join(f"{index} 0 R" for index in range(4, len(objects) + 1, 2))
    objects[1] = f"<< /Type /Pages /Count {len(pages)} /Kids [{children}] >>".encode()
    document = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(document))
        document.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    start = len(document)
    document.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode())
    document.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode()
    )
    return bytes(document)


class TaxonomyServer(ThreadingHTTPServer):
    """Serve saved work identities and PDF reports over a real TLS socket."""

    pdf: bytes
    empty_pdf: bytes
    registrations: dict[str, str]


class SourceHandler(BaseHTTPRequestHandler):
    """Expose genuine response, redirect, body failure and registration cases."""

    def do_GET(self) -> None:
        server = self.server
        assert isinstance(server, TaxonomyServer)
        path = unquote(urlsplit(self.path).path)
        if path == "/stall":
            self.send_response(200)
            self.send_header("Content-Length", "100")
            self.end_headers()
            time.sleep(0.3)
            self.close_connection = True
            return
        if path == "/drop" or path.startswith("/drop/"):
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        if path in {"/redirect", "/downgrade", "/loop", "/no-location", "/credential-redirect"}:
            self.send_response(302)
            locations = {
                "/redirect": "/html",
                "/downgrade": "http://127.0.0.1:9/",
                "/loop": "/loop",
                "/credential-redirect": "https://person@localhost/",
            }
            if path in locations:
                self.send_header("Location", locations[path])
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        status, content_type = 200, "text/html"
        body = b"<title>  Source\n identity  </title><p>Access is not scientific approval.</p>"
        if path == "/pdf":
            body, content_type = server.pdf, "application/pdf"
        elif path == "/empty-pdf":
            body, content_type = server.empty_pdf, "application/pdf"
        elif path == "/bad-pdf":
            body, content_type = server.pdf[:100], "application/pdf"
        elif path == "/large":
            body = body + b"x" * 65536
        elif path == "/plain":
            body = b"No title available"
        elif path == "/empty":
            body = b""
        elif path == "/barrier":
            status, body = 403, b"<title>Captcha</title>"
        elif path.startswith("/doi/"):
            doi = path.split("/", 3)[3]
            body = f"<title>{html.escape(server.registrations.get(doi, doi))}</title>".encode()
        elif path.startswith("/works/"):
            _, _, case, doi = path.split("/", 3)
            title = server.registrations.get(doi)
            message: dict[str, object] = {"DOI": doi, "title": [title] if title else []}
            document: object = {"message": message}
            if case == "saved" and title is None:
                status = 404
            elif case == "status":
                status = 503
            elif case == "root":
                document = []
            elif case == "message":
                document = {"message": []}
            elif case == "identity":
                message["DOI"] = "another-work"
            elif case == "identity-type":
                message["DOI"] = 42
            elif case == "title":
                message["title"] = title
            elif case == "empty-title":
                message["title"] = []
            elif case == "blank-title":
                message["title"] = [" "]
            elif case == "numeric-title":
                message["title"] = [7]
            elif case == "large":
                message["padding"] = "x" * 65536
            body = b"{" if case == "json" else json.dumps(document).encode()
            content_type = "application/json"
        elif path.startswith("/source/"):
            index = int(path.rsplit("/", 1)[1])
            if index % 4 == 0:
                body, content_type = server.pdf, "application/pdf"
            elif index % 4 == 1:
                status = 404
            elif index % 4 == 2:
                body = b"Untitled response"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Keep fixture TLS traffic out of test summaries."""


@pytest.fixture(scope="module")
def https_sources(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[str, Path]]:
    directory = tmp_path_factory.mktemp("taxonomy-https")
    certificate, key = directory / "certificate.pem", directory / "key.pem"
    openssl = shutil.which("openssl")
    assert openssl is not None
    subprocess.run(
        [
            openssl,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost,IP:127.0.0.1",
            "-keyout",
            str(key),
            "-out",
            str(certificate),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    server = TaxonomyServer(("127.0.0.1", 0), SourceHandler)
    server.daemon_threads = True
    server.pdf, server.empty_pdf = taxonomy_pdf(), taxonomy_pdf(empty=True)
    server.registrations = {
        record["url"].split("doi.org/", 1)[1]: record["registered_title"]
        for record in json.loads(SAVED.read_text())["records"]
        if record.get("doi_registered") is True
    }
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certificate, key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    previous = os.environ.get("NO_PROXY")
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    try:
        yield f"https://localhost:{server.server_port}", certificate
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        if previous is None:
            os.environ.pop("NO_PROXY", None)
        else:
            os.environ["NO_PROXY"] = previous


def service_catalogue(directory: Path, base: str) -> tuple[Path, Path, dict[str, str]]:
    """Map the full real snapshot and replacements to distinct genuine TLS routes."""
    fields, rows = read_table(SNAPSHOT)
    additional = json.loads(ADDITIONAL.read_text())
    original = sorted(
        {url for row in rows for url in row["source_urls"].split(" | ")}
        | set(additional["records"])
    )
    mapping = {
        url: base + "/doi/saved/" + url.split("doi.org/", 1)[1]
        if url.startswith("https://doi.org/")
        else f"{base}/source/{index}?original={index}"
        for index, url in enumerate(original)
    }
    for row in rows:
        row["source_urls"] = " | ".join(mapping[url] for url in row["source_urls"].split(" | "))
    additional["records"] = [mapping[url] for url in additional["records"]]
    snapshot, supplement = directory / "snapshot.tsv", directory / "additional.json"
    write_table(snapshot, fields, rows)
    supplement.write_text(json.dumps(additional))
    return snapshot, supplement, mapping


def test_complete_snapshot_native_cli_and_audit_consumer(
    https_sources: tuple[str, Path], tmp_path: Path
) -> None:
    base, certificate = https_sources
    snapshot, additional, mapping = service_catalogue(tmp_path, base)
    original_paths = [
        SNAPSHOT,
        ADDITIONAL,
        SAVED,
        SCRIPT.with_name("sources.tsv"),
        SCRIPT.with_name("audit.tsv"),
    ]
    before = {path: path.read_bytes() for path in original_paths}
    for optimized in (False, True):
        output = tmp_path / f"output-{optimized}"
        result = run_cli(
            SCRIPT,
            "--input",
            str(snapshot),
            "--additional",
            str(additional),
            "--output-directory",
            str(output),
            "--ca-certificate",
            str(certificate),
            "--doi-origin",
            base + "/doi/saved",
            "--crossref-base",
            base + "/works/saved",
            "--checked-on",
            DATE,
            optimize=optimized,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        document = json.loads((output / "url_checks.json").read_text())
        assert document["schema_version"] == "1.0.0" and document["record_count"] == 68
        assert [row["url"] for row in document["records"]] == sorted(mapping.values())
        assert {row["checked_date"] for row in document["records"]} == {DATE}
        assert {row["access"] for row in document["records"]} == {
            "pdf-extracted",
            "http-error-or-access-barrier",
            "html-response-not-fulltext-verified",
        }
        assert (
            read_table(output / "sources.tsv")[0] == read_table(SCRIPT.with_name("sources.tsv"))[0]
        )
        assert len(read_table(output / "sources.tsv")[1]) == 68
        assert sum(row.get("doi_registered") is True for row in document["records"]) == 21
        audit = tmp_path / f"audit-{optimized}"
        consumer = run_cli(
            SCRIPT.with_name("build_audit.py"),
            "--input",
            str(snapshot),
            "--checks",
            str(output / "url_checks.json"),
            "--output-directory",
            str(audit),
            optimize=optimized,
        )
        assert consumer.returncode == 0, consumer.stdout + consumer.stderr
        assert len(read_table(audit / "audit.tsv")[1]) == 123
        assert (
            json.loads((audit / "summary.json").read_text())[
                "checked_sources_including_replacements"
            ]
            == 68
        )
    assert all(path.read_bytes() == value for path, value in before.items())


@pytest.mark.parametrize(
    "route,access",
    [
        ("/redirect", "html-response-not-fulltext-verified"),
        ("/downgrade", "request-failed"),
        ("/loop", "request-failed"),
        ("/no-location", "request-failed"),
        ("/credential-redirect", "request-failed"),
        ("/stall", "request-failed"),
        ("/drop", "request-failed"),
        ("/barrier", "http-error-or-access-barrier"),
        ("/plain", "html-response-not-fulltext-verified"),
        ("/empty", "html-response-not-fulltext-verified"),
        ("/large", "response-body-limit-exceeded"),
    ],
)
def test_genuine_redirect_read_and_access_observations(
    https_sources: tuple[str, Path], route: str, access: str
) -> None:
    base, certificate = https_sources
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_taxonomy_source_checker")
    config = module.CheckConfig(
        ca_certificate=certificate, timeout=0.1 if route == "/stall" else 3, max_bytes=4096
    )
    record = module.check(base + route, config)
    assert record["access"] == access
    if route == "/redirect":
        assert record["title"] == "Source identity" and record["final_url"] == base + "/html"
    if route == "/barrier":
        assert record["status"] == 403 and record["title"] == "Captcha"
    if access in {"request-failed", "response-body-limit-exceeded"}:
        assert record["title"] == "" and record["error"]
        assert "person@" not in record["error"]


def test_real_certificate_failure_and_refused_socket(https_sources: tuple[str, Path]) -> None:
    base, certificate = https_sources
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_taxonomy_source_checker")
    assert module.check(base + "/html")["access"] == "request-failed"
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    record = module.check(
        f"https://localhost:{port}/", module.CheckConfig(ca_certificate=certificate, timeout=1)
    )
    assert record["access"] == "request-failed" and record["status"] == ""


@pytest.mark.parametrize(
    "failure", ["success", "disabled", "invalid", "empty", "timeout", "missing"]
)
def test_real_pdf_extraction_and_native_failure_results(
    https_sources: tuple[str, Path], tmp_path: Path, failure: str
) -> None:
    base, certificate = https_sources
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_taxonomy_source_checker")
    executable = shutil.which("pdftotext")
    assert executable is not None
    config = module.CheckConfig(
        ca_certificate=certificate,
        pdf_executable=None
        if failure == "disabled"
        else str(tmp_path / "missing-pdftotext")
        if failure == "missing"
        else executable,
        pdf_timeout=1e-9 if failure == "timeout" else 5,
    )
    route = "/bad-pdf" if failure == "invalid" else "/empty-pdf" if failure == "empty" else "/pdf"
    record = module.check(base + route, config)
    assert record["status"] == 200
    assert record["access"] == (
        "pdf-extracted" if failure == "success" else "pdf-response-text-unavailable"
    )
    if failure == "success":
        assert (
            "Taxonomy snapshot: 123 historical entries" in record["title"]
            and "pwr" in record["title"]
        )
        assert len(record["title"]) <= 700
    else:
        assert record["title"] == ""


@pytest.mark.parametrize(
    "case",
    [
        "json",
        "root",
        "message",
        "identity",
        "identity-type",
        "title",
        "empty-title",
        "blank-title",
        "numeric-title",
        "status",
        "large",
    ],
)
def test_registration_requires_matching_work_and_nonempty_titles(
    https_sources: tuple[str, Path], case: str
) -> None:
    base, certificate = https_sources
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_taxonomy_source_checker")
    doi = "10.1063/5.0206222"
    config = module.CheckConfig(
        ca_certificate=certificate,
        doi_origin=base + "/doi/" + case,
        crossref_base=base + "/works/" + case,
        max_bytes=4096,
    )
    record = module.check(base + "/doi/" + case + "/" + doi, config)
    assert (
        record["access"] == "html-response-not-fulltext-verified"
        and record["doi_registered"] is False
    )
    assert "registered_title" not in record


def test_registration_transport_failure_and_doi_substring_are_not_identity(
    https_sources: tuple[str, Path],
) -> None:
    base, certificate = https_sources
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_taxonomy_source_checker")
    config = module.CheckConfig(
        ca_certificate=certificate, doi_origin=base + "/doi/saved", crossref_base=base + "/drop"
    )
    record = module.check(base + "/doi/saved/10.1063/5.0206222", config)
    assert (
        record["doi_registered"] is False
        and record["access"] == "html-response-not-fulltext-verified"
    )
    record = module.check(base + "/html?unrelated=doi.org/10.1063/5.0206222", config)
    assert "doi_registered" not in record


def test_doi_host_case_query_and_fragment_do_not_change_work_identity(
    https_sources: tuple[str, Path],
) -> None:
    base, certificate = https_sources
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_taxonomy_source_checker")
    config = module.CheckConfig(
        ca_certificate=certificate,
        doi_origin=base + "/doi/saved",
        crossref_base=base + "/works/saved",
    )
    url = (
        base.replace("localhost", "LOCALHOST")
        + "/doi/saved/10.1063%2F5.0206222?access=public#section"
    )
    record = module.check(url, config)
    expected = next(
        row["registered_title"]
        for row in json.loads(SAVED.read_text())["records"]
        if row["url"] == "https://doi.org/10.1063/5.0206222"
    )
    assert record["doi_registered"] is True and record["registered_title"] == expected


@pytest.mark.parametrize(
    "damage",
    [
        "header",
        "no_header",
        "empty",
        "short",
        "extra",
        "quote",
        "utf8",
        "missing",
        "http",
        "hostname",
        "brackets",
        "port",
        "zero_port",
        "userinfo",
        "password",
        "whitespace",
        "blank",
    ],
)
def test_bad_actual_snapshot_refuses_before_transfer_and_preserves_outputs(
    tmp_path: Path, damage: str
) -> None:
    path = tmp_path / "snapshot.tsv"
    fields, rows = read_table(SNAPSHOT)
    if damage == "header":
        fields.reverse()
    elif damage == "empty":
        rows.clear()
    elif damage in {
        "http",
        "hostname",
        "brackets",
        "port",
        "zero_port",
        "userinfo",
        "password",
        "whitespace",
        "blank",
    }:
        rows[0]["source_urls"] = {
            "http": "http://localhost/",
            "hostname": "https:///missing",
            "brackets": "https://[",
            "port": "https://localhost:invalid/",
            "zero_port": "https://localhost:0/",
            "userinfo": "https://person@localhost/",
            "password": "https://:untrusted@localhost/",
            "whitespace": "https://localhost/a b",
            "blank": "",
        }[damage]
    write_table(path, fields, rows)
    if damage == "no_header":
        path.write_text("")
    elif damage == "short":
        path.write_text("\t".join(fields) + "\nonly-id\n")
    elif damage == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif damage == "quote":
        path.write_text("\t".join(fields) + '\n"unclosed')
    elif damage == "utf8":
        path.write_bytes(b"\xff")
    elif damage == "missing":
        path.unlink()
    output = tmp_path / "output"
    output.mkdir()
    for name in ("url_checks.json", "sources.tsv"):
        shutil.copy2(SCRIPT.with_name(name), output / name)
    before = {file: file.read_bytes() for file in output.iterdir()}
    result = run_cli(SCRIPT, "--input", str(path), "--output-directory", str(output), optimize=True)
    assert result.returncode == 1 and "CHECK FAILED" in result.stdout
    assert "Traceback" not in result.stderr and "untrusted" not in result.stdout + result.stderr
    assert all(file.read_bytes() == value for file, value in before.items())


@pytest.mark.parametrize(
    "damage",
    [
        "version",
        "keys",
        "count",
        "bool_count",
        "records_type",
        "root",
        "record_type",
        "record_url",
        "json",
        "utf8",
        "missing",
    ],
)
def test_bad_full_supplementary_envelope_refuses_before_network(
    tmp_path: Path, damage: str
) -> None:
    document = json.loads(ADDITIONAL.read_text())
    if damage == "version":
        document["schema_version"] = "2.0.0"
    elif damage == "keys":
        document["extra"] = "unexpected"
    elif damage == "count":
        document["record_count"] -= 1
    elif damage == "bool_count":
        document["record_count"] = True
    elif damage == "records_type":
        document["records"] = {}
    elif damage == "root":
        document = None
    elif damage == "record_type":
        document["records"][0] = 7
    elif damage == "record_url":
        document["records"][0] = "file:///not-a-source"
    path = tmp_path / "additional.json"
    path.write_text(json.dumps(document))
    if damage == "json":
        path.write_text("{")
    elif damage == "utf8":
        path.write_bytes(b"\xff")
    elif damage == "missing":
        path.unlink()
    output = tmp_path / "output"
    result = run_cli(SCRIPT, "--additional", str(path), "--output-directory", str(output))
    assert result.returncode == 1 and "CHECK FAILED" in result.stdout
    assert not output.exists() and "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "option,value",
    [
        ("--timeout", "0"),
        ("--timeout", "nan"),
        ("--timeout", "inf"),
        ("--pdf-timeout", "-1"),
        ("--max-bytes", "0"),
        ("--max-bytes", "-1"),
        ("--checked-on", "2026-02-30"),
        ("--checked-on", "20260930"),
        ("--doi-origin", "http://localhost/"),
        ("--crossref-base", "http://localhost/"),
        ("--doi-origin", "https://localhost/?unexpected=1"),
        ("--crossref-base", "https://localhost/#section"),
    ],
)
def test_bad_transfer_configuration_refuses_before_network(
    tmp_path: Path, option: str, value: str
) -> None:
    output = tmp_path / "output"
    result = run_cli(SCRIPT, option, value, "--output-directory", str(output))
    assert result.returncode == 1 and "CHECK FAILED" in result.stdout
    assert not output.exists() and "Traceback" not in result.stderr


@pytest.mark.parametrize("name", ["url_checks.json", "sources.tsv"])
def test_maintained_snapshots_and_aliases_are_protected(tmp_path: Path, name: str) -> None:
    original = SCRIPT.with_name(name)
    before = original.read_bytes()
    (tmp_path / name).symlink_to(original)
    for directory in (tmp_path, SCRIPT.parent):
        result = run_cli(SCRIPT, "--output-directory", str(directory))
        assert result.returncode == 1 and "cannot replace" in result.stdout
    assert original.read_bytes() == before


@pytest.mark.parametrize("option,original", [("--input", SNAPSHOT), ("--additional", ADDITIONAL)])
def test_outputs_cannot_replace_custom_inputs(tmp_path: Path, option: str, original: Path) -> None:
    path = tmp_path / "url_checks.json"
    shutil.copy2(original, path)
    before = path.read_bytes()
    result = run_cli(SCRIPT, option, str(path), "--output-directory", str(tmp_path))
    assert result.returncode == 1 and "cannot replace" in result.stdout
    assert path.read_bytes() == before


@pytest.mark.parametrize("failure", ["directory", "json", "tsv"])
def test_real_output_io_failure_is_controlled(
    https_sources: tuple[str, Path], tmp_path: Path, failure: str
) -> None:
    base, certificate = https_sources
    snapshot, additional, _ = service_catalogue(tmp_path, base)
    output = tmp_path / "output"
    if failure == "directory":
        output.write_text("existing file\n")
    else:
        output.mkdir()
        (output / ("url_checks.json" if failure == "json" else "sources.tsv")).mkdir()
    result = run_cli(
        SCRIPT,
        "--input",
        str(snapshot),
        "--additional",
        str(additional),
        "--output-directory",
        str(output),
        "--ca-certificate",
        str(certificate),
        "--doi-origin",
        base + "/doi/saved",
        "--crossref-base",
        base + "/works/saved",
        "--no-pdf-text",
    )
    assert result.returncode == 1 and "CHECK FAILED" in result.stdout
    assert "Traceback" not in result.stderr


def test_public_import_collection_and_main_preserve_historical_observations(
    https_sources: tuple[str, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = [SNAPSHOT, ADDITIONAL, SAVED, SCRIPT.with_name("sources.tsv")]
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
    old_path = os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", str(tmp_path / "absent-tools"))
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_taxonomy_source_checker")
    assert module.collect_urls(SNAPSHOT, ADDITIONAL) == sorted(
        record["url"] for record in json.loads(SAVED.read_text())["records"]
    )
    assert len(module.collect_urls(SNAPSHOT)) == 56
    bare = tmp_path / "legacy.json"
    records = json.loads(ADDITIONAL.read_text())["records"]
    bare.write_text(json.dumps(records + records))
    assert len(module.collect_urls(SNAPSHOT, bare)) == 68
    with pytest.raises(ValueError, match="positive integer"):
        module.CheckConfig(max_bytes=True)
    with pytest.raises(ValueError, match="anonymous HTTPS"):
        module.check("file:///not-a-reference")
    base, certificate = https_sources
    snapshot, _additional, mapping = service_catalogue(tmp_path, base)
    output = tmp_path / "output"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--input",
            str(snapshot),
            "--no-additional",
            "--output-directory",
            str(output),
            "--ca-certificate",
            str(certificate),
            "--doi-origin",
            base + "/doi/saved",
            "--crossref-base",
            base + "/works/saved",
        ],
    )
    assert module.main() == 0
    document = json.loads((output / "url_checks.json").read_text())
    assert document["record_count"] == 56
    assert {row["checked_date"] for row in document["records"]} == {
        dt.datetime.now(dt.UTC).date().isoformat()
    }
    assert "pdf-response-text-unavailable" in {row["access"] for row in document["records"]}
    assert len(mapping) == 68
    assert all(
        (path.read_bytes(), path.stat().st_mtime_ns) == data for path, data in before.items()
    )
    monkeypatch.setenv("PATH", old_path)


def test_destination_must_be_explicit_before_any_network_work() -> None:
    result = run_cli(SCRIPT)
    assert result.returncode == 2 and "--output-directory" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("date", ["CALLER_DATE_SENTINEL", "2026-02-30"])
@pytest.mark.parametrize("optimized", [False, True])
def test_public_cli_date_refusal_is_authored_and_does_not_echo_input(
    tmp_path: Path, date: str, optimized: bool
) -> None:
    """Refuse bad dates before transfer with only the intended caller message."""
    output = tmp_path / "output"
    result = run_cli(
        SCRIPT,
        "--checked-on",
        date,
        "--output-directory",
        str(output),
        optimize=optimized,
    )
    assert result.returncode == 1
    assert result.stdout == "CHECK FAILED: observation date must use YYYY-MM-DD\n"
    assert not result.stderr and not output.exists()
    assert date not in result.stdout


@pytest.mark.parametrize("failure", ["missing-input", "utf8-input", "json-supplement"])
def test_public_cli_unanticipated_input_failure_has_fixed_text_and_preserves_reports(
    tmp_path: Path, failure: str
) -> None:
    """Keep parser details and caller paths out of real CLI output."""
    output = tmp_path / "output"
    output.mkdir()
    for name in ("url_checks.json", "sources.tsv"):
        shutil.copy2(SCRIPT.with_name(name), output / name)
    before = {path: path.read_bytes() for path in output.iterdir()}
    path = tmp_path / "CALLER_INPUT_SENTINEL"
    option = "--input"
    if failure == "utf8-input":
        path.write_bytes(b"\xff")
    elif failure == "json-supplement":
        option = "--additional"
        path.write_text('{"CALLER_JSON_SENTINEL":')
    result = run_cli(SCRIPT, option, str(path), "--output-directory", str(output), optimize=True)
    assert result.returncode == 1
    assert result.stdout == (
        "CHECK FAILED: source input or observation output is invalid or unavailable\n"
    )
    assert not result.stderr
    assert "CALLER_" not in result.stdout
    assert all(path.read_bytes() == value for path, value in before.items())


@pytest.mark.parametrize(
    "failure,error",
    [
        ("missing-pdf", "native PDF extraction unavailable"),
        ("pdf-timeout", "native PDF extraction timed out"),
        ("missing-ca", "source request failed"),
    ],
)
def test_public_observer_reports_fixed_real_native_and_transport_failures(
    https_sources: tuple[str, Path], tmp_path: Path, failure: str, error: str
) -> None:
    """Report real tool/TLS failures without echoing exception or path text."""
    base, certificate = https_sources
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_taxonomy_source_checker")
    executable = shutil.which("pdftotext")
    assert executable is not None
    config = module.CheckConfig(
        ca_certificate=tmp_path / "CALLER_CA_SENTINEL" if failure == "missing-ca" else certificate,
        pdf_executable=str(tmp_path / "CALLER_PDF_SENTINEL")
        if failure == "missing-pdf"
        else executable,
        pdf_timeout=1e-9 if failure == "pdf-timeout" else 5,
    )
    record = module.check(base + "/pdf", config)
    assert record["error"] == error and record["title"] == ""
    assert record["access"] == (
        "request-failed" if failure == "missing-ca" else "pdf-response-text-unavailable"
    )
    assert record["status"] == ("" if failure == "missing-ca" else 200)
    assert "CALLER_" not in record["error"]


def test_deliberate_public_refusals_retain_their_authored_identity(
    https_sources: tuple[str, Path],
) -> None:
    """Preserve intended HTTPS refusal text and its explicit public type."""
    base, certificate = https_sources
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_taxonomy_source_checker")
    with pytest.raises(
        module.SourceObservationRefused, match="source references must use anonymous HTTPS"
    ):
        module.check("file:///CALLER_REFUSAL_SENTINEL")
    record = module.check(
        base + "/credential-redirect", module.CheckConfig(ca_certificate=certificate)
    )
    assert record["access"] == "request-failed"
    assert record["error"] == "source references must use anonymous HTTPS"


@pytest.mark.parametrize("option", ["--timeout", "--pdf-timeout"])
@pytest.mark.parametrize("value", ["1e308", "3600.0001"])
def test_public_cli_refuses_unsupported_upper_timeouts_before_input_work(
    tmp_path: Path, option: str, value: str
) -> None:
    """Refuse unsupported finite waits before filesystem or network work."""
    output = tmp_path / "output"
    result = run_cli(
        SCRIPT,
        option,
        value,
        "--input",
        str(tmp_path / "not-read"),
        "--output-directory",
        str(output),
    )
    assert result.returncode == 1
    assert result.stdout == (
        "CHECK FAILED: timeouts must be positive, finite and at most 3600 seconds\n"
    )
    assert not result.stderr and not output.exists()


@pytest.mark.parametrize("field", ["timeout", "pdf_timeout"])
@pytest.mark.parametrize("value", [1e308, 3600.0001])
def test_public_configuration_refuses_unsupported_upper_timeouts(field: str, value: float) -> None:
    """Bound the public configuration before any source transfer is possible."""
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_taxonomy_source_checker")
    with pytest.raises(
        module.SourceObservationRefused,
        match="timeouts must be positive, finite and at most 3600 seconds",
    ):
        module.CheckConfig(**{field: value})


def test_public_configuration_accepts_the_documented_inclusive_upper_timeout() -> None:
    """Keep the exact supported endpoint usable without silently clamping it."""
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_taxonomy_source_checker")
    config = module.CheckConfig(timeout=3600, pdf_timeout=3600)
    assert config.timeout == config.pdf_timeout == module.MAX_TIMEOUT_SECONDS == 3600
