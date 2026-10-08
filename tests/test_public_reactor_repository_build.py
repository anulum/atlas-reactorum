# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — public repository producer conformance

"""Exercise the complete accepted GitHub source through isolated public builds."""

from __future__ import annotations

import hashlib
import json
import shutil
import ssl
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from ._catalogue_inputs import ROOT, run_cli
from .conftest import load_module

DIRECTORY = ROOT / "metadata/anulum_github"
SCRIPT = DIRECTORY / "build_repo_catalog.py"
SOURCE = DIRECTORY / "source_snapshot.json"
PRESENTATION = ROOT / "04_interactive_presentation/data"
FIXTURE = ROOT / "tests/data/anulum_github/repositories.json"


@pytest.fixture(scope="module")
def certificate(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """Create a localhost certificate and key for real trusted HTTPS requests.

    Parameters
    ----------
    tmp_path_factory
        Pytest owner of the module-scoped TLS directory.

    Returns
    -------
    tuple[pathlib.Path, pathlib.Path]
        Certificate and private-key paths; the certificate covers DNS localhost.

    Notes
    -----
    OpenSSL is required. The fixture fails if it cannot create the certificate.
    """
    directory = tmp_path_factory.mktemp("catalogue-tls")
    cert, key = directory / "cert.pem", directory / "key.pem"
    openssl = shutil.which("openssl")
    if openssl is None:
        pytest.fail("openssl is required for real catalogue TLS tests")
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
            "subjectAltName=DNS:localhost",
            "-keyout",
            str(key),
            "-out",
            str(cert),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    return cert, key


@contextmanager
def api_server(
    certificate: tuple[Path, Path],
    routes: dict[str, tuple[int, dict[str, str], bytes, float]],
) -> Iterator[tuple[str, list[str]]]:
    """Serve selected responses over real HTTPS and reap all owned threads.

    Parameters
    ----------
    certificate
        Localhost certificate and private-key paths used by the TLS listener.
    routes
        Request-path mapping to HTTP status, headers, body bytes and delay in seconds.

    Yields
    ------
    tuple[str, list[str]]
        HTTPS repository endpoint and the mutable ordered request-path log.

    Notes
    -----
    Refusal tests may close a live connection early. Cleanup shuts down the
    listener, closes its sockets and verifies the serving thread has stopped.
    """
    requests: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            """Return the response selected by the requested real API path."""
            requests.append(self.path)
            status, headers, body, delay = routes.get(self.path, (404, {}, b"not found", 0))
            if delay:
                time.sleep(delay)
            try:
                self.send_response(status)
                for name, value in headers.items():
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError, ssl.SSLError):
                pass  # Timeout/refusal tests intentionally close the real connection.

        def log_message(self, format: str, *args: object) -> None:
            """Keep expected HTTP refusal diagnostics out of test output."""

    server = ThreadingHTTPServer(("localhost", 0), Handler)
    server.daemon_threads = False
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(*certificate)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
    thread.start()
    try:
        yield f"https://localhost:{server.server_port}/repos", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def api_body(records: object) -> bytes:
    """Encode complete source cells or an explicit malformed-response mutation.

    Parameters
    ----------
    records
        JSON-compatible API records or a selected invalid response structure.

    Returns
    -------
    bytes
        ASCII-escaped JSON response body for the real HTTPS listener.
    """
    return json.dumps(records, ensure_ascii=True).encode()


def api_records() -> list[dict[str, Any]]:
    """Reload the complete minimised real GitHub response for each test.

    Returns
    -------
    list[dict[str, typing.Any]]
        Fresh mutable source records whose consumed cells have fixture provenance.
    """
    records: list[dict[str, Any]] = json.loads(FIXTURE.read_bytes())
    return records


