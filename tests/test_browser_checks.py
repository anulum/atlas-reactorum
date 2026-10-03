# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — native full-data browser checker conformance

"""Use isolated native Chrome and all actual Atlas assets, not browser doubles."""

from __future__ import annotations

import copy
import csv
import json
import mimetypes
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TypedDict
from urllib.parse import unquote, urlsplit

import pytest
import requests

from ._catalogue_inputs import ROOT, run_cli
from .conftest import load_module

SCRIPT = ROOT / "04_interactive_presentation/browser-check.py"
ASSETS = SCRIPT.parent
COUNT_EXPRESSION = "({types: reactors.length, facilities: window.REACTOR_FACILITIES.length, companies: window.FUSION_COMPANIES.length, repositories: window.ANULUM_REACTOR_REPOS.length})"


class BrowserEndpoints(TypedDict):
    """Owned native browser and complete normal/damaged Atlas page locations."""

    endpoint: str
    page: str
    damaged: str
    static: str


class NativeObservation(TypedDict):
    """Actual Chrome target list, serialized reply and its complete count observation."""

    targets: list[dict[str, object]]
    payload: str | bytes
    message: dict[str, object]
    result: dict[str, object]
    counts: dict[str, int]


class AtlasHandler(BaseHTTPRequestHandler):
    """Serve complete canonical assets; one explicit index mutation changes language."""

    def do_GET(self) -> None:
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
        """Keep actual asset traffic out of test summaries."""


@pytest.fixture(scope="module")
def native_browser(tmp_path_factory: pytest.TempPathFactory) -> Iterator[BrowserEndpoints]:
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


