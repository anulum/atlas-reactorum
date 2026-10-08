# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — complete shared map source and real runtime qualification.
"""Require source-exact shared map execution across genuine Node/Cairo and Chrome runtimes."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from tools.research_objects import object_fields, object_rows

from ._native_browser_ranges import browser_ranges, verify_ranges
from ._native_gate_ranges import run_gate
from .browser_checks_runtime import BrowserEndpoints
from .browser_checks_runtime import native_browser as native_browser
from .test_evidence_profiles_browser import Browser

ROOT = Path(__file__).resolve().parents[1]
MODULES = tuple(
    ROOT / "04_interactive_presentation/map" / name
    for name in (
        "projection.js",
        "coastline.js",
        "quadtree.js",
        "cluster.js",
        "viewport.js",
        "renderer.js",
        "engine.js",
        "interactions.js",
        "accessibility.js",
    )
)


@pytest.fixture(scope="module")
def evidence_directory(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Retain exact native Node and Chrome reports without inventing Node AST coverage.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        Owner-selected Samsung workspace for source-exact native execution reports.

    Yields
    ------
    pathlib.Path
        Exclusive report directory; teardown requires all source functions and native regions across both real runtimes.
    """
    directory = tmp_path_factory.mktemp("map-real-native-ranges")
    node = shutil.which("node")
    assert node is not None
    source_hashes = {
        str(source): hashlib.sha256(source.read_bytes()).hexdigest() for source in MODULES
    }
    raw = directory / "node-v8"
    raw.mkdir()
    result = subprocess.run(
        [
            node,
            "--test",
            "04_interactive_presentation/map/tests/engine-dom.test.js",
            "04_interactive_presentation/map/tests/engine-native-contract.test.js",
            "04_interactive_presentation/map/tests/accessibility.test.js",
            "04_interactive_presentation/map/tests/interactions.test.js",
            "04_interactive_presentation/map/tests/native-geometry.test.js",
            "04_interactive_presentation/map/tests/native-renderer.test.js",
        ],
        cwd=ROOT,
        env={**os.environ, "NODE_V8_COVERAGE": str(raw)},
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert all(
        hashlib.sha256(Path(source).read_bytes()).hexdigest() == digest
        for source, digest in source_hashes.items()
    )
    reports = []
    for source in MODULES:
        scripts: list[dict[str, object]] = []
        for receipt in raw.glob("*.json"):
            value: object = json.loads(receipt.read_text())
            assert isinstance(value, dict)
            native = value["result"]
            assert isinstance(native, list)
            for script in native:
                assert isinstance(script, dict)
                if script["url"] == source.as_uri():
                    scripts.append(script)
        assert scripts, source.name
        reports.append(
            {
                "source": str(source),
                "source_sha256": source_hashes[str(source)],
                "native_source_equal": True,
                "runtime": "node/cairo",
                "scripts": scripts,
            }
        )
    with (directory / "case-actual-node-cairo.json").open("x") as handle:
        json.dump(reports, handle, indent=2)
    yield directory
    verify_ranges(directory, MODULES)


@pytest.fixture
def browser(
    native_browser: BrowserEndpoints, request: pytest.FixtureRequest, evidence_directory: Path
) -> Iterator[Browser]:
    """Yield the actual Chrome application with complete current shared-map source capture.

    Parameters
    ----------
    native_browser : BrowserEndpoints
        Owned real Chrome and complete maintained page URL.
    request : pytest.FixtureRequest
        Actual registered case name used for its exclusive native receipt.
    evidence_directory : pathlib.Path
        Source-exact Node and Chrome receipt directory owned by this module.

    Yields
    ------
    Browser
        Actual maintained session recording the complete shared map implementation.
    """
    with browser_ranges(native_browser, evidence_directory, MODULES, request.node.name) as actual:
        yield actual


def test_actual_complete_map_projection_focus_and_source_identity(browser: Browser) -> None:
    """Reproject all real records, retain their source identity and activate native accessible controls."""
    assert browser.evaluate("atlasMap.points.length") == 13357
    browser.evaluate("atlasMap.setProjection('plate-carree');atlasMap.draw()")
    assert browser.evaluate("atlasMap.projection.id") == "plate-carree"
    browser.evaluate(
        "atlasMap.setProjection('equal-earth');atlasMap.draw();document.querySelector('#mapHost .atlas-map-sr-list button').click()"
    )
    assert browser.evaluate("reactorDialog.open") is True
    assert browser.evaluate("atlasMap.focus.row===REACTOR_FACILITIES[0]") is True
    browser.evaluate(
        'reactorDialog.close();atlasMap.setProjection("plate-carree");atlasMap.setData([]);atlasMap.draw()'
    )
    assert browser.evaluate("atlasMap.focus===null&&atlasMap.points.length===0") is True
    browser.evaluate(
        'atlasMap.setData(REACTOR_FACILITIES);atlasMap.setProjection("equal-earth");atlasMap.draw()'
    )
    assert (
        browser.evaluate("atlasMap.points.every(point=>REACTOR_FACILITIES.includes(point.row))")
        is True
    )


def test_actual_native_pointer_capture_and_keyboard_dispatch(browser: Browser) -> None:
    """Use native input dispatch to retain pointer capture and complete map key behavior."""
    rect = browser.evaluate(
        "(()=>{const r=atlasMap.canvas.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2};})()"
    )
    assert isinstance(rect, dict)
    browser.command(
        "Input.dispatchMouseEvent",
        {"type": "mousePressed", "button": "left", "clickCount": 1, **rect},
    )
    assert browser.evaluate("atlasMap.canvas.hasPointerCapture(1)") is True
    browser.command(
        "Input.dispatchMouseEvent",
        {
            "type": "mouseMoved",
            "button": "left",
            "buttons": 1,
            "x": float(rect["x"]) + 40,
            "y": rect["y"],
        },
    )
    browser.command(
        "Input.dispatchMouseEvent",
        {
            "type": "mouseReleased",
            "button": "left",
            "clickCount": 1,
            "x": float(rect["x"]) + 40,
            "y": rect["y"],
        },
    )
    assert browser.evaluate("atlasMap.canvas.hasPointerCapture(1)") is False
    browser.evaluate("atlasMap.canvas.focus()")
    for key in (
        "ArrowLeft",
        "ArrowRight",
        "ArrowUp",
        "ArrowDown",
        "+",
        "=",
        "-",
        "_",
        "0",
        "Enter",
        " ",
        "Tab",
    ):
        browser.evaluate(
            'atlasMap.canvas.dispatchEvent(new KeyboardEvent("keydown",{key:'
            + json.dumps(key)
            + ",cancelable:true,shiftKey:true}))"
        )
    browser.evaluate("atlasMap.draw()")


def test_real_legacy_map_cases_refuse_malformed_original_dataset(tmp_path: Path) -> None:
    """Refuse an invalid original country cell through all three real native map test entry points.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Owning directory for complete source copies and a deliberately damaged
        full original dataset. Canonical source and data remain unchanged.
    """
    node = shutil.which("node")
    assert node is not None
    root = tmp_path / "candidate"
    modules = (
        ROOT / "04_interactive_presentation/application-data.js",
        *MODULES,
        *(
            ROOT / "04_interactive_presentation/map/tests" / (name + ".test.js")
            for name in ("engine", "cluster", "quadtree")
        ),
    )
    for source in modules:
        target = root / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    original = ROOT / "04_interactive_presentation/data/global_reactors.sample.json"
    before = original.read_bytes()
    document = object_fields(json.loads(before))
    rows = object_rows(document["records"])
    assert isinstance(rows[0]["country"], str)
    rows[0]["country"] = 17
    document["records"] = rows
    target = root / original.relative_to(ROOT)
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    damaged = target.read_bytes()
    command = [
        node,
        "--test",
        *(
            "04_interactive_presentation/map/tests/" + name + ".test.js"
            for name in ("engine", "cluster", "quadtree")
        ),
    ]
    result = run_gate(
        root,
        command,
        [str(source.relative_to(ROOT)) for source in modules],
        dict(os.environ),
        30,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "Atlas dataset text cell is unavailable: country" in result.stdout + result.stderr
    assert target.read_bytes() == damaged
    assert original.read_bytes() == before


def test_actual_map_refuses_inherited_projection_names_without_state_change(
    browser: Browser,
) -> None:
    """Refuse unregistered prototype names through the real map while preserving its entire view.

    Parameters
    ----------
    browser : Browser
        Actual maintained Chrome page with source-bound shared map coverage.
    """
    rows = object_rows(
        browser.evaluate(
            """(() => {
                const state = () => [atlasMap.projection, atlasMap.world,
                    atlasMap.viewport, atlasMap.viewport.world, atlasMap.viewport.zoom,
                    atlasMap.viewport.centreX, atlasMap.viewport.centreY,
                    atlasMap.points, atlasMap.tree, atlasMap.focus];
                const before = state();
                return Object.getOwnPropertyNames(Object.prototype).map(id => {
                    let message = null;
                    try { atlasMap.setProjection(id); }
                    catch (error) { message = error.message; }
                    return {id, message,
                        unchanged: state().every((value, index) => value === before[index])};
                });
            })()"""
        )
    )
    assert rows
    for row in rows:
        identifier = row["id"]
        assert isinstance(identifier, str)
        assert row["message"] == f"unknown projection: {identifier}"
        assert row["unchanged"] is True