@pytest.fixture
def producer() -> ModuleType:
    """Load the actual catalogue producer in an isolated module namespace.

    Returns
    -------
    types.ModuleType
        Production API used by these source, output and HTTPS conformance cases.
    """
    return load_module(str(SCRIPT.relative_to(ROOT)), "atlas_public_repository_build")


def source() -> dict[str, Any]:
    """Reload all 43 captured records so mutations cannot escape their test.

    Returns
    -------
    dict[str, typing.Any]
        Fresh decoded accepted source document, including schema and record count.
    """
    value: dict[str, Any] = json.loads(SOURCE.read_bytes())
    return value


def test_complete_build_preserves_all_four_accepted_formats(
    producer: ModuleType, tmp_path: Path
) -> None:
    """All 43 source records produce 30 catalogue entries in four accepted byte-exact formats."""
    original = SOURCE.read_bytes()
    assert len(source()["records"]) == 43
    assert producer.build(source(), tmp_path, retrieved="2026-09-27") == 30
    for name in producer.OUTPUT_NAMES:
        accepted = DIRECTORY if name.startswith("reactor_") else PRESENTATION
        assert (tmp_path / name).read_bytes() == (accepted / name).read_bytes()
    assert SOURCE.read_bytes() == original


@pytest.mark.parametrize("optimize", [False, True])
def test_native_offline_build_and_validator(optimize: bool, tmp_path: Path) -> None:
    """Normal and optimised CLI builds produce TSV accepted by the actual source validator."""
    result = run_cli(SCRIPT, "--output-dir", str(tmp_path), optimize=optimize)
    assert result.returncode == 0, result.stdout + result.stderr
    result = run_cli(
        DIRECTORY / "validate.py", "--input", str(tmp_path / "reactor_repositories.tsv")
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", None),
        ("name", "invalid name"),
        ("private", True),
        ("private", 0),
        ("html_url", "https://github.com/another/repository"),
        ("url", "http://api.github.com/repos/anulum/repository"),
        ("description", 3),
        ("language", []),
        ("archived", "false"),
        ("fork", 0),
        ("license", "AGPL-3.0"),
        ("license", {"spdx_id": 3}),
        ("topics", "reactor"),
        ("topics", [1]),
        ("topics", [" "]),
        ("updated_at", None),
        ("updated_at", "2026-09-27T12:00:00"),
        ("updated_at", "not a timestamp"),
    ],
)
def test_invalid_real_source_cell_refuses_before_any_output(
    producer: ModuleType, tmp_path: Path, field: str, value: object
) -> None:
    """A malformed consumed GitHub cell raises before the candidate directory is created."""
    loaded = source()
    loaded["records"][0][field] = value
    output = tmp_path / "candidate"
    with pytest.raises((ValueError, TypeError)):
        producer.build(loaded, output, retrieved="2026-09-27")
    assert not output.exists()


@pytest.mark.parametrize(
    "corruption",
    [
        "schema",
        "count",
        "boolean-count",
        "records",
        "empty",
        "scalar",
        "record",
        "duplicate",
        "missing",
    ],
)
def test_invalid_complete_source_structure_refuses_without_writes(
    producer: ModuleType, tmp_path: Path, corruption: str
) -> None:
    """Schema, count, identity and required-repository defects refuse before output creation."""
    loaded: Any = source()
    if corruption == "schema":
        loaded["schema_version"] = "2.0.0"
    elif corruption == "count":
        loaded["record_count"] = 42
    elif corruption == "boolean-count":
        loaded["record_count"] = True
    elif corruption == "records":
        loaded["records"] = {}
    elif corruption == "empty":
        loaded = []
    elif corruption == "scalar":
        loaded = 43
    elif corruption == "record":
        loaded["records"][0] = 1
    elif corruption == "duplicate":
        loaded["records"][1] = loaded["records"][0].copy()
    else:
        loaded["records"] = [r for r in loaded["records"] if r["name"] != "scpn-fusion-core"]
        loaded["record_count"] = len(loaded["records"])
    output = tmp_path / "candidate"
    with pytest.raises(ValueError):
        producer.build(loaded, output, retrieved="2026-09-27")
    assert not output.exists()


