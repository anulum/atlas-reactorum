# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 04_interactive_presentation/browser-check.py
"""Verify the full loaded Atlas through an explicitly selected local Chrome page."""

from __future__ import annotations

import argparse
import json
import math
import time
from types import TracebackType
from urllib.parse import urlsplit

import requests
import websocket

EXPECTED_COUNTS = {"types": 135, "facilities": 13459, "companies": 98, "repositories": 30}


class BrowserCheckError(RuntimeError):
    """An unavailable browser, invalid protocol message or failed Atlas invariant."""


def validate_endpoint(endpoint: str) -> None:
    """Restrict DevTools discovery to an anonymous loopback HTTP origin.

    Parameters
    ----------
    endpoint : str
        Local Chrome origin, with an optional trailing slash.

    Raises
    ------
    ValueError
        Origin is malformed, remote, credential-bearing or contains a path.
    """
    try:
        parsed = urlsplit(endpoint)
        valid = (
            parsed.scheme == "http"
            and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
            and parsed.username is None
            and parsed.password is None
            and parsed.path in {"", "/"}
            and not parsed.query
            and not parsed.fragment
            and not any(character.isspace() for character in endpoint)
        )
        port = parsed.port
    except ValueError:
        valid, port = False, None
    if not valid or port == 0:
        raise ValueError("DevTools endpoint must be an anonymous loopback HTTP origin")


def select_page(targets: object, page_url: str, endpoint: str) -> str:
    """Select exactly one intended page from a Chrome target-list document.

    Parameters
    ----------
    targets : object
        Decoded native Chrome JSON target list.
    page_url : str
        Exact intended page URL; substring selection is not sufficient.
    endpoint : str
        Validated local discovery origin.

    Returns
    -------
    str
        Debugger WebSocket URL with the same authority as discovery.

    Raises
    ------
    BrowserCheckError
        List is invalid, selection is absent/ambiguous or debugger is unsafe.
    """
    validate_endpoint(endpoint)
    if not isinstance(targets, list) or any(not isinstance(target, dict) for target in targets):
        raise BrowserCheckError("invalid Chrome target list")
    matches = [
        target
        for target in targets
        if target.get("type") == "page" and target.get("url") == page_url
    ]
    if len(matches) != 1:
        raise BrowserCheckError("exactly one matching Atlas page is required")
    debugger: object = matches[0].get("webSocketDebuggerUrl")
    if not isinstance(debugger, str):
        raise BrowserCheckError("page debugger URL missing")
    parsed, origin = urlsplit(debugger), urlsplit(endpoint)
    if (
        parsed.scheme != "ws"
        or parsed.netloc.casefold() != origin.netloc.casefold()
        or parsed.username is not None
        or parsed.password is not None
        or not parsed.path.startswith("/devtools/page/")
        or parsed.query
        or parsed.fragment
    ):
        raise BrowserCheckError("page debugger must belong to the selected local Chrome")
    return debugger


def response_result(payload: str | bytes, expected_id: int) -> dict[str, object] | None:
    """Decode a native CDP reply and distinguish events from the requested result.

    Parameters
    ----------
    payload : str or bytes
        Serialized Chrome reply or event.
    expected_id : int
        Sequence identifier sent on the active connection.

    Returns
    -------
    dict or None
        Requested result, or None for an event or another sequence identifier.

    Raises
    ------
    BrowserCheckError
        Matching reply has a protocol/JavaScript error or invalid result shape.
    ValueError
        Serialized document is not valid JSON.
    """
    message: object = json.loads(payload)
    if not isinstance(message, dict):
        raise BrowserCheckError("Chrome message must be an object")
    if message.get("id") != expected_id:
        return None
    if message.get("error"):
        raise BrowserCheckError("Chrome protocol command failed")
    result: object = message.get("result")
    if not isinstance(result, dict):
        raise BrowserCheckError("Chrome result must be an object")
    if result.get("exceptionDetails"):
        raise BrowserCheckError("Chrome JavaScript evaluation failed")
    return {str(key): value for key, value in result.items()}


