# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — native full-data browser checker conformance

"""Own native Chrome, complete Atlas asset serving and committed-page fixtures."""

from __future__ import annotations

import json
import math
import mimetypes
import os
import shutil
import socket
import subprocess
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import ModuleType
from typing import TypedDict
from urllib.parse import unquote, urlsplit

import pytest
import requests

from ._catalogue_inputs import ROOT
from .conftest import load_module

SCRIPT = ROOT / "04_interactive_presentation/browser-check.py"
ASSETS = SCRIPT.parent
NAVIGATION_CHECKER: ModuleType = load_module(
    str(SCRIPT.relative_to(ROOT)), "atlas_navigation_checker"
)
COUNT_EXPRESSION = "({types: reactors.length, facilities: window.REACTOR_FACILITIES.length, companies: window.FUSION_COMPANIES.length, repositories: window.ANULUM_REACTOR_REPOS.length})"


class BrowserEndpoints(TypedDict):
    """Owned native browser and complete normal/damaged Atlas page locations.

    Attributes
    ----------
    endpoint : str
        Isolated loopback Chrome DevTools HTTP origin.
    page : str
        Exact complete Atlas page URL for this owned browser.
    damaged : str
        Exact page URL whose real HTML deliberately changes the language.
    static : str
        Loopback HTTP origin serving the complete actual Atlas assets.
    """

    endpoint: str
    page: str
    damaged: str
    static: str


class NativeObservation(TypedDict):
    """Native Chrome target list, reply and complete catalogue count observation.

    Attributes
    ----------
    targets : list of dict
        Complete native discovery target document.
    payload : str or bytes
        Original serialized Chrome reply for the count expression.
    message : dict
        Decoded native reply retaining its command identifier.
    result : dict
        Validated native command result.
    counts : dict of str to int
        Actual complete type, facility, company and repository counts.
    """

    targets: list[dict[str, object]]
    payload: str | bytes
    message: dict[str, object]
    result: dict[str, object]
    counts: dict[str, int]


