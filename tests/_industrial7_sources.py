# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete original-source TLS conformance inputs
"""Serve complete native publisher captures through a real verified TLS connection."""

from __future__ import annotations

import contextlib
import hashlib
import importlib
import json
import os
import shutil
import ssl
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from functools import cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "05_global_reactor_map.imports.industrial_facilities.expansion_round7"
CAPTURE = importlib.import_module(PREFIX + ".capture")
ACQUISITION = importlib.import_module(PREFIX + ".acquisition")
SCRIPTS = ROOT / "05_global_reactor_map/imports/industrial_facilities/expansion_round7"


def copy_custody(target: Path, original: Path) -> None:
    """Preserve complete originals and receipts in a newly owned test copy.

    Parameters
    ----------
    target : pathlib.Path
        Previously absent destination for the complete source and receipt set.
    original : pathlib.Path
        Verified complete original publisher custody.
    """
    target.mkdir()
    for name in [*CAPTURE.BASE_URLS, "ARPAE_COMPLETE.json"]:
        for filename in (name, name + ".receipt.json"):
            shutil.copy2(original / filename, target / filename)


def revise_json(directory: Path, name: str, value: object) -> None:
    """Bind an explicit negative source mutation to its updated copy receipt.

    Parameters
    ----------
    directory : pathlib.Path
        Owned negative-test source copy; original custody remains unchanged.
    name : str
        Fixed JSON resource filename.
    value : object
        Explicit negative JSON content to serialize.
    """
    path = directory / name
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    receipt_path = directory / (name + ".receipt.json")
    receipt = json.loads(receipt_path.read_text())
    receipt["bytes"] = path.stat().st_size
    receipt["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")


def receipt_change(directory: Path, name: str, field: str, value: object) -> None:
    """Change one negative receipt member without modifying original custody.

    Parameters
    ----------
    directory : pathlib.Path
        Owned source copy for the refusal case.
    name : str
        Resource filename whose acquisition receipt is changed.
    field : str
        Receipt member deliberately made inconsistent.
    value : object
        Authored negative value for that member.
    """
    path = directory / (name + ".receipt.json")
    record = json.loads(path.read_text())
    record[field] = value
    path.write_text(json.dumps(record))


def run_cli(
    module: str, directory: Path, *args: str, optimize: bool = False
) -> subprocess.CompletedProcess[str]:
    """Exercise the public source CLI in a bounded separate native process.

    Parameters
    ----------
    module : str
        Fixed source-script basename.
    directory : pathlib.Path
        Capture or bundle path supplied to the CLI.
    optimize : bool, optional
        Enable interpreter optimization while retaining runtime source guards.
    *args : str
        Additional native CLI arguments, preserved in their original order.

    Returns
    -------
    subprocess.CompletedProcess of str
        Native exit status and captured stdout/stderr from the public CLI.
    """
    return subprocess.run(
        [
            sys.executable,
            *(["-O"] if optimize else []),
            str(SCRIPTS / (module + ".py")),
            "--directory",
            str(directory),
            *args,
        ],
        cwd=directory.parent,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@contextlib.contextmanager
def tls_source(
    directory: Path, original: Path, overrides: dict[str, bytes] | None = None
) -> Iterator[tuple[str, Path]]:
    """Serve complete publisher originals through a real trusted TLS connection.

    Parameters
    ----------
    directory : pathlib.Path
        Owned directory for the one-day localhost certificate and private key.
    original : pathlib.Path
        Complete publisher source captures to serve without rewriting them.
    overrides : dict of str to bytes or None, optional
        Explicit negative bodies or real paginated features replacing named resources.

    Yields
    ------
    tuple of str and pathlib.Path
        HTTPS server URL and its trusted certificate path; shutdown is guaranteed.
    """
    bodies = {name: (original / name).read_bytes() for name in CAPTURE.BASE_URLS}
    bodies["ARPAE_COMPLETE.json"] = (original / "ARPAE_COMPLETE.json").read_bytes()
    bodies["ARPAE_PAGE_0000.json"] = (original / "ARPAE_COMPLETE.json").read_bytes()
    bodies.update(overrides or {})
    certificate, key = directory / "ca.pem", directory / "key.pem"
    result = subprocess.run(
        [
            "/usr/bin/openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key),
            "-out",
            str(certificate),
            "-days",
            "1",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost",
        ],
        capture_output=True,
        timeout=10,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("owned TLS certificate generation failed")

    class Handler(BaseHTTPRequestHandler):
        """Serve actual original bytes; special paths exercise real transport refusals."""

        def log_message(self, format: str, *args: object) -> None:
            """Suppress HTTP request diagnostics while retaining real transport behavior.

            Parameters
            ----------
            format : str
                HTTP-server diagnostic template, intentionally not emitted.
            *args : object
                HTTP-server formatting arguments, intentionally not emitted.
            """

        def do_GET(self) -> None:
            """Return exact source bodies or explicit status and slow-read refusal inputs."""
            path = urlsplit(self.path).path
            if path.startswith("/status/"):
                self.send_response(int(path.rsplit("/", 1)[1]))
                self.send_header("Location", "/files/SFOE_ORIGINAL.csv.zip")
                self.end_headers()
                return
            name = path.rsplit("/", 1)[-1]
            body = bodies["SFOE_ORIGINAL.csv.zip"] if path in {"/", "/slow"} else bodies.get(name)
            if body is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                if path == "/slow":
                    self.wfile.write(body[:1])
                    self.wfile.flush()
                    time.sleep(0.1)
                    self.wfile.write(body[1:])
                else:
                    self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError, ssl.SSLError):
                return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certificate, key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"https://localhost:{server.server_port}", certificate
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@cache
def _prepared_custody(base: Path, supplied: str | None) -> Path:
    """Reuse retained originals without overwriting a failed source acquisition.

    Parameters
    ----------
    base : pathlib.Path
        External session directory containing the fixed capture location.
    supplied : str or None
        Explicit original custody; otherwise acquire only a previously absent target.

    Returns
    -------
    pathlib.Path
        Original custody after complete receipt, resource and rights validation.

    Raises
    ------
    ValueError
        Retained source captures fail their original validation contract.
    OSError
        Explicit custody or a required retained capture is unavailable.

    Notes
    -----
    Successful preparation is cached. Exceptions retain their source files and
    are not cached; later fixture requests revalidate those same bytes rather
    than attempting to acquire into an existing target.
    """
    if supplied:
        path = Path(supplied).resolve(strict=True)
        CAPTURE.read_captures(path)
    else:
        path = base / "atlas-industrial7-native-source" / "capture"
        if path.exists():
            CAPTURE.read_captures(path)
        else:
            ACQUISITION.acquire(path)
    return path


@pytest.fixture(scope="session")
def source_custody(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Use verified local originals or acquire the complete sources outside the checkout.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        Session-owned external location for the genuine native acquisition.

    Returns
    -------
    pathlib.Path
        Complete positively reviewed source captures, including their receipts.

    Notes
    -----
    ATLAS_INDUSTRIAL7_CAPTURE_DIR selects previously retained genuine originals.
    Without it the real public collector fetches the publisher URLs. Raw terms
    HTML remains only in temporary or owner-supplied custody, never in Git.
    """
    return _prepared_custody(
        tmp_path_factory.getbasetemp(), os.environ.get("ATLAS_INDUSTRIAL7_CAPTURE_DIR")
    )