def test_nullable_metadata_and_unicode_are_rendered_before_writes(
    producer: ModuleType, tmp_path: Path
) -> None:
    """Null metadata retains explicit absence; an unencodable description refuses before output."""
    loaded = source()
    record = next(r for r in loaded["records"] if r["name"] == "scpn-fusion-core")
    for field in ("description", "language", "license", "topics"):
        record[field] = None
    rows = producer.catalogue_rows(loaded["records"], retrieved="2026-09-27")
    row = next(r for r in rows if r["name"] == record["name"])
    assert row["description"] == "No public description provided."
    assert row["language"] == "not specified"
    assert row["license"] == "not asserted by GitHub metadata"
    assert row["topics"] == []
    record["description"] = "\ud800"
    with pytest.raises(UnicodeError):
        producer.build(loaded, tmp_path / "candidate", retrieved="2026-09-27")
    assert not (tmp_path / "candidate").exists()


@pytest.mark.parametrize("capture_date", ["20260927", "2026-02-30", "unknown"])
def test_invalid_capture_date_refuses_all_outputs(
    producer: ModuleType, tmp_path: Path, capture_date: str
) -> None:
    """Noncanonical or impossible retrieval dates cannot create a candidate directory."""
    with pytest.raises(ValueError):
        producer.build(source(), tmp_path / "candidate", retrieved=capture_date)
    assert not (tmp_path / "candidate").exists()


def test_input_and_symlink_output_guards_preserve_accepted_bytes(
    producer: ModuleType, tmp_path: Path
) -> None:
    """Output aliases and overlapping inputs refuse while preserving the accepted source bytes."""
    before = SOURCE.read_bytes()
    link = tmp_path / "accepted"
    link.symlink_to(DIRECTORY, target_is_directory=True)
    with pytest.raises(ValueError):
        producer.build(source(), link, retrieved="2026-09-27")
    output = tmp_path / "candidate"
    with pytest.raises(ValueError):
        producer.build(
            source(), output, retrieved="2026-09-27", inputs=(output / "reactor_repositories.tsv",)
        )
    assert not output.exists() and SOURCE.read_bytes() == before


def test_custom_source_requires_date_and_native_errors_are_trace_free(tmp_path: Path) -> None:
    """Custom input requires a date; malformed JSON and UTF-8 return clean CLI errors."""
    custom = tmp_path / "source.json"
    custom.write_bytes(SOURCE.read_bytes())
    output = tmp_path / "candidate"
    result = run_cli(SCRIPT, "--source", str(custom), "--output-dir", str(output))
    assert result.returncode == 1 and not output.exists()
    result = run_cli(
        SCRIPT, "--source", str(custom), "--output-dir", str(output), "--date", "2026-09-27"
    )
    assert result.returncode == 0
    for bad in (b"{", b"\xff"):
        custom.write_bytes(bad)
        result = run_cli(
            SCRIPT, "--source", str(custom), "--output-dir", str(output), "--date", "2026-09-27"
        )
        assert result.returncode == 1 and "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "options",
    [
        ["--refresh"],
        ["--snapshot-out", "candidate.json"],
        ["--api-url", "https://example.com/repos"],
        ["--ca-file", "missing.pem"],
    ],
)
def test_inconsistent_refresh_options_refuse_before_creating_output(
    tmp_path: Path, options: list[str]
) -> None:
    """Incomplete online option combinations return failure without creating output."""
    output = tmp_path / "candidate"
    result = run_cli(SCRIPT, "--output-dir", str(output), *options)
    assert result.returncode == 1 and not output.exists()


