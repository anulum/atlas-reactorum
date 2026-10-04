# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — native full-data browser checker conformance

"""Exercise complete native Atlas browser journeys, protocol recovery and downloads."""

from __future__ import annotations

import csv
import json
import socket
import sys
import time
from pathlib import Path

import pytest
import requests

from ._catalogue_inputs import ROOT, run_cli
from .browser_checks_runtime import (
    ASSETS,
    NAVIGATION_CHECKER,
    SCRIPT,
    wait_for_page,
)
from .browser_checks_runtime import BrowserEndpoints as BrowserEndpoints
from .browser_checks_runtime import native_browser as native_browser
from .conftest import load_module


def test_full_native_application_cli_normal_and_optimized(native_browser: BrowserEndpoints) -> None:
    """Require all sixteen public checks and complete catalogue counts in both interpreter modes.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Actual isolated Chrome discovery origin and complete normal/damaged Atlas URLs.

    Raises
    ------
    AssertionError
        The actual native response, refusal, restored page or exported content
        differs from the complete contract asserted by this case.
    """
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
    """Reject the real non-English page and commit its restoration before another test can select it.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Actual isolated Chrome discovery origin and complete normal/damaged Atlas URLs.

    Raises
    ------
    AssertionError
        The actual native response, refusal, restored page or exported content
        differs from the complete contract asserted by this case.
    """
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_browser_checker")
    with module.BrowserSession(native_browser["endpoint"], native_browser["page"]) as browser:
        browser.command("Page.navigate", {"url": native_browser["damaged"]})
    wait_for_page(native_browser["endpoint"], native_browser["damaged"])
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
        wait_for_page(native_browser["endpoint"], native_browser["page"])


def test_native_protocol_events_exceptions_values_and_deadlines(
    native_browser: BrowserEndpoints,
) -> None:
    """Exercise real CDP events, JavaScript failures, expired replies and recovery on the owned page.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Actual isolated Chrome discovery origin and complete normal/damaged Atlas URLs.

    Raises
    ------
    AssertionError
        The actual native response, refusal, restored page or exported content
        differs from the complete contract asserted by this case.
    """
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
    """Require a released native WebSocket to fail evaluation rather than pass a browser check.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Actual isolated Chrome discovery origin and complete normal/damaged Atlas URLs.

    Raises
    ------
    AssertionError
        The actual native response, refusal, restored page or exported content
        differs from the complete contract asserted by this case.
    """
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
    """Reject unsafe discovery origins without disclosing credential text through the public CLI.

    Parameters
    ----------
    endpoint : str
        Explicit invalid discovery origin exercised before any browser access.
    native_browser : BrowserEndpoints
        Actual isolated Chrome discovery origin and complete normal/damaged Atlas URLs.

    Raises
    ------
    AssertionError
        The actual native response, refusal, restored page or exported content
        differs from the complete contract asserted by this case.
    """
    result = run_cli(SCRIPT, "--endpoint", endpoint, "--page-url", native_browser["page"])
    assert result.returncode == 1 and "loopback HTTP origin" in result.stdout
    assert "Traceback" not in result.stderr and "untrusted" not in result.stdout


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf"])
def test_invalid_deadline_refuses_before_discovery(
    native_browser: BrowserEndpoints, timeout: str
) -> None:
    """Reject invalid public deadlines before contacting the actual Chrome discovery endpoint.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Actual isolated Chrome discovery origin and complete normal/damaged Atlas URLs.
    timeout : str
        Nonpositive or nonfinite CLI deadline exercised before discovery.

    Raises
    ------
    AssertionError
        The actual native response, refusal, restored page or exported content
        differs from the complete contract asserted by this case.
    """
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
    """Reject an ordinary asset server, absent exact page and closed local port through the real CLI.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Actual isolated Chrome discovery origin and complete normal/damaged Atlas URLs.

    Raises
    ------
    AssertionError
        The actual native response, refusal, restored page or exported content
        differs from the complete contract asserted by this case.
    """
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