def evaluation_value(result: dict[str, object]) -> object:
    """Read the remote value from a validated Runtime.evaluate result.

    Parameters
    ----------
    result : dict
        Native Runtime.evaluate result after command/error validation.

    Returns
    -------
    object
        JSON value, or None for a JavaScript value not returned by value.

    Raises
    ------
    BrowserCheckError
        Remote object descriptor is absent or malformed.
    """
    remote: object = result.get("result")
    if not isinstance(remote, dict):
        raise BrowserCheckError("Chrome remote object missing")
    value: object = remote.get("value")
    return value


class BrowserSession:
    """An owned CDP connection to one explicitly selected local Atlas page."""

    def __init__(self, endpoint: str, page_url: str, timeout: float = 15) -> None:
        """Discover the exact page and connect with a positive finite deadline."""
        validate_endpoint(endpoint)
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("browser timeout must be positive and finite")
        self.timeout = timeout
        self.sequence = 0
        with requests.get(
            endpoint.rstrip("/") + "/json/list", timeout=timeout, allow_redirects=False
        ) as response:
            if response.status_code != 200:
                raise BrowserCheckError("Chrome discovery request failed")
            debugger = select_page(response.json(), page_url, endpoint)
        self.connection: websocket.WebSocket = websocket.create_connection(
            debugger, origin=endpoint.rstrip("/"), timeout=timeout
        )

    def __enter__(self) -> BrowserSession:
        """Keep the connected page available within an owned context."""
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the debugger connection after successful or failed checks."""
        self.close()

    def close(self) -> None:
        """Release the debugger connection without closing the user's browser."""
        self.connection.close()

    def command(
        self, method: str, params: dict[str, object] | None = None, *, timeout: float | None = None
    ) -> dict[str, object]:
        """Run a real CDP command with a deadline across intervening events.

        Parameters
        ----------
        method : str
            Chrome protocol method.
        params : dict, optional
            Native method arguments.
        timeout : float, optional
            Per-command deadline, defaulting to the connection timeout.

        Returns
        -------
        dict
            Validated result for this sequence identifier.

        Raises
        ------
        BrowserCheckError
            Deadline expires or Chrome rejects/evaluation fails.
        ValueError
            Timeout or received JSON is invalid.
        """
        duration = self.timeout if timeout is None else timeout
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("command timeout must be positive and finite")
        self.sequence += 1
        deadline = time.monotonic() + duration
        try:
            self.connection.settimeout(duration)
            self.connection.send(
                json.dumps({"id": self.sequence, "method": method, "params": params or {}})
            )
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise BrowserCheckError("Chrome command deadline expired")
                self.connection.settimeout(remaining)
                payload: str | bytes = self.connection.recv()
                result = response_result(payload, self.sequence)
                if result is not None:
                    return result
        finally:
            self.connection.settimeout(self.timeout)

    def evaluate(self, expression: str, *, timeout: float | None = None) -> object:
        """Evaluate JavaScript with native error handling and await promises.

        Parameters
        ----------
        expression : str
            JavaScript evaluated only on the selected page.
        timeout : float, optional
            Deadline covering the requested reply and intervening events.

        Returns
        -------
        object
            Marshalled browser value, never an asserted successful evaluation.
        """
        return evaluation_value(
            self.command(
                "Runtime.evaluate",
                {"expression": expression, "returnByValue": True, "awaitPromise": True},
                timeout=timeout,
            )
        )

    def verify(self, expression: str) -> None:
        """Require a true browser predicate even when Python assertions are disabled.

        Parameters
        ----------
        expression : str
            JavaScript boolean invariant over the full actual page state.

        Raises
        ------
        BrowserCheckError
            Predicate is false or does not return the boolean true.
        """
        if self.evaluate(expression) is not True:
            raise BrowserCheckError("Atlas invariant failed: " + expression)

    def wait_ready(self, *, timeout: float = 15) -> None:
        """Wait for document and real dataset/map initialization before checking.

        Parameters
        ----------
        timeout : float
            Positive finite readiness deadline in seconds.

        Raises
        ------
        BrowserCheckError
            Full application is not initialized by the deadline.
        """
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("readiness timeout must be positive and finite")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if (
                self.evaluate(
                    "document.readyState === 'complete' && typeof reactors !== 'undefined' && !!window.REACTOR_FACILITIES && !!window.FUSION_COMPANIES && !!window.ANULUM_REACTOR_REPOS && typeof atlasMap !== 'undefined'"
                )
                is True
            ):
                return
            time.sleep(min(0.05, max(0, deadline - time.monotonic())))
        raise BrowserCheckError("Atlas readiness deadline expired")