def test_atomic_output_failure_removes_only_its_own_temporary_file(
    producer: ModuleType, tmp_path: Path
) -> None:
    """An atomic write to a directory raises and preserves the unrelated file and directory."""
    destination = tmp_path / "directory"
    destination.mkdir()
    preserved = tmp_path / "preserved"
    preserved.write_bytes(b"untouched")
    with pytest.raises(OSError):
        producer.atomic_write(destination, b"real output")
    assert set(tmp_path.iterdir()) == {destination, preserved}
    assert preserved.read_bytes() == b"untouched"


def test_fixture_preserves_every_consumed_cell_and_real_exclusion(producer: ModuleType) -> None:
    """Fixture hashes bind all 43 records and consumed cells, with 13 genuine exclusions."""
    provenance = json.loads((FIXTURE.parent / "SOURCE.json").read_bytes())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == provenance["source_sha256"]
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == provenance["fixture_sha256"]
    original, records = source()["records"], api_records()
    assert len(records) == len(original) == 43
    for before, after in zip(original, records, strict=True):
        assert set(after) == set(provenance["retained_fields"])
        for field, value in after.items():
            assert value == (
                {"spdx_id": before[field]["spdx_id"]}
                if field == "license" and before[field] is not None
                else before[field]
            )
    assert len({r["name"] for r in records} - producer.RELEVANT) == 13
    assert producer.render_outputs(producer.catalogue_rows(records, retrieved="2026-09-27")) == {
        name: ((DIRECTORY if name.startswith("reactor_") else PRESENTATION) / name).read_bytes()
        for name in producer.OUTPUT_NAMES
    }


@pytest.mark.parametrize("pagination", ["single", "absolute", "relative", "other-relations"])
def test_complete_trusted_api_acquisition_and_native_online_outputs(
    producer: ModuleType, tmp_path: Path, certificate: tuple[Path, Path], pagination: str
) -> None:
    """Trusted HTTPS pagination preserves all records and builds the complete native snapshot."""
    records = api_records()
    routes: dict[str, tuple[int, dict[str, str], bytes, float]] = {
        "/repos": (200, {}, api_body(records), 0.0)
    }
    with api_server(certificate, routes) as (url, requests):
        if pagination != "single":
            next_url = "?page=2" if pagination == "relative" else url + "?page=2"
            link = f'<{next_url}>; rel="next"'
            if pagination == "other-relations":
                link = f'<{url}>; rel="prev", ' + link + f', <{url}?page=2>; rel="last"'
            routes["/repos"] = (200, {"Link": link}, api_body(records[:21]), 0.0)
            routes["/repos?page=2"] = (200, {}, api_body(records[21:]), 0.0)
        fetched = producer.fetch_repositories(url, ca_file=certificate[0])
        assert fetched == records
        expected_requests = ["/repos"] if pagination == "single" else ["/repos", "/repos?page=2"]
        assert requests == expected_requests
        output, snapshot = tmp_path / "candidate", tmp_path / "snapshot.json"
        result = run_cli(
            SCRIPT,
            "--refresh",
            "--api-url",
            url,
            "--ca-file",
            str(certificate[0]),
            "--snapshot-out",
            str(snapshot),
            "--output-dir",
            str(output),
        )
        assert result.returncode == 0, result.stdout + result.stderr
        document = json.loads(snapshot.read_bytes())
        assert document == {
            "schema_version": "1.0.0",
            "record_count": 43,
            "records": records,
            "retrieved": date.today().isoformat(),
        }
        expected = producer.render_outputs(
            producer.catalogue_rows(records, retrieved=date.today().isoformat())
        )
        assert {p.name: p.read_bytes() for p in output.iterdir()} == expected
        assert requests == expected_requests * 2