def test_public_main_and_import_have_no_implicit_browser_access(
    native_browser: BrowserEndpoints, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the explicit imported CLI while preserving argument-required refusal on bare invocation.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Actual isolated Chrome discovery origin and complete normal/damaged Atlas URLs.
    monkeypatch : pytest.MonkeyPatch
        Restore the real public CLI arguments after invoking its imported entry point.

    Raises
    ------
    AssertionError
        The actual native response, refusal, restored page or exported content
        differs from the complete contract asserted by this case.
    """
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
    """Compare every actual JSON and CSV download record and source assertion with the complete export.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Actual isolated Chrome discovery origin and complete normal/damaged Atlas URLs.
    tmp_path : pathlib.Path
        Owned directory receiving real browser-produced CSV and JSON downloads.

    Raises
    ------
    AssertionError
        The actual native response, refusal, restored page or exported content
        differs from the complete contract asserted by this case.
    """
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


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_owned_page_wait_refuses_invalid_deadlines(
    native_browser: BrowserEndpoints, timeout: float
) -> None:
    """Reject invalid fixture deadlines before native discovery can be queried.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Actual isolated Chrome endpoint used by the browser journeys.
    timeout : float
        Nonpositive or nonfinite bounded-wait argument.

    Raises
    ------
    AssertionError
        Invalid readiness bounds do not raise the explicit argument refusal.
    """
    with pytest.raises(ValueError, match="positive and finite"):
        wait_for_page(native_browser["endpoint"], native_browser["page"], timeout=timeout)


def test_owned_page_wait_has_a_finite_missing_target_deadline(
    native_browser: BrowserEndpoints,
) -> None:
    """Bound an absent exact target without selecting or altering another native page.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Actual Chrome discovery origin and committed full Atlas page.

    Raises
    ------
    AssertionError
        A page Chrome never opened passes readiness or the existing page is lost.
    """
    started = time.monotonic()
    with pytest.raises(AssertionError, match="did not commit the exact Atlas page"):
        wait_for_page(
            native_browser["endpoint"],
            native_browser["page"] + "?deliberately-never-opened",
            timeout=1,
        )
    assert time.monotonic() - started < 3
    wait_for_page(native_browser["endpoint"], native_browser["page"])


def test_owned_page_wait_refuses_two_real_matching_chrome_targets(
    native_browser: BrowserEndpoints,
) -> None:
    """Refuse actual duplicate Chrome pages and close only the newly owned extra target.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Owned complete Atlas page whose second native target creates ambiguity.

    Raises
    ------
    AssertionError
        The second real page cannot commit or an ambiguous exact target is accepted.
    """
    module = load_module(str(SCRIPT.relative_to(ROOT)), "atlas_duplicate_page_checker")
    with module.BrowserSession(native_browser["endpoint"], native_browser["page"]) as browser:
        target = browser.command("Target.createTarget", {"url": native_browser["page"]})["targetId"]
        assert isinstance(target, str)
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                info = browser.command("Target.getTargetInfo", {"targetId": target})["targetInfo"]
                assert isinstance(info, dict)
                if info.get("url") == native_browser["page"]:
                    break
                time.sleep(0.05)
            else:
                pytest.fail("Owned second native Chrome page did not commit")
            with pytest.raises(NAVIGATION_CHECKER.BrowserCheckError, match="exactly one matching"):
                wait_for_page(native_browser["endpoint"], native_browser["page"])
        finally:
            browser.command("Target.closeTarget", {"targetId": target})
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                with requests.get(
                    native_browser["endpoint"] + "/json/list",
                    timeout=1,
                    allow_redirects=False,
                ) as response:
                    response.raise_for_status()
                    targets = response.json()
                assert isinstance(targets, list)
                assert all(isinstance(item, dict) for item in targets)
                if all(item.get("id") != target for item in targets):
                    break
                time.sleep(0.05)
            else:
                pytest.fail("Owned extra Chrome target remained after its close acknowledgement")
    wait_for_page(native_browser["endpoint"], native_browser["page"])