class AtlasHandler(BaseHTTPRequestHandler):
    """Serve complete canonical assets; one explicit index mutation changes language."""

    def do_GET(self) -> None:
        """Serve canonical assets or the deliberate non-English index mutation.

        Raises
        ------
        OSError
            Reading an actual asset or writing the owned HTTP response fails.
        """
        path = unquote(urlsplit(self.path).path)
        damaged = path.startswith("/bad/")
        relative = path[5:] if damaged else path.lstrip("/")
        source = (ASSETS / relative).resolve()
        if not source.is_relative_to(ASSETS) or not source.is_file():
            self.send_error(404)
            return
        body = source.read_bytes()
        if damaged and source.name == "index.html":
            body = body.replace(b'<html lang="en">', b'<html lang="sk">')
        self.send_response(200)
        self.send_header(
            "Content-Type", mimetypes.guess_type(source.name)[0] or "application/octet-stream"
        )
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Suppress only the standard access log for the owned native asset server.

        Parameters
        ----------
        format : str
            Inherited HTTP access-log format, deliberately unused.
        *args : object
            Inherited HTTP access-log values, deliberately unused.
        """


def wait_for_page(endpoint: str, page_url: str, *, timeout: float = 20) -> None:
    """Wait for an owned Chrome navigation to commit its exact target URL.

    Parameters
    ----------
    endpoint : str
        Isolated loopback discovery origin owned by the fixture.
    page_url : str
        Exact intended page URL; another target never satisfies readiness.
    timeout : float, optional
        Positive finite bound for this owned navigation, in seconds.

    Raises
    ------
    ValueError
        The deadline is nonpositive or nonfinite.
    AssertionError
        The owned page remains absent through the bounded navigation deadline.
    BrowserCheckError
        Native target validation finds malformed, ambiguous or unsafe discovery.
    requests.RequestException
        The already-started native discovery endpoint cannot be queried.
    """
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("page readiness deadline must be positive and finite")
    module = NAVIGATION_CHECKER
    module.validate_endpoint(endpoint)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with requests.get(
            endpoint + "/json/list", timeout=min(1, timeout), allow_redirects=False
        ) as response:
            response.raise_for_status()
            targets = response.json()
        if isinstance(targets, list) and all(isinstance(target, dict) for target in targets):
            matches = [
                target
                for target in targets
                if target.get("type") == "page" and target.get("url") == page_url
            ]
            if not matches:
                time.sleep(0.05)
                continue
        module.select_page(targets, page_url, endpoint)
        return
    raise AssertionError("Owned native Chrome did not commit the exact Atlas page")


@pytest.fixture(scope="module")
def native_browser(tmp_path_factory: pytest.TempPathFactory) -> Iterator[BrowserEndpoints]:
    """Yield isolated real Chrome only after its exact Atlas page is committed.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        Owner-controlled directory for the native profile and original Chrome log.

    Yields
    ------
    BrowserEndpoints
        Complete normal/damaged Atlas URLs and their isolated loopback origins.

    Raises
    ------
    AssertionError
        Native Chrome is absent, exits early or fails to commit the exact page.
    """
    directory = tmp_path_factory.mktemp("native-atlas-browser")
    executable = shutil.which("google-chrome") or shutil.which("chromium")
    assert executable is not None
    server = ThreadingHTTPServer(("127.0.0.1", 0), AtlasHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    static = f"http://127.0.0.1:{server.server_port}"
    page = static + "/index.html"
    with (directory / "chrome.log").open("wb") as log:
        process = subprocess.Popen(
            [
                executable,
                "--headless=new",
                *(["--no-sandbox"] if os.environ.get("ATLAS_BROWSER_NO_SANDBOX") == "1" else []),
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-background-networking",
                "--window-size=1440,1000",
                f"--remote-debugging-port={port}",
                "--remote-debugging-address=127.0.0.1",
                f"--remote-allow-origins={origin}",
                f"--user-data-dir={directory / 'profile'}",
                page,
            ],
            stdout=log,
            stderr=log,
        )
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                assert process.poll() is None, (directory / "chrome.log").read_text(
                    errors="replace"
                )
                try:
                    with requests.get(origin + "/json/list", timeout=1) as response:
                        if response.status_code == 200:
                            break
                except requests.RequestException:
                    pass
                time.sleep(0.05)
            else:
                pytest.fail("Owned native Chrome did not expose DevTools")
            wait_for_page(origin, page, timeout=deadline - time.monotonic())
            yield BrowserEndpoints(
                endpoint=origin, page=page, damaged=static + "/bad/index.html", static=static
            )
        finally:
            process.terminate()
            process.wait(timeout=10)
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


@pytest.fixture(scope="module")
def native_observation(native_browser: BrowserEndpoints) -> NativeObservation:
    """Capture a complete count reply and target list from the owned native page.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Committed owned Chrome endpoint and complete actual Atlas page.

    Returns
    -------
    NativeObservation
        Original native payload, decoded result, complete counts and discovery list.

    Raises
    ------
    AssertionError
        The real matching native command reply contains no validated result.
    """
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    with module.BrowserSession(native_browser["endpoint"], native_browser["page"]) as browser:
        browser.wait_ready()
        browser.connection.send(
            json.dumps(
                {
                    "id": 100001,
                    "method": "Runtime.evaluate",
                    "params": {"expression": COUNT_EXPRESSION, "returnByValue": True},
                }
            )
        )
        while True:
            payload = browser.connection.recv()
            message = json.loads(payload)
            if message.get("id") == 100001:
                result = module.response_result(payload, 100001)
                assert result is not None
                counts = module.parse_counts(module.evaluation_value(result))
                break
    with requests.get(native_browser["endpoint"] + "/json/list", timeout=3) as response:
        targets = response.json()
    return NativeObservation(
        targets=targets, payload=payload, message=message, result=result, counts=counts
    )
