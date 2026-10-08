# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — expansion URL availability conformance

"""Exercise native curl against real certificate-verified local HTTPS responses."""

from __future__ import annotations

import datetime as dt
import os
import shutil
import signal
import socket
import ssl
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from ._catalogue_inputs import ROOT, read_table, run_cli, write_table
from .conftest import load_module

SCRIPT = ROOT / "metadata/company_audit/check_expansion_urls.py"
SOURCE = SCRIPT.with_name("expansion_candidates.tsv")
SNAPSHOT = SCRIPT.with_name("expansion_url_checks.tsv")
DATE = "2026-09-30"


class SourceHandler(BaseHTTPRequestHandler):
    """Serve actual success, access, redirect and incomplete-transfer responses."""

    def do_GET(self) -> None:
        """Serve real status, redirect, dropped-connection and incomplete-transfer controls."""
        if self.path in {"/stall", "/process-stall"}:
            self.send_response(200)
            self.send_header("Content-Length", "10")
            self.end_headers()
            time.sleep(5 if self.path == "/process-stall" else 0.3)
            self.close_connection = True
            return
        if self.path == "/drop":
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        if self.path in {"/redirect", "/downgrade"}:
            self.send_response(302)
            self.send_header(
                "Location", "/status/200" if self.path == "/redirect" else "http://127.0.0.1:9/"
            )
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        status = int(self.path.split("?", 1)[0].rsplit("/", 1)[1])
        body = b"" if status == 204 else b"source response\n"
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Keep bounded fixture traffic out of the runtime evidence stream."""


@pytest.fixture(scope="module")
def https_source(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[str, Path]]:
    """Run a module-scoped HTTPS listener with an owned, locally trusted certificate.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        Allocator for the certificate and key directory.

    Yields
    ------
    tuple[str, Path]
        Local HTTPS origin and its one-day certificate for native curl.

    Notes
    -----
    Close the listener, join its worker and restore the original NO_PROXY value.
    """
    directory = tmp_path_factory.mktemp("https-source")
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
    server = ThreadingHTTPServer(("127.0.0.1", 0), SourceHandler)
    server.daemon_threads = True
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


def service_catalogue(directory: Path, base: str) -> tuple[Path, dict[str, set[str]]]:
    """Map every recorded source link to a real local HTTP status control.

    Parameters
    ----------
    directory : Path
        Owned destination for the complete expansion table copy.
    base : str
        Origin of the trusted local HTTPS listener.

    Returns
    -------
    tuple[Path, dict[str, set[str]]]
        Copied table path and every distinct local URL's official or independent roles.
    """
    fields, rows = read_table(SOURCE)
    original = sorted(
        {
            value.strip()
            for row in rows
            for field in ("official_url", "independent_urls")
            for value in row[field].split(";")
        }
    )
    statuses = [200, 204, 301, 401, 403, 406, 429, 404, 500]
    mapping = {
        url: f"{base}/status/{statuses[index % len(statuses)]}?source={index}"
        for index, url in enumerate(original)
    }
    references: dict[str, set[str]] = {}
    for row in rows:
        for field, role in (("official_url", "official_url"), ("independent_urls", "independent")):
            links = [mapping[value.strip()] for value in row[field].split(";")]
            row[field] = ";".join(links)
            for url in links:
                references.setdefault(url, set()).add(role)
    path = directory / "expansion.tsv"
    write_table(path, fields, rows)
    return path, references


def test_native_cli_checks_all_actual_links_once(
    https_source: tuple[str, Path], tmp_path: Path
) -> None:
    """Check every distinct recorded link with exact status, roles and dates in both CLI modes."""
    base, certificate = https_source
    source, references = service_catalogue(tmp_path, base)
    output = tmp_path / "checks.tsv"
    before = {path: path.read_bytes() for path in [SOURCE, SNAPSHOT]}
    for optimized in (False, True):
        result = run_cli(
            SCRIPT,
            "--input",
            str(source),
            "--output",
            str(output),
            "--ca-certificate",
            str(certificate),
            "--checked-on",
            DATE,
            optimize=optimized,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        fields, rows = read_table(output)
        assert fields == read_table(SNAPSHOT)[0]
        assert [row["url"] for row in rows] == sorted(references)
        assert len(rows) == len(references)
        for row in rows:
            status = row["url"].split("/status/", 1)[1].split("?", 1)[0]
            assert row["http_status"] == status
            assert row["roles"] == ";".join(sorted(references[row["url"]]))
            assert row["reachable_or_access_controlled"] == (
                "no" if status in {"404", "500"} else "yes"
            )
            assert row["checked_on"] == DATE
        assert "unacceptable results:" in result.stdout and "404" in result.stdout
    assert all(path.read_bytes() == data for path, data in before.items())


@pytest.mark.parametrize(
    "route,trust,status,reachable",
    [
        ("/redirect", True, "200", "yes"),
        ("/downgrade", True, "302", "no"),
        ("/stall", True, "200", "no"),
        ("/drop", True, "000", "no"),
        ("/status/200", False, "000", "no"),
    ],
)
def test_real_tls_redirect_and_transfer_failures_do_not_claim_reachability(
    https_source: tuple[str, Path], route: str, trust: bool, status: str, reachable: str
) -> None:
    """Distinguish successful TLS redirects from downgrade, timeout, disconnect and trust failures."""
    base, certificate = https_source
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_expansion_url_checker")
    curl = shutil.which("curl")
    assert curl is not None
    row = module.check_url(
        base + route,
        {"official_url"},
        curl,
        timeout=0.1 if route == "/stall" else 3,
        checked_on=DATE,
        ca_certificate=certificate if trust else None,
    )
    assert row["http_status"] == status and row["reachable_or_access_controlled"] == reachable


def test_real_connection_refusal_and_missing_executable(
    https_source: tuple[str, Path], tmp_path: Path
) -> None:
    """Record unavailable endpoints and missing curl as unreachable with status 000."""
    base, certificate = https_source
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_expansion_url_checker")
    curl = shutil.which("curl")
    assert curl is not None
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    for url, executable in [
        (f"https://localhost:{port}/", curl),
        (base + "/status/200", str(tmp_path / "missing-curl")),
    ]:
        row = module.check_url(
            url, {"independent"}, executable, timeout=1, checked_on=DATE, ca_certificate=certificate
        )
        assert row["http_status"] == "000" and row["reachable_or_access_controlled"] == "no"


@pytest.mark.parametrize(
    "damage",
    [
        "header",
        "empty",
        "short",
        "extra",
        "quote",
        "utf8",
        "missing",
        "http",
        "no_host",
        "brackets",
        "userinfo",
        "password",
        "whitespace",
        "blank",
    ],
)
def test_bad_recorded_reference_preserves_existing_snapshot(tmp_path: Path, damage: str) -> None:
    """Reject malformed source tables and unsafe URLs without replacing the accepted snapshot."""
    path = tmp_path / "source.tsv"
    fields, rows = read_table(SOURCE)
    if damage == "header":
        fields.reverse()
    elif damage == "empty":
        rows.clear()
    elif damage in {"http", "no_host", "brackets", "userinfo", "password", "whitespace", "blank"}:
        rows[0]["official_url"] = {
            "http": "http://localhost/",
            "no_host": "https:///absent",
            "brackets": "https://[",
            "userinfo": "https://person@localhost/",
            "password": "https://:untrusted@localhost/",
            "whitespace": "https://localhost/a b",
            "blank": "",
        }[damage]
    write_table(path, fields, rows)
    if damage == "short":
        path.write_text("\t".join(fields) + "\nonly-name\n")
    elif damage == "extra":
        path.write_text(path.read_text() + "\t".join(rows[0].values()) + "\textra\n")
    elif damage == "quote":
        path.write_text("\t".join(fields) + '\n"unclosed')
    elif damage == "utf8":
        path.write_bytes(b"\xff")
    elif damage == "missing":
        path.unlink()
    output = tmp_path / "checks.tsv"
    shutil.copy2(SNAPSHOT, output)
    before = output.read_bytes()
    result = run_cli(SCRIPT, "--input", str(path), "--output", str(output))
    assert result.returncode == 1 and "CHECK FAILED" in result.stdout
    assert "Traceback" not in result.stderr and output.read_bytes() == before
    assert "untrusted" not in result.stdout + result.stderr


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf"])
def test_invalid_transfer_limit_refuses_before_network(tmp_path: Path, timeout: str) -> None:
    """Reject nonpositive or non-finite CLI transfer limits before creating output."""
    result = run_cli(SCRIPT, "--timeout", timeout, "--output", str(tmp_path / "checks.tsv"))
    assert result.returncode == 2 and "positive and finite" in result.stderr
    assert not (tmp_path / "checks.tsv").exists()


@pytest.mark.parametrize("date", ["2026-02-30", "20260930"])
def test_invalid_snapshot_date_refuses_before_network(tmp_path: Path, date: str) -> None:
    """Reject malformed calendar dates without a traceback or output snapshot."""
    result = run_cli(SCRIPT, "--checked-on", date, "--output", str(tmp_path / "checks.tsv"))
    assert result.returncode == 1 and "CHECK FAILED" in result.stdout
    assert "Traceback" not in result.stderr and not (tmp_path / "checks.tsv").exists()


def test_output_cannot_replace_source(tmp_path: Path) -> None:
    """Refuse output aliasing the expansion input and preserve its exact bytes."""
    path = tmp_path / "source.tsv"
    shutil.copy2(SOURCE, path)
    before = path.read_bytes()
    result = run_cli(SCRIPT, "--input", str(path), "--output", str(path))
    assert result.returncode == 1 and "replace expansion input" in result.stdout
    assert path.read_bytes() == before


def test_missing_native_curl_is_controlled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Report absent native curl without creating an output snapshot."""
    monkeypatch.setenv("PATH", str(tmp_path / "no-tools"))
    result = run_cli(SCRIPT, "--output", str(tmp_path / "checks.tsv"))
    assert result.returncode == 1 and "curl not found on PATH" in result.stdout
    assert not (tmp_path / "checks.tsv").exists()