def parse_counts(raw: object) -> dict[str, int]:
    """Require the complete current dataset sizes before any successful report.

    Parameters
    ----------
    raw : object
        Actual four-field observation returned by the native page evaluation.

    Returns
    -------
    dict of str to int
        All four observed dataset counts.

    Raises
    ------
    BrowserCheckError
        Shape, type or any complete-dataset count differs from this snapshot.
    """
    if not isinstance(raw, dict) or set(raw) != set(EXPECTED_COUNTS):
        raise BrowserCheckError("Atlas dataset count shape mismatch")
    counts: dict[str, int] = {}
    for name, expected in EXPECTED_COUNTS.items():
        value: object = raw[name]
        if isinstance(value, bool) or not isinstance(value, int) or value != expected:
            raise BrowserCheckError("Atlas complete dataset count mismatch: " + name)
        counts[name] = value
    return counts


def run_checks(browser: BrowserSession, *, reload: bool = True) -> dict[str, object]:
    """Exercise every original full-data Atlas invariant through real Chrome.

    Parameters
    ----------
    browser : BrowserSession
        Owned connection to the exact intended full application.
    reload : bool
        Reload first by default; False inspects an already established state.

    Returns
    -------
    dict
        Passing report only after all current dataset, map and UI checks pass.
    """
    if reload:
        browser.command("Page.reload")
    browser.wait_ready(timeout=browser.timeout)
    counts = parse_counts(
        browser.evaluate(
            "({types: reactors.length, facilities: window.REACTOR_FACILITIES.length, companies: window.FUSION_COMPANIES.length, repositories: window.ANULUM_REACTOR_REPOS.length})"
        )
    )
    browser.verify('((document.documentElement.lang) === "en")')
    browser.verify("((document.querySelectorAll('.reactor-card').length) === (reactors.length))")
    browser.verify("((document.querySelector('#kindFilter').options.length) > 2)")
    browser.evaluate(
        "document.querySelector('#reactorSearch').value='tokamak'; document.querySelector('#reactorSearch').dispatchEvent(new Event('input'))"
    )
    browser.verify(
        "(0 < (document.querySelectorAll('.reactor-card').length)) && ((document.querySelectorAll('.reactor-card').length) < (reactors.length))"
    )
    browser.evaluate("document.querySelector('.reactor-card').click()")
    browser.verify("(document.querySelector('#reactorDialog').open)")
    browser.verify(
        "(document.querySelector('#reactorDialog').textContent.includes('Taxonomy audit'))"
    )
    browser.verify(
        "(document.querySelector('#reactorDialog').textContent.includes('plausible-provisional'))"
    )
    browser.evaluate(
        "document.querySelector('#reactorDialog').close(); document.querySelector('#reactorSearch').value=''; document.querySelector('#reactorSearch').dispatchEvent(new Event('input'))"
    )
    browser.verify("(document.querySelector('#compareView').textContent.includes('Tokamak'))")
    browser.verify("!((document.querySelector('#compareView').textContent.includes('/5')))")
    browser.verify("(!!document.querySelector('#mapHost canvas.atlas-map-canvas'))")
    browser.verify("(!!window.AtlasMap && !!window.AtlasMap.MapEngine)")
    browser.verify("((atlasMap.points.length) === 13357)")
    browser.verify('((atlasMap.projection.id) === "equal-earth")')
    browser.verify("((atlasMap.projection.equalArea) === true)")
    browser.verify("((atlasMap.tree.size) === 13357)")
    browser.verify(
        "((document.querySelector('#mapHost canvas').getAttribute('tabindex')) === \"0\")"
    )
    browser.verify("((document.querySelectorAll('.atlas-map-sr-list button').length) > 0)")
    browser.verify("((atlasMap.clusters.length) > 0)")
    browser.verify("((atlasMap.clusters.reduce((t,c)=>t+c.count,0)) > 0)")
    browser.verify("((document.querySelectorAll('#facilityList article').length) === 250)")
    browser.verify(
        "(document.querySelector('#facilityCompleteness').textContent.includes('list capped at 250'))"
    )
    browser.verify("(document.querySelector('#facilityExportCsv').textContent.includes('CSV'))")
    browser.verify("(document.querySelector('#facilityExportJson').textContent.includes('JSON'))")
    browser.verify(
        "(document.querySelector('#facilityLayerSummary').textContent.includes('fission: 2192'))"
    )
    browser.verify("((filteredFacilities().length) === (window.REACTOR_FACILITIES.length))")
    browser.verify(
        "((REACTOR_FACILITIES.filter(r => r.dataset_source.includes('expansion_round2')).length) === 1776)"
    )
    browser.verify(
        "((REACTOR_FACILITIES.find(r => r.stable_id === 'wikidata-q5642030').status) === \"shutdown\")"
    )
    browser.verify("((document.querySelector('#facilityKind').options.length) > 2)")
    browser.verify("((document.querySelector('#facilityDataset').options.length) > 5)")
    browser.verify("((document.querySelector('#facilityCountry').options.length) > 2)")
    browser.evaluate(
        "document.querySelector('#facilityDataset').value='05_global_reactor_map/imports/industrial_facilities/expansion_round2/industrial_facilities_round2.tsv'; document.querySelector('#facilityDataset').dispatchEvent(new Event('change'))"
    )
    browser.verify("((filteredFacilities().length) === 1776)")
    browser.evaluate(
        "document.querySelector('#facilityDataset').value='all'; document.querySelector('#facilityDataset').dispatchEvent(new Event('change'))"
    )
    browser.evaluate("atlasMap.emitSelection(atlasMap.points[0])")
    browser.verify("(document.querySelector('#reactorDialog').open)")
    browser.evaluate("document.querySelector('#reactorDialog').close()")
    browser.verify(
        "(atlasMap.clusters.every(c => Object.values(c.domains).reduce((t,n)=>t+n,0) === c.count))"
    )
    browser.evaluate(
        "atlasMap.viewport.zoom = 12; atlasMap.viewport.clampCentre(); atlasMap.draw()"
    )
    browser.verify("((atlasMap.clusters.length) > 0)")
    browser.evaluate("atlasMap.viewport.reset(); atlasMap.draw()")
    browser.evaluate(
        "document.querySelector('#facilityDataset').value='05_global_reactor_map/imports/fusion/ffdb/fusion_facilities.tsv'; document.querySelector('#facilityDataset').dispatchEvent(new Event('change'))"
    )
    browser.verify("(filteredFacilities().length === 174)")
    browser.verify(
        "(document.querySelector('#facilityDataset').selectedOptions[0].textContent.includes('IAEA FFDB'))"
    )
    browser.evaluate(
        "document.querySelector('#facilitySearch').value='UH-MCPG1'; document.querySelector('#facilitySearch').dispatchEvent(new Event('input'))"
    )
    browser.verify("((document.querySelectorAll('#facilityList article').length) === 1)")
    browser.verify("(document.querySelector('#facilityList').textContent.includes('UH-MCPG1'))")
    browser.evaluate(
        "document.querySelector('#facilitySearch').value=''; document.querySelector('#facilitySearch').dispatchEvent(new Event('input'))"
    )
    browser.evaluate(
        "for (const id of ['facilityDomain','facilityKind','facilityDataset','facilityCountry','facilityStatus']) document.querySelector('#' + id).value = 'all'; document.querySelector('#facilitySearch').value='Agrossilvopastoris'; document.querySelector('#facilitySearch').dispatchEvent(new Event('input'))"
    )
    browser.verify("(filteredFacilities().length === 26)")
    browser.verify(
        "(filteredFacilities().every(r => (r.fuel_or_feed || '').includes('Agrossilvopastoris')))"
    )
    browser.evaluate(
        "document.querySelector('#facilitySearch').value=''; document.querySelector('#facilitySearch').dispatchEvent(new Event('input'))"
    )
    browser.verify("(window.REACTOR_FACILITIES.filter(r => r.purpose).length === 1342)")
    browser.verify("(window.REACTOR_FACILITIES.filter(r => r.fuel_or_feed).length === 533)")
    browser.verify(
        "(window.REACTOR_FACILITIES.reduce((n,r) => n + (r.field_observations || []).length, 0) === 1631)"
    )
    browser.evaluate(
        "(() => { const record = window.REACTOR_FACILITIES.find(r => (r.field_observations || []).some(o => o.basis === 'secondary-fuel-classification')); openFacility(record.id); })()"
    )
    browser.verify(
        "(document.querySelector('#dialogBody').textContent.includes('Secondary whole-plant fuel category'))"
    )
    browser.verify(
        "(document.querySelector('#dialogBody').textContent.includes('Captured') || document.querySelector('#dialogBody').textContent.includes('captured'))"
    )
    browser.evaluate("document.querySelector('#reactorDialog').close()")
    browser.verify(
        "((document.querySelectorAll('#companyGrid article').length) === (window.FUSION_COMPANIES.length))"
    )
    browser.verify(
        "(document.querySelector('#companyGrid').textContent.includes('Highest independently supported milestone'))"
    )
    browser.verify(
        "(document.querySelector('#companyGrid').textContent.includes('Unsupported / ambiguous claims'))"
    )
    browser.verify("(FUSION_COMPANIES.some(r => r.name === 'Dongsheng Fusion'))")
    browser.evaluate(
        "document.querySelector('#companySearch').value='Commonwealth'; document.querySelector('#companySearch').dispatchEvent(new Event('input'))"
    )
    browser.verify("((document.querySelectorAll('#companyGrid article').length) === 1)")
    browser.evaluate(
        "document.querySelector('#companySearch').value='NovaFusionX'; document.querySelector('#companySearch').dispatchEvent(new Event('input'))"
    )
    browser.verify("((document.querySelectorAll('#companyGrid article').length) === 1)")
    browser.verify("(document.querySelector('#companyGrid').textContent.includes('Nova 1'))")
    browser.evaluate(
        "document.querySelector('#companySearch').value=''; document.querySelector('#companySearch').dispatchEvent(new Event('input'))"
    )
    browser.verify(
        "((document.querySelectorAll('#repoGrid .repo-card').length) === (window.ANULUM_REACTOR_REPOS.length))"
    )
    browser.evaluate(
        "document.querySelector('#repoSearch').value='theta pinch'; document.querySelector('#repoSearch').dispatchEvent(new Event('input'))"
    )
    browser.verify("((document.querySelectorAll('#repoGrid .repo-card').length) === 1)")
    return {
        "result": "passed",
        "counts": counts,
        "checks": [
            "English",
            "full data loaded",
            "taxonomy search",
            "reactor dialog",
            "comparison",
            "13,357 records projected and indexed",
            "canvas map engine on an equal-area projection",
            "keyboard reachability at full dataset size",
            "cluster record conservation",
            "filtered CSV/JSON export controls",
            "layer count summary",
            "LM26 enrichment search",
            "250-card render cap",
            "98 audited company records",
            "NovaFusionX expansion record",
            "30-repository GitHub catalog",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    """Run the browser checks with explicit page selection and controlled failure.

    Parameters
    ----------
    argv : list of str, optional
        CLI arguments, otherwise process arguments.

    Returns
    -------
    int
        Zero after every full-data check passes; one on browser/invariant failure.
        Argument errors use argparse's exit status two.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:9223")
    parser.add_argument("--page-url", required=True)
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args(argv)
    try:
        with BrowserSession(args.endpoint, args.page_url, args.timeout) as browser:
            report = run_checks(browser)
    except (
        BrowserCheckError,
        requests.RequestException,
        websocket.WebSocketException,
        OSError,
        ValueError,
    ) as exc:
        print(json.dumps({"result": "failed", "reason": str(exc)}))
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