@pytest.mark.parametrize(
    "case",
    [
        "malformed",
        "multiple",
        "loop",
        "foreign-path",
        "foreign-authority",
        "fragment",
        "downgrade",
        "credentials",
        "invalid-port",
        "duplicate",
        "non-list",
        "empty",
        "bad-json",
        "201",
        "404",
        "untrusted",
        "page-limit",
        "byte-limit",
        "stall",
    ],
)
def test_real_tls_api_refusals(
    producer: ModuleType, certificate: tuple[Path, Path], case: str
) -> None:
    """Invalid API links, responses, trust and finite limits raise within the allowed request paths."""
    records = api_records()
    routes: dict[str, tuple[int, dict[str, str], bytes, float]] = {
        "/repos": (200, {}, api_body(records), 0.0)
    }
    with api_server(certificate, routes) as (url, requests):
        options: dict[str, Any] = {"ca_file": certificate[0], "timeout": 0.5}
        link_cases = {
            "malformed": "this is not a link",
            "multiple": f'<{url}?page=2>; rel="next", <{url}?page=3>; rel="next"',
            "loop": f'<{url}>; rel="next"',
            "foreign-path": f'<{url}/other>; rel="next"',
            "foreign-authority": '<https://other.invalid/repos>; rel="next"',
            "fragment": f'<{url}?page=2#part>; rel="next"',
            "downgrade": f'<{url.replace("https:", "http:")}>; rel="next"',
            "credentials": f'<{url.replace("https://", "https://user@")}>; rel="next"',
            "invalid-port": '<https://localhost:invalid/repos>; rel="next"',
        }
        if case in link_cases:
            routes["/repos"] = (200, {"Link": link_cases[case]}, api_body(records), 0.0)
        elif case in {"duplicate", "page-limit", "byte-limit"}:
            routes["/repos"] = (
                200,
                {"Link": f'<{url}?page=2>; rel="next"'},
                api_body(records[:21]),
                0.0,
            )
            routes["/repos?page=2"] = (200, {}, api_body(records[21:]), 0.0)
            if case == "duplicate":
                routes["/repos?page=2"] = (200, {}, api_body([records[0], *records[21:]]), 0.0)
            elif case == "page-limit":
                options["max_pages"] = 1
            else:
                options["max_bytes"] = len(api_body(records[:21])) + 1
        elif case in {"non-list", "empty", "bad-json"}:
            body = {"non-list": api_body(source()), "empty": b"[]", "bad-json": b"{"}[case]
            routes["/repos"] = (200, {}, body, 0.0)
        elif case in {"201", "404"}:
            routes["/repos"] = (int(case), {}, api_body(records), 0.0)
        elif case == "untrusted":
            options["ca_file"] = None
        else:
            routes["/repos"] = (200, {}, api_body(records), 0.15)
            options["timeout"] = 0.03
        with pytest.raises((ValueError, OSError)):
            producer.fetch_repositories(url, **options)
        assert all(path in {"/repos", "/repos?page=2"} for path in requests)


@pytest.mark.parametrize("target", ["accepted", "downgrade", "credentials", "loop"])
def test_real_http_redirects_are_validated_before_following(
    producer: ModuleType, certificate: tuple[Path, Path], target: str
) -> None:
    """Only the trusted redirect is followed; unsafe or looping targets refuse before a second request."""
    routes: dict[str, tuple[int, dict[str, str], bytes, float]] = {}
    with api_server(certificate, routes) as (url, requests):
        destinations = {
            "accepted": url + "?final=1",
            "downgrade": url.replace("https:", "http:"),
            "credentials": url.replace("https://", "https://user@"),
            "loop": url,
        }
        routes["/repos"] = (302, {"Location": destinations[target]}, b"", 0.0)
        routes["/repos?final=1"] = (200, {}, api_body(api_records()), 0.0)
        if target == "accepted":
            assert producer.fetch_repositories(url, ca_file=certificate[0]) == api_records()
            assert requests == ["/repos", "/repos?final=1"]
        else:
            with pytest.raises((ValueError, OSError)):
                producer.fetch_repositories(url, ca_file=certificate[0])
            assert set(requests) == {"/repos"}


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/repos",
        "https:///repos",
        "https://user@localhost/repos",
        "https://localhost:0/repos",
        "https://localhost:invalid/repos",
        "https://localhost/re pos",
    ],
)
def test_invalid_source_urls_refuse_before_network(producer: ModuleType, url: str) -> None:
    """Malformed, credential-bearing or non-HTTPS source URLs fail validation before acquisition."""
    with pytest.raises(ValueError):
        producer.fetch_repositories(url)