def test_public_url_check_refuses_unsafe_reference_without_transfer() -> None:
    """Reject a file URL through the public checker before invoking native curl."""
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_expansion_url_checker")
    curl = shutil.which("curl")
    assert curl is not None
    with pytest.raises(ValueError, match="anonymous HTTPS"):
        module.check_url("file:///not-a-source", {"official_url"}, curl, timeout=1, checked_on=DATE)


def test_import_collection_and_public_main_use_real_tls_without_touching_saved_snapshot(
    https_source: tuple[str, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Collect recorded links and run main over real TLS while preserving saved bytes and mtimes."""
    paths = [SOURCE, SNAPSHOT]
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
    original_path = os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", str(tmp_path / "no-tools"))
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_expansion_url_checker")
    recorded = module.collect_urls(SOURCE)
    saved = {row["url"]: set(row["roles"].split(";")) for row in read_table(SNAPSHOT)[1]}
    assert recorded == saved
    assert all(
        (path.read_bytes(), path.stat().st_mtime_ns) == data for path, data in before.items()
    )
    monkeypatch.setenv("PATH", original_path)
    base, certificate = https_source
    source, references = service_catalogue(tmp_path, base)
    output = tmp_path / "checks.tsv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--input",
            str(source),
            "--output",
            str(output),
            "--ca-certificate",
            str(certificate),
        ],
    )
    module.main()
    rows = read_table(output)[1]
    assert len(rows) == len(references)
    assert {row["checked_on"] for row in rows} == {dt.datetime.now(dt.UTC).date().isoformat()}
    assert all(
        (path.read_bytes(), path.stat().st_mtime_ns) == data for path, data in before.items()
    )


def test_output_io_failure_after_real_transfer_is_controlled(
    https_source: tuple[str, Path], tmp_path: Path
) -> None:
    """Report failed output writing after native transfer without populating the directory target."""
    base, certificate = https_source
    source, _references = service_catalogue(tmp_path, base)
    output = tmp_path / "checks.tsv"
    output.mkdir()
    result = run_cli(
        SCRIPT,
        "--input",
        str(source),
        "--output",
        str(output),
        "--ca-certificate",
        str(certificate),
    )
    assert result.returncode == 1 and "CHECK FAILED" in result.stdout
    assert "Traceback" not in result.stderr and not list(output.iterdir())


def test_public_curl_arguments_preserve_literal_shell_characters(
    https_source: tuple[str, Path], tmp_path: Path
) -> None:
    """Pass shell metacharacters literally to curl without executing their apparent command."""
    base, certificate = https_source
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_expansion_url_checker")
    curl = shutil.which("curl")
    assert curl is not None
    marker = tmp_path / "must-not-be-created-by-a-shell"
    url = f"{base}/status/200?note=;echo>{marker}"
    before = {path: path.read_bytes() for path in (SOURCE, SNAPSHOT)}
    row = module.check_url(
        url,
        {"official_url"},
        curl,
        timeout=3,
        checked_on=DATE,
        ca_certificate=certificate,
    )
    assert row["url"] == url
    assert row["http_status"] == "200"
    assert row["reachable_or_access_controlled"] == "yes"
    assert not marker.exists()
    assert all(path.read_bytes() == data for path, data in before.items())


@pytest.mark.parametrize("timeout", [0.0, -1.0, float("nan"), float("inf"), 1e308, 3600.0001])
def test_public_transfer_limit_refuses_before_process_creation(
    tmp_path: Path, timeout: float
) -> None:
    """Reject invalid or unsupported public timeouts before starting a process or writing files."""
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_expansion_url_checker")
    with pytest.raises(ValueError, match="positive and finite"):
        module.check_url(
            "https://localhost/not-transferred",
            {"official_url"},
            str(tmp_path / "not-a-program"),
            timeout=timeout,
            checked_on=DATE,
        )
    assert list(tmp_path.iterdir()) == []


def test_stopped_native_curl_is_killed_and_reaped_at_process_deadline(
    https_source: tuple[str, Path],
) -> None:
    """Kill and reap the observed stopped curl child at the operating-system deadline."""
    base, certificate = https_source
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_expansion_url_checker")
    curl = shutil.which("curl")
    assert curl is not None
    url = base + "/process-stall"
    results: list[dict[str, str]] = []
    errors: list[Exception] = []

    def transfer() -> None:
        """Collect the native curl result or exception for the worker-thread deadline assertion."""
        try:
            results.append(
                module.check_url(
                    url,
                    {"official_url"},
                    curl,
                    timeout=3,
                    checked_on=DATE,
                    ca_certificate=certificate,
                )
            )
        except Exception as error:
            errors.append(error)

    worker = threading.Thread(target=transfer, daemon=True)

    def owned_curl_child() -> int | None:
        """Identify only this worker's curl child using its executable and exact URL argument.

        Returns
        -------
        int or None
            Matching child PID, or no child when the worker or process has disappeared.
        """
        try:
            children = Path(f"/proc/self/task/{worker.native_id}/children").read_text().split()
        except FileNotFoundError:
            return None
        for child in children:
            proc = Path("/proc") / child
            try:
                if (proc / "exe").resolve(strict=True) == Path(curl).resolve() and url.encode() in (
                    proc / "cmdline"
                ).read_bytes().split(b"\0"):
                    return int(child)
            except (FileNotFoundError, ProcessLookupError):
                continue
        return None

    worker.start()
    try:
        deadline = time.monotonic() + 2
        child = owned_curl_child()
        while child is None and time.monotonic() < deadline:
            time.sleep(0.002)
            child = owned_curl_child()
        assert child is not None, "the owned native curl process was not observed"
        os.kill(child, signal.SIGSTOP)
        worker.join(timeout=6)
        assert not worker.is_alive(), "the OS-side curl deadline did not terminate the process"
        assert errors == []
        assert len(results) == 1
        assert results[0]["url"] == url
        assert results[0]["http_status"] == "000"
        assert results[0]["reachable_or_access_controlled"] == "no"
        assert owned_curl_child() is None
    finally:
        if worker.is_alive():
            remaining = owned_curl_child()
            if remaining is not None:
                try:
                    os.kill(remaining, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        worker.join(timeout=3)


@pytest.mark.parametrize("timeout", ["1e308", "3600.0001"])
def test_public_cli_oversized_timeout_refuses_before_source_or_output_work(
    tmp_path: Path, timeout: str
) -> None:
    """Refuse unsupported finite waits before reading input or starting curl."""
    output = tmp_path / "checks.tsv"
    shutil.copy2(SNAPSHOT, output)
    before = output.read_bytes()
    result = run_cli(
        SCRIPT,
        "--input",
        str(tmp_path / "not-read"),
        "--output",
        str(output),
        "--timeout",
        timeout,
    )
    assert result.returncode == 2
    assert "timeout must be positive and finite and at most 3600 seconds" in result.stderr
    assert "Traceback" not in result.stderr and "OverflowError" not in result.stderr
    assert output.read_bytes() == before


def test_public_transfer_accepts_documented_upper_limit_on_native_https(
    https_source: tuple[str, Path],
) -> None:
    """Keep the inclusive supported bound usable through a real native transfer."""
    base, certificate = https_source
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_expansion_url_checker")
    curl = shutil.which("curl")
    assert curl is not None and module.MAX_TIMEOUT_SECONDS == 3600
    row = module.check_url(
        base + "/status/200",
        {"official_url"},
        curl,
        timeout=module.MAX_TIMEOUT_SECONDS,
        checked_on=DATE,
        ca_certificate=certificate,
    )
    assert row["http_status"] == "200" and row["reachable_or_access_controlled"] == "yes"
    assert row["roles"] == "official_url" and row["checked_on"] == DATE
