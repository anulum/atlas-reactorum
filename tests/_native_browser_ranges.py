# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — source-exact native browser coverage for owning modules.
"""Collect and require complete source-exact execution in the actual Chrome application."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from itertools import pairwise
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

import requests

from .browser_checks_runtime import BrowserEndpoints
from .conftest import load_module
from .test_evidence_profiles_browser import Browser
from .test_taxonomy_comparison_browser import NativeScript, native_count, reload_page


@contextmanager
def browser_ranges(
    native: BrowserEndpoints, directory: Path, modules: Sequence[Path], case: str
) -> Iterator[Browser]:
    """Record actual native source functions and blocks around one complete page use.

    Parameters
    ----------
    native : BrowserEndpoints
        Owned real Chrome endpoint and exact maintained page URL.
    directory : pathlib.Path
        Test-owned receipt directory; each case is created exclusively.
    modules : sequence of pathlib.Path
        Complete actual module sources whose native bytes must match the checkout.
    case : str
        Unique registered test identity, retained in the receipt filename.

    Yields
    ------
    Browser
        Real maintained session after a fresh source-exact application reload.
    """
    module = load_module(
        "04_interactive_presentation/browser-check.py", "atlas_owned_native_ranges"
    )
    with requests.get(native["endpoint"] + "/json/list", timeout=5) as response:
        response.raise_for_status()
        targets: object = response.json()
    assert isinstance(targets, list)
    baseline = urlsplit(native["page"])
    pages = [
        target["url"]
        for target in targets
        if isinstance(target, dict)
        and target.get("type") == "page"
        and isinstance(target.get("url"), str)
        and urlsplit(target["url"])[:3] == baseline[:3]
    ]
    assert len(pages) == 1
    with module.BrowserSession(native["endpoint"], pages[0]) as connected:
        browser = cast(Browser, connected)
        browser.wait_ready()
        browser.command("Debugger.enable")
        browser.command("Profiler.enable")
        browser.command("Profiler.startPreciseCoverage", {"callCount": True, "detailed": True})
        reload_page(browser)
        try:
            yield browser
        finally:
            result = browser.command("Profiler.takePreciseCoverage")["result"]
            assert isinstance(result, list)
            captured = []
            for source in modules:
                scripts = [
                    script
                    for script in result
                    if isinstance(script, dict)
                    and str(script.get("url", "")).endswith("/" + source.name)
                ]
                assert scripts, source.name
                for script in scripts:
                    actual = browser.command(
                        "Debugger.getScriptSource", {"scriptId": script["scriptId"]}
                    )
                    assert actual["scriptSource"] == source.read_text()
                captured.append(
                    {
                        "source": str(source),
                        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        "native_source_equal": True,
                        "scripts": scripts,
                    }
                )
            with (directory / ("case-" + case + ".json")).open("x") as handle:
                json.dump(captured, handle, indent=2)
            browser.command("Profiler.stopPreciseCoverage")
            browser.command("Profiler.disable")
            browser.command("Debugger.disable")
            if browser.evaluate("location.href") != native["page"]:
                browser.command("Page.navigate", {"url": native["page"]})
                browser.wait_ready()


def verify_ranges(directory: Path, modules: Sequence[Path]) -> None:
    """Require every actual compiler region and function in each complete source.

    Parameters
    ----------
    directory : pathlib.Path
        Actual case receipts emitted by the source-exact native collector.
    modules : sequence of pathlib.Path
        Complete current module sources; another file or stale hash never satisfies coverage.

    Raises
    ------
    AssertionError
        A source, region or function is absent, stale or unexecuted in actual Chrome.
    """
    gaps: dict[str, list[tuple[int, int]]] = {}
    for source in modules:
        scripts: list[NativeScript] = []
        for receipt in directory.glob("case-*.json"):
            report: object = json.loads(receipt.read_text())
            assert isinstance(report, list)
            for item in report:
                assert isinstance(item, dict)
                if item["source"] != str(source):
                    continue
                assert item["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
                assert item["native_source_equal"] is True
                native = item["scripts"]
                assert isinstance(native, list)
                for script in native:
                    assert isinstance(script, dict) and str(script["url"]).endswith(
                        "/" + source.name
                    )
                    scripts.append(cast(NativeScript, script))
        assert scripts, source.name
        boundaries = sorted(
            {
                offset
                for script in scripts
                for function in script["functions"]
                for region in function["ranges"]
                for offset in (region["startOffset"], region["endOffset"])
            }
        )
        assert (
            boundaries[0] == 0
            and boundaries[-1] == len(source.read_text().encode("utf-16-le")) // 2
        )
        gaps[source.name] = [
            (start, end)
            for start, end in pairwise(boundaries)
            if max(native_count(script, (start + end) / 2) for script in scripts) == 0
        ]
        functions: dict[tuple[str, int, int], int] = {}
        for script in scripts:
            for function in script["functions"]:
                outer = function["ranges"][0]
                key = (function["functionName"], outer["startOffset"], outer["endOffset"])
                functions[key] = functions.get(key, 0) + outer["count"]
        assert all(count > 0 for count in functions.values()), (
            source.name,
            [key for key, count in functions.items() if count == 0],
        )
    with (directory / "native-region-gaps.json").open("x") as handle:
        json.dump(gaps, handle, indent=2)
    assert not any(gaps.values()), gaps