@pytest.mark.parametrize(
    "options",
    [
        {"timeout": 0},
        {"timeout": float("nan")},
        {"timeout": float("inf")},
        {"max_bytes": 0},
        {"max_pages": 0},
    ],
)
def test_nonpositive_or_unbounded_limits_refuse_before_network(
    producer: ModuleType, options: dict[str, int | float]
) -> None:
    """Invalid timeout, byte or page limits fail validation before acquisition."""
    with pytest.raises(ValueError):
        producer.fetch_repositories(**options)


@pytest.mark.parametrize("case", ["input", "ca", "output", "accepted", "output-symlink"])
def test_native_online_aliases_refuse_without_touching_inputs(
    certificate: tuple[Path, Path], tmp_path: Path, case: str
) -> None:
    """Online output and snapshot aliases refuse without changing source or certificate bytes."""
    output, snapshot = tmp_path / "candidate", tmp_path / "snapshot.json"
    original = SOURCE.read_bytes()
    cert_before = certificate[0].read_bytes()
    source_path = SOURCE
    if case == "input":
        snapshot = SOURCE
    elif case == "ca":
        snapshot = certificate[0]
    elif case == "output":
        snapshot = output / "reactor_repositories.tsv"
    elif case == "accepted":
        output = DIRECTORY
    else:
        output.mkdir()
        (output / "anulum_reactor_repos.js").symlink_to(SOURCE)
    result = run_cli(
        SCRIPT,
        "--refresh",
        "--source",
        str(source_path),
        "--ca-file",
        str(certificate[0]),
        "--api-url",
        "https://localhost:0/repos",
        "--snapshot-out",
        str(snapshot),
        "--output-dir",
        str(output),
    )
    assert result.returncode == 1 and "output must be separate" in result.stdout
    assert SOURCE.read_bytes() == original and certificate[0].read_bytes() == cert_before


@pytest.mark.parametrize("mutation", ["bad-date", "bad-unicode", "missing-repository", "201"])
def test_native_online_preparation_errors_never_write_snapshot(
    certificate: tuple[Path, Path], tmp_path: Path, mutation: str
) -> None:
    """Invalid dates, encoding, required records or HTTP status produce neither snapshot nor outputs."""
    records = api_records()
    if mutation == "bad-unicode":
        next(r for r in records if r["name"] == "scpn-fusion-core")["description"] = "\ud800"
    elif mutation == "missing-repository":
        records = [r for r in records if r["name"] != "scpn-fusion-core"]
    routes: dict[str, tuple[int, dict[str, str], bytes, float]] = {
        "/repos": (201 if mutation == "201" else 200, {}, api_body(records), 0.0)
    }
    with api_server(certificate, routes) as (url, _requests):
        snapshot, output = tmp_path / "snapshot.json", tmp_path / "candidate"
        result = run_cli(
            SCRIPT,
            "--refresh",
            "--api-url",
            url,
            "--ca-file",
            str(certificate[0]),
            "--snapshot-out",
            str(snapshot),
            "--output-dir",
            str(output),
            "--date",
            "invalid" if mutation == "bad-date" else "2026-09-27",
        )
        assert result.returncode == 1 and "Traceback" not in result.stderr
        assert not snapshot.exists() and not output.exists()