def test_full_native_application_cli_normal_and_optimized(native_browser: BrowserEndpoints) -> None:
    for optimized in (False, True):
        result = run_cli(
            SCRIPT,
            "--endpoint",
            native_browser["endpoint"],
            "--page-url",
            native_browser["page"],
            optimize=optimized,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads(result.stdout)
        assert report["result"] == "passed"
        assert report["counts"] == {
            "types": 135,
            "facilities": 13459,
            "companies": 98,
            "repositories": 30,
        }
        assert "cluster record conservation" in report["checks"] and len(report["checks"]) == 16


def test_native_page_language_failure_is_enforced_even_under_optimization(
    native_browser: BrowserEndpoints,
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    with module.BrowserSession(native_browser["endpoint"], native_browser["page"]) as browser:
        browser.command("Page.navigate", {"url": native_browser["damaged"]})
    try:
        for optimized in (False, True):
            result = run_cli(
                SCRIPT,
                "--endpoint",
                native_browser["endpoint"],
                "--page-url",
                native_browser["damaged"],
                optimize=optimized,
            )
            assert result.returncode == 1 and "Atlas invariant failed" in result.stdout
            assert (
                "document.documentElement.lang" in result.stdout
                and "Traceback" not in result.stderr
            )
    finally:
        with module.BrowserSession(
            native_browser["endpoint"], native_browser["damaged"]
        ) as browser:
            browser.command("Page.navigate", {"url": native_browser["page"]})


def test_native_protocol_events_exceptions_values_and_deadlines(
    native_browser: BrowserEndpoints,
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    with module.BrowserSession(native_browser["endpoint"], native_browser["page"]) as browser:
        browser.wait_ready()
        browser.command("Runtime.enable")
        assert browser.evaluate("console.log('owned native event'); 42") == 42
        assert browser.evaluate("undefined") is None
        with pytest.raises(module.BrowserCheckError, match="protocol command"):
            browser.command("AtlasMethodDoesNotExist")
        with pytest.raises(module.BrowserCheckError, match="JavaScript evaluation"):
            browser.evaluate("throw new Error('explicit native negative case')")
        with pytest.raises(module.BrowserCheckError, match="invariant"):
            browser.verify("1")
        with pytest.raises((module.BrowserCheckError, module.websocket.WebSocketException)):
            browser.evaluate("true", timeout=1e-12)
        assert browser.evaluate("true") is True
        with pytest.raises(module.websocket.WebSocketException):
            browser.evaluate(
                "new Promise(resolve => setTimeout(() => resolve(true), 100))", timeout=0.01
            )
        assert browser.evaluate("true") is True
        with pytest.raises(ValueError, match="positive and finite"):
            browser.command("Runtime.enable", timeout=0)
        with pytest.raises(ValueError, match="positive and finite"):
            browser.wait_ready(timeout=0)
        browser.evaluate("window.REACTOR_FACILITIES = undefined")
        with pytest.raises(module.BrowserCheckError, match="readiness deadline"):
            browser.wait_ready(timeout=0.01)
        browser.command("Page.reload")
        browser.wait_ready()
        assert module.run_checks(browser, reload=False)["result"] == "passed"


def test_real_closed_socket_is_not_a_passing_check(native_browser: BrowserEndpoints) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    browser = module.BrowserSession(native_browser["endpoint"], native_browser["page"])
    browser.close()
    with pytest.raises(module.websocket.WebSocketException):
        browser.evaluate("true")


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://example.org/",
        "https://localhost/",
        "http://127.0.0.1:0/",
        "http://127.0.0.1:invalid/",
        "http://[",
        "http://person@localhost/",
        "http://:untrusted@localhost/",
        "http://localhost/json",
        "http://localhost/?x=1",
        "http://localhost/#target",
        "http://localhost/a b",
    ],
)
def test_nonlocal_or_credential_bearing_endpoint_refuses_before_browser_access(
    endpoint: str, native_browser: BrowserEndpoints
) -> None:
    result = run_cli(SCRIPT, "--endpoint", endpoint, "--page-url", native_browser["page"])
    assert result.returncode == 1 and "loopback HTTP origin" in result.stdout
    assert "Traceback" not in result.stderr and "untrusted" not in result.stdout


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf"])
def test_invalid_deadline_refuses_before_discovery(
    native_browser: BrowserEndpoints, timeout: str
) -> None:
    result = run_cli(
        SCRIPT,
        "--endpoint",
        native_browser["endpoint"],
        "--page-url",
        native_browser["page"],
        "--timeout",
        timeout,
    )
    assert result.returncode == 1 and "positive and finite" in result.stdout


def test_actual_static_server_and_missing_page_are_not_devtools(
    native_browser: BrowserEndpoints,
) -> None:
    for endpoint, page in [
        (native_browser["static"], native_browser["page"]),
        (native_browser["endpoint"], native_browser["page"] + "?not-selected"),
    ]:
        result = run_cli(SCRIPT, "--endpoint", endpoint, "--page-url", page)
        assert result.returncode == 1 and "failed" in result.stdout
        assert "Traceback" not in result.stderr
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    result = run_cli(
        SCRIPT, "--endpoint", f"http://127.0.0.1:{port}", "--page-url", native_browser["page"]
    )
    assert result.returncode == 1 and "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "damage",
    [
        "root",
        "item",
        "absent",
        "duplicate",
        "missing_debugger",
        "debugger_type",
        "remote_debugger",
        "debugger_scheme",
        "debugger_path",
        "debugger_query",
        "debugger_fragment",
    ],
)
def test_public_selection_refuses_damaged_actual_target_documents(
    native_browser: BrowserEndpoints, native_observation: NativeObservation, damage: str
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    targets = copy.deepcopy(native_observation["targets"])
    if damage == "root":
        document: object = {"records": targets}
    elif damage == "item":
        document = [*targets, None]
    else:
        document = targets
        selected = next(target for target in targets if target["url"] == native_browser["page"])
        if damage == "absent":
            selected["url"] = native_browser["page"] + "?not-the-same-page"
        elif damage == "duplicate":
            targets.append(selected.copy())
        elif damage == "missing_debugger":
            selected.pop("webSocketDebuggerUrl")
        elif damage == "debugger_type":
            selected["webSocketDebuggerUrl"] = True
        else:
            selected["webSocketDebuggerUrl"] = {
                "remote_debugger": "ws://example.org/devtools/page/identity",
                "debugger_scheme": native_browser["endpoint"].replace("http:", "wss:")
                + "/devtools/page/identity",
                "debugger_path": native_browser["endpoint"].replace("http:", "ws:")
                + "/other/identity",
                "debugger_query": native_browser["endpoint"].replace("http:", "ws:")
                + "/devtools/page/identity?x=1",
                "debugger_fragment": native_browser["endpoint"].replace("http:", "ws:")
                + "/devtools/page/identity#section",
            }[damage]
    with pytest.raises(module.BrowserCheckError):
        module.select_page(document, native_browser["page"], native_browser["endpoint"])


@pytest.mark.parametrize(
    "damage", ["root", "json", "event", "other_id", "error", "result", "exception"]
)
def test_public_decoder_uses_captured_native_reply_and_explicit_corruptions(
    native_observation: NativeObservation, damage: str
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    message = copy.deepcopy(native_observation["message"])
    if damage == "root":
        payload = json.dumps([message])
    elif damage == "json":
        payload = str(native_observation["payload"])[:-1]
    else:
        if damage == "event":
            message.pop("id")
        elif damage == "other_id":
            message["id"] = 100000
        elif damage == "error":
            message["error"] = {"code": -32601, "message": "explicit damaged replay"}
        elif damage == "result":
            message["result"] = []
        elif damage == "exception":
            result = copy.deepcopy(native_observation["result"])
            result["exceptionDetails"] = {"text": "explicit damaged replay"}
            message["result"] = result
        payload = json.dumps(message)
    if damage in {"event", "other_id"}:
        assert module.response_result(payload, 100001) is None
    else:
        with pytest.raises((module.BrowserCheckError, ValueError)):
            module.response_result(payload, 100001)


@pytest.mark.parametrize("damage", ["missing", "invalid"])
def test_public_remote_value_refuses_damage_to_actual_native_descriptor(
    native_observation: NativeObservation, damage: str
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    result = copy.deepcopy(native_observation["result"])
    if damage == "missing":
        result.pop("result")
    else:
        result["result"] = []
    with pytest.raises(module.BrowserCheckError, match="remote object"):
        module.evaluation_value(result)


@pytest.mark.parametrize("damage", ["root", "missing", "extra", "bool", "text", "different"])
def test_public_count_decoder_refuses_corrupted_complete_native_observation(
    native_observation: NativeObservation, damage: str
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    counts = native_observation["counts"].copy()
    if damage == "root":
        observation: object = list(counts.values())
    else:
        changed: dict[str, object] = dict(counts)
        if damage == "missing":
            changed.pop("companies")
        elif damage == "extra":
            changed["untracked"] = 1
        else:
            changed["companies"] = {
                "bool": True,
                "text": str(counts["companies"]),
                "different": counts["companies"] - 1,
            }[damage]
        observation = changed
    with pytest.raises(module.BrowserCheckError, match="count"):
        module.parse_counts(observation)


def test_public_main_and_import_have_no_implicit_browser_access(
    native_browser: BrowserEndpoints, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--endpoint",
            native_browser["endpoint"],
            "--page-url",
            native_browser["page"],
        ],
    )
    assert module.main() == 0
    result = run_cli(SCRIPT)
    assert result.returncode == 2 and "--page-url" in result.stderr


def test_real_csv_and_json_downloads_preserve_all_field_assertions(
    native_browser: BrowserEndpoints, tmp_path: Path
) -> None:
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_download_checker")
    with module.BrowserSession(native_browser["endpoint"], native_browser["page"]) as browser:
        browser.command("Page.reload")
        browser.wait_ready()
        browser.command(
            "Browser.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": str(tmp_path), "eventsEnabled": True},
        )
        browser.evaluate("downloadFacilityData('json'); downloadFacilityData('csv')")
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            csv_files = list(tmp_path.glob("reactor-atlas-filtered-*.csv"))
            json_files = list(tmp_path.glob("reactor-atlas-filtered-*.json"))
            if len(csv_files) == len(json_files) == 1 and not list(tmp_path.glob("*.crdownload")):
                break
            time.sleep(0.05)
        assert len(csv_files) == len(json_files) == 1
        original = json.loads((ASSETS / "data/global_reactors.sample.json").read_bytes())["records"]
        downloaded = json.loads(json_files[0].read_bytes())
        assert downloaded == original
        with csv_files[0].open(newline="", encoding="utf-8") as stream:
            tabular = list(csv.DictReader(stream))
        assert len(tabular) == len(original) == 13459
        for record, row in zip(original, tabular, strict=True):
            assert row["id"] == record["id"]
            assert row["purpose"] == record.get("purpose", "")
            assert row["fuel_or_feed"] == record.get("fuel_or_feed", "")
            assert row["process_or_activity"] == record.get("process_or_activity", "")
            assert json.loads(row["field_observations"]) == record.get("field_observations", [])
