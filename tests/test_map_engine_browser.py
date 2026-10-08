# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — native map engine pointer gesture regression

"""Exercise cluster dragging and activation through real Chrome pointer input."""

from __future__ import annotations

import pytest

from .browser_checks_runtime import (
    ASSETS,
    NAVIGATION_CHECKER,
    BrowserEndpoints,
    wait_for_page,
)
from .browser_checks_runtime import (
    native_browser as native_browser,
)


@pytest.mark.parametrize("mode", ("http", "file"))
def test_pointer_capture_preserves_drag_outside_canvas(
    native_browser: BrowserEndpoints, mode: str
) -> None:
    """Retain an actual mouse drag outside the canvas and release capture on pointer-up.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Real Chrome and canonical Atlas assets owned by the runtime fixture.
    mode : str
        HTTP presentation or its identical direct-file entry point.

    Raises
    ------
    AssertionError
        Native capture is absent, survives release, or an outside drag fails
        to pan without activating the original source cluster.
    """
    endpoint, initial = native_browser["endpoint"], native_browser["page"]
    page = initial if mode == "http" else (ASSETS / "index.html").as_uri()
    with NAVIGATION_CHECKER.BrowserSession(endpoint, initial, timeout=30) as browser:
        browser.wait_ready(timeout=30)
        if page != initial:
            browser.command("Page.navigate", {"url": page})
            wait_for_page(endpoint, page, timeout=30)
            browser.wait_ready(timeout=30)
        try:
            browser.evaluate(
                (ASSETS / "map/tests/engine-browser-fixture.js").read_text(encoding="utf-8")
            )
            before = browser.evaluate("window.__engineGestureTests.setup()")
            assert isinstance(before, dict)
            x, y = before["x"], before["y"]
            assert isinstance(x, (int, float)) and isinstance(y, (int, float))
            browser.command("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
            browser.command(
                "Input.dispatchMouseEvent",
                {"type": "mousePressed", "button": "left", "clickCount": 1, "x": x, "y": y},
            )
            assert browser.evaluate("window.__engineGestureTests.capture(1)") is True
            browser.command(
                "Input.dispatchMouseEvent",
                {"type": "mouseMoved", "button": "left", "buttons": 1, "x": x + 700, "y": y},
            )
            browser.command(
                "Input.dispatchMouseEvent",
                {
                    "type": "mouseReleased",
                    "button": "left",
                    "clickCount": 1,
                    "x": x + 700,
                    "y": y,
                },
            )
            assert browser.evaluate("window.__engineGestureTests.capture(1)") is False
            assert browser.evaluate("window.__engineGestureTests.afterDrag()") == {
                "zoom": 4,
                "panned": True,
                "selected": 0,
            }
        finally:
            browser.evaluate("window.__engineGestureTests.cleanup()")
            if page != initial:
                browser.command("Page.navigate", {"url": initial})
                wait_for_page(endpoint, initial, timeout=30)
                browser.wait_ready(timeout=30)


@pytest.mark.parametrize("mode", ("http", "file"))
def test_cluster_drag_preserves_zoom_and_next_click_zooms(
    native_browser: BrowserEndpoints, mode: str
) -> None:
    """Pan an original source pair without activation, then zoom by a fresh click.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Owned real Chrome endpoint serving all canonical Atlas assets.
    mode : str
        HTTP presentation or the identical page opened directly from disk.

    Raises
    ------
    AssertionError
        A native pointer drag activates its glyph, fails to pan, or consumes
        the next deliberate click; source rows must remain unselected.
    """
    endpoint, initial = native_browser["endpoint"], native_browser["page"]
    page = initial if mode == "http" else (ASSETS / "index.html").as_uri()
    with NAVIGATION_CHECKER.BrowserSession(endpoint, initial, timeout=30) as browser:
        browser.wait_ready(timeout=30)
        if page != initial:
            browser.command("Page.navigate", {"url": page})
            wait_for_page(endpoint, page, timeout=30)
            browser.wait_ready(timeout=30)
        try:
            browser.evaluate(
                (ASSETS / "map/tests/engine-browser-fixture.js").read_text(encoding="utf-8")
            )
            before = browser.evaluate("window.__engineGestureTests.setup()")
            assert isinstance(before, dict)
            x, y = before["x"], before["y"]
            assert isinstance(x, (int, float)) and isinstance(y, (int, float))
            assert before["zoom"] == 4
            browser.command("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
            browser.command(
                "Input.dispatchMouseEvent",
                {"type": "mousePressed", "button": "left", "clickCount": 1, "x": x, "y": y},
            )
            browser.command(
                "Input.dispatchMouseEvent",
                {"type": "mouseMoved", "button": "left", "buttons": 1, "x": x + 40, "y": y + 15},
            )
            browser.command(
                "Input.dispatchMouseEvent",
                {
                    "type": "mouseReleased",
                    "button": "left",
                    "clickCount": 1,
                    "x": x + 40,
                    "y": y + 15,
                },
            )
            assert browser.evaluate("window.__engineGestureTests.afterDrag()") == {
                "zoom": 4,
                "panned": True,
                "selected": 0,
            }
            position = browser.evaluate("window.__engineGestureTests.glyph()")
            assert isinstance(position, dict)
            x, y = position["x"], position["y"]
            assert isinstance(x, (int, float)) and isinstance(y, (int, float))
            browser.command("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
            browser.command(
                "Input.dispatchMouseEvent",
                {"type": "mousePressed", "button": "left", "clickCount": 1, "x": x, "y": y},
            )
            browser.command(
                "Input.dispatchMouseEvent",
                {"type": "mouseReleased", "button": "left", "clickCount": 1, "x": x, "y": y},
            )
            assert browser.evaluate("window.__engineGestureTests.afterClick()") == {
                "zoom": 10,
                "selected": 0,
            }
        finally:
            browser.evaluate("window.__engineGestureTests.cleanup()")
            if page != initial:
                browser.command("Page.navigate", {"url": initial})
                wait_for_page(endpoint, initial, timeout=30)
                browser.wait_ready(timeout=30)


@pytest.mark.parametrize("mode", ("http", "file"))
@pytest.mark.parametrize("excursion", (3, 40))
def test_click_tolerance_and_returning_drag_remain_distinct(
    native_browser: BrowserEndpoints, mode: str, excursion: int
) -> None:
    """Accept slight click movement but retain drag identity after returning to start.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Owned native Chrome with complete canonical Atlas assets.
    mode : str
        HTTP presentation or the identical direct-file page.
    excursion : int
        Three CSS pixels of click jitter, or a forty-pixel drag that returns
        to its initial position before release.

    Raises
    ------
    AssertionError
        Jitter prevents a deliberate click or an out-and-back drag activates
        the original co-located source pair.
    """
    endpoint, initial = native_browser["endpoint"], native_browser["page"]
    page = initial if mode == "http" else (ASSETS / "index.html").as_uri()
    with NAVIGATION_CHECKER.BrowserSession(endpoint, initial, timeout=30) as browser:
        browser.wait_ready(timeout=30)
        if page != initial:
            browser.command("Page.navigate", {"url": page})
            wait_for_page(endpoint, page, timeout=30)
            browser.wait_ready(timeout=30)
        try:
            browser.evaluate(
                (ASSETS / "map/tests/engine-browser-fixture.js").read_text(encoding="utf-8")
            )
            before = browser.evaluate("window.__engineGestureTests.setup()")
            assert isinstance(before, dict)
            x, y = before["x"], before["y"]
            assert isinstance(x, (int, float)) and isinstance(y, (int, float))
            browser.command("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
            browser.command(
                "Input.dispatchMouseEvent",
                {"type": "mousePressed", "button": "left", "clickCount": 1, "x": x, "y": y},
            )
            browser.command(
                "Input.dispatchMouseEvent",
                {"type": "mouseMoved", "button": "left", "buttons": 1, "x": x + excursion, "y": y},
            )
            end_x = x + excursion
            if excursion > 4:
                end_x = x
                browser.command(
                    "Input.dispatchMouseEvent",
                    {"type": "mouseMoved", "button": "left", "buttons": 1, "x": x, "y": y},
                )
            browser.command(
                "Input.dispatchMouseEvent",
                {"type": "mouseReleased", "button": "left", "clickCount": 1, "x": end_x, "y": y},
            )
            assert browser.evaluate("window.__engineGestureTests.afterClick()") == {
                "zoom": 10 if excursion <= 4 else 4,
                "selected": 0,
            }
        finally:
            browser.evaluate("window.__engineGestureTests.cleanup()")
            if page != initial:
                browser.command("Page.navigate", {"url": initial})
                wait_for_page(endpoint, initial, timeout=30)
                browser.wait_ready(timeout=30)