@pytest.mark.parametrize("size", [4096, 16384])
def test_real_file_size_limit_cleans_failed_atomic_temporary(tmp_path: Path, size: int) -> None:
    """A real 1,024-byte file limit refuses larger writes and preserves the prior candidate alone."""
    destination = tmp_path / "candidate"
    destination.write_bytes(b"previous accepted candidate")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import importlib.util,resource,signal,sys; from pathlib import Path; "
            "s=importlib.util.spec_from_file_location('producer',sys.argv[1]); "
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
            "signal.signal(signal.SIGXFSZ,signal.SIG_IGN); "
            "previous=resource.getrlimit(resource.RLIMIT_FSIZE); "
            "resource.setrlimit(resource.RLIMIT_FSIZE,(1024,previous[1]));\n"
            "try:\n m.atomic_write(Path(sys.argv[2]),b'x'*int(sys.argv[3]))\n"
            "finally:\n resource.setrlimit(resource.RLIMIT_FSIZE,previous)\n",
            str(SCRIPT),
            str(destination),
            str(size),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0 and "File too large" in result.stderr
    assert list(tmp_path.iterdir()) == [destination]
    assert destination.read_bytes() == b"previous accepted candidate"


def test_casefold_identity_collision_is_refused_before_writing(
    producer: ModuleType, tmp_path: Path
) -> None:
    """Case-insensitive duplicate repository identities raise before creating output."""
    records = api_records()
    duplicate = records[0].copy()
    duplicate["name"] = duplicate["name"].swapcase()
    duplicate["html_url"] = "https://github.com/anulum/" + duplicate["name"]
    duplicate["url"] = "https://api.github.com/repos/anulum/" + duplicate["name"]
    with pytest.raises(ValueError, match="duplicate"):
        producer.build([*records, duplicate], tmp_path / "candidate", retrieved="2026-09-27")
    assert not (tmp_path / "candidate").exists()


def test_null_spdx_is_an_observation_without_a_software_licence_claim(
    producer: ModuleType, tmp_path: Path
) -> None:
    """A null SPDX cell retains licence absence and the original shared-physics evidence boundary."""
    records = api_records()
    next(r for r in records if r["name"] == "scpn-fusion-core")["license"] = {"spdx_id": None}
    producer.build(records, tmp_path, retrieved="2026-09-27")
    rows = json.loads((tmp_path / "reactor_repositories.json").read_bytes())["records"]
    row = next(r for r in rows if r["name"] == "scpn-fusion-core")
    assert row["license"] == "not asserted by GitHub metadata"
    assert row["evidence_boundary"] == producer.BOUNDARIES["shared physics / kernels"]


def test_native_write_failure_preserves_destination_but_bundle_is_not_transactional(
    tmp_path: Path,
) -> None:
    """A later native write failure preserves its directory while retaining the earlier successful TSV."""
    (tmp_path / "reactor_repositories.json").mkdir()
    result = run_cli(SCRIPT, "--output-dir", str(tmp_path))
    assert result.returncode == 1 and "Traceback" not in result.stderr
    assert (tmp_path / "reactor_repositories.json").is_dir()
    assert (tmp_path / "reactor_repositories.tsv").read_bytes() == (
        DIRECTORY / "reactor_repositories.tsv"
    ).read_bytes()
    assert {p.name for p in tmp_path.iterdir()} == {
        "reactor_repositories.tsv",
        "reactor_repositories.json",
    }


def test_native_snapshot_symlink_to_input_is_refused(tmp_path: Path) -> None:
    """A snapshot symlink to accepted input refuses while preserving the source and link."""
    before = SOURCE.read_bytes()
    link = tmp_path / "snapshot.json"
    link.symlink_to(SOURCE)
    result = run_cli(
        SCRIPT,
        "--refresh",
        "--snapshot-out",
        str(link),
        "--output-dir",
        str(tmp_path / "candidate"),
    )
    assert result.returncode == 1 and "output must be separate" in result.stdout
    assert SOURCE.read_bytes() == before and link.is_symlink()
    assert not (tmp_path / "candidate").exists()
